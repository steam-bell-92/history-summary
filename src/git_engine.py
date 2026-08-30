from __future__ import annotations

from collections import Counter
from pathlib import Path

from .classifier import classify_commit
from .impact import assess_impact, detect_change_domains, explain_impact_score
from .models import AnalysisResult, Commit
from .parser import merge_file_changes, parse_git_log_output, parse_name_status_output, parse_numstat_output
from .summary import generate_summary
from .utils import normalize_repo_path, run_git_command


def get_commit_range(repo_path: str | Path, range_spec: str) -> list[Commit]:
    """Retrieve commits for a repo range using git log."""
    repo = normalize_repo_path(str(repo_path))
    git_format = "--pretty=format:%H%x1f%an%x1f%ad%x1f%s%x1e"

    try:
        commit_count = run_git_command(repo, ["rev-list", "--count", "--all"]).strip()
    except RuntimeError:
        raise
    if commit_count == "0":
        return []

    output = run_git_command(repo, ["log", git_format, "--date=iso-strict", "--reverse", range_spec])

    commits = parse_git_log_output(output)
    return commits


def build_analysis(repo_path: str | Path, range_spec: str) -> AnalysisResult:
    """Analyze a commit range and produce project insight data."""
    commits = get_commit_range(repo_path, range_spec)
    repo = normalize_repo_path(str(repo_path))
    if not commits:
        return AnalysisResult(
            commit_count=0,
            revision_range=range_spec,
            repository=str(repo),
            contributors=[],
            categories={},
            hotspots={},
            impact_score=0,
            summary="No commit history is available for the selected range.",
            impacts=[],
            commits=[],
        )

    contributors = sorted({commit.author for commit in commits if commit.author})
    categories: Counter[str] = Counter()
    hotspots: Counter[str] = Counter()
    impacts: list[str] = []
    impact_reasons: list[str] = []

    for commit in commits:
        changes = get_commit_changes(repo_path, commit.hash)
        commit.changes = changes
        commit.files_changed = len(changes)
        commit.insertions = sum(change.additions for change in changes if change.additions > 0)
        commit.deletions = sum(change.deletions for change in changes if change.deletions > 0)
        category = classify_commit(commit.message, changes)
        categories[category] += 1
        for file_name in extract_files_from_changes(changes):
            hotspots[file_name] += 1
        domains, reasons = detect_change_domains(commit.message, changes)
        impacts.extend(domains)
        impact_reasons.extend(reasons)

    impact_score = assess_impact(impacts, commits)

    analysis = AnalysisResult(
        commit_count=len(commits),
        revision_range=range_spec,
        repository=str(repo),
        contributors=contributors,
        categories=dict(categories),
        hotspots=dict(hotspots),
        impact_score=impact_score,
        impact_reasons=explain_impact_score(impact_score, impacts, impact_reasons, commits),
        summary="",
        impacts=sorted(set(impacts)),
        commits=commits,
    )
    analysis.summary = generate_summary(analysis)
    return analysis


def get_commit_changes(repo_path: str | Path, revision: str) -> list:
    """Return structured file changes for a single commit."""
    repo = normalize_repo_path(str(repo_path))
    try:
        name_status = run_git_command(
            repo,
            ["diff-tree", "--root", "--no-commit-id", "-r", "-m", "-M", "-C", "-z", "--name-status", revision],
        )
        numstat = run_git_command(
            repo,
            ["diff-tree", "--root", "--no-commit-id", "-r", "-m", "-M", "-C", "-z", "--numstat", revision],
        )
        changes = merge_file_changes(parse_name_status_output(name_status), parse_numstat_output(numstat))
        for change in changes:
            change.path = change.path.removeprefix("b/")
            if change.old_path:
                change.old_path = change.old_path.removeprefix("a/")
        return changes
    except RuntimeError:
        return []


def extract_files_from_changes(changes: list) -> list[str]:
    """Parse file paths from structured change records."""
    files: list[str] = []
    seen: set[str] = set()
    for change in changes:
        for path in [getattr(change, "old_path", None), getattr(change, "path", None)]:
            if path and path not in seen:
                files.append(path.removeprefix("a/").removeprefix("b/"))
                seen.add(path)
    return files


def get_repo_status(repo_path: str | Path) -> str:
    """Return git status output for a repository."""
    repo = normalize_repo_path(str(repo_path))
    return run_git_command(repo, ["status", "--short", "--branch"])
