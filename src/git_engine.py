from __future__ import annotations

from collections import Counter
from pathlib import Path

from .classifier import classify_commit
from .impact import assess_impact, detect_impacts
from .models import AnalysisResult, Commit
from .parser import parse_git_log_output
from .summary import generate_summary
from .utils import normalize_repo_path, run_git_command


def get_commit_range(repo_path: str | Path, range_spec: str) -> list[Commit]:
    """Retrieve commits for a repo range using git log."""
    repo = normalize_repo_path(str(repo_path))
    git_format = "--pretty=format:commit %H%nAuthor: %an%nDate:   %ad%n%n    %s%n%n"

    try:
        output = run_git_command(repo, ["log", git_format, "--date=default", range_spec])
    except RuntimeError:
        try:
            output = run_git_command(repo, ["log", git_format, "--date=default", "-n", "20"])
        except RuntimeError:
            return []

    commits = parse_git_log_output(output)
    return commits


def build_analysis(repo_path: str | Path, range_spec: str) -> AnalysisResult:
    """Analyze a commit range and produce project insight data."""
    commits = get_commit_range(repo_path, range_spec)
    if not commits:
        return AnalysisResult(
            commit_count=0,
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

    for commit in commits:
        diff_output = get_commit_diff(repo_path, commit.hash)
        category = classify_commit(commit.message, diff_output)
        categories[category] += 1
        commit.diff = diff_output
        commit_files = extract_files_from_diff(diff_output)
        for file_name in commit_files:
            hotspots[file_name] += 1
        impacts.extend(detect_impacts(commit.message, diff_output))

    analysis = AnalysisResult(
        commit_count=len(commits),
        contributors=contributors,
        categories=dict(categories),
        hotspots=dict(hotspots),
        impact_score=assess_impact(impacts),
        summary="",
        impacts=sorted(set(impacts)),
        commits=commits,
    )
    analysis.summary = generate_summary(analysis)
    return analysis


def get_commit_diff(repo_path: str | Path, revision: str) -> str:
    """Return the patch for a single commit."""
    repo = normalize_repo_path(str(repo_path))
    try:
        return run_git_command(repo, ["show", "--stat", "--patch", revision])
    except RuntimeError:
        return ""


def extract_files_from_diff(diff_text: str) -> list[str]:
    """Parse file paths from the diff text."""
    files: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                if path.startswith("a/"):
                    path = path[2:]
                if path and path not in seen:
                    files.append(path)
                    seen.add(path)
    return files


def get_repo_status(repo_path: str | Path) -> str:
    """Return git status output for a repository."""
    repo = normalize_repo_path(str(repo_path))
    return run_git_command(repo, ["status", "--short", "--branch"])
