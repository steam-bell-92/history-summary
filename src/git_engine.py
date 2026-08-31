from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Sequence

from .classifier import classify_commit
from .excludes import matched_exclude_pattern, resolve_patterns
from .impact import assess_risk, detect_domain_findings, merge_domain_findings
from .models import AnalysisResult, Commit, DomainFinding, ExcludedFile, FileChange
from .parser import merge_file_changes, parse_git_log_output, parse_name_status_output, parse_numstat_output
from .summary import generate_summary
from .utils import normalize_repo_path, run_git_command


def get_commit_range(repo_path: str | Path, range_spec: str) -> list[Commit]:
    """Retrieve commits for a repo range using git log."""
    repo = normalize_repo_path(str(repo_path))
    git_format = "--pretty=format:%H%x1f%an%x1f%ad%x1f%s%x1e"

    commit_count = run_git_command(repo, ["rev-list", "--count", "--all"]).strip()
    if commit_count == "0":
        return []

    output = run_git_command(repo, ["log", git_format, "--date=iso-strict", "--reverse", range_spec])

    commits = parse_git_log_output(output)
    return commits


def build_analysis(
    repo_path: str | Path,
    range_spec: str,
    exclude_patterns: Sequence[str] | None = None,
    include_generated: bool = False,
) -> AnalysisResult:
    """Analyze a commit range and produce project insight data.

    ``exclude_patterns`` adds extra glob patterns (on top of the built-in
    generated/build artifact patterns) to treat as non-substantive. Pass
    ``include_generated=True`` to disable exclusion entirely -- every matched
    file is always reported transparently via ``AnalysisResult.excluded_files``
    regardless of whether it was excluded from the rest of the analysis.
    """
    commits = get_commit_range(repo_path, range_spec)
    repo = normalize_repo_path(str(repo_path))
    if not commits:
        return AnalysisResult(
            commit_count=0,
            revision_range=range_spec,
            repository=str(repo),
            summary="No commit history is available for the selected range.",
        )

    patterns = resolve_patterns(list(exclude_patterns or []), include_generated)

    contributors = sorted({commit.author for commit in commits if commit.author})
    categories: Counter[str] = Counter()
    hotspots: Counter[str] = Counter()
    changed_areas: Counter[str] = Counter()
    per_commit_domain_findings: list[DomainFinding] = []
    excluded: dict[str, str] = {}

    for commit in commits:
        changes = get_commit_changes(repo_path, commit.hash)
        annotate_generated_changes(changes, patterns)
        commit.changes = changes
        commit.files_changed = len(changes)
        commit.insertions = sum(change.additions for change in changes if change.additions > 0)
        commit.deletions = sum(change.deletions for change in changes if change.deletions > 0)

        for change in changes:
            if change.is_generated and change.exclude_pattern:
                excluded.setdefault(change.path, change.exclude_pattern)

        category = classify_commit(commit.message, changes)
        categories[category] += 1

        for file_name in extract_files_from_changes(changes):
            hotspots[file_name] += 1
            changed_areas[area_for_path(file_name)] += 1

        per_commit_domain_findings.extend(detect_domain_findings(commit.message, changes))

    domain_findings = merge_domain_findings(per_commit_domain_findings)
    risk = assess_risk(domain_findings, commits)

    analysis = AnalysisResult(
        commit_count=len(commits),
        revision_range=range_spec,
        repository=str(repo),
        contributors=contributors,
        categories=dict(categories),
        hotspots=dict(hotspots),
        changed_areas=dict(changed_areas),
        domain_findings=domain_findings,
        risk=risk,
        summary="",
        commits=commits,
        excluded_files=[ExcludedFile(path=path, pattern=pattern) for path, pattern in sorted(excluded.items())],
    )
    analysis.summary = generate_summary(analysis)
    return analysis


def get_commit_changes(repo_path: str | Path, revision: str) -> list[FileChange]:
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


def annotate_generated_changes(changes: list[FileChange], patterns: tuple[str, ...]) -> None:
    """Mark each change as generated/build-artifact-or-not using the given patterns.

    Both the new and old path are checked (a rename into or out of a generated
    location still counts), and the matched pattern is recorded so it can be
    surfaced transparently in reports.
    """
    for change in changes:
        pattern = matched_exclude_pattern(change.path, patterns)
        if pattern is None and change.old_path:
            pattern = matched_exclude_pattern(change.old_path, patterns)
        change.is_generated = pattern is not None
        change.exclude_pattern = pattern


def extract_files_from_changes(changes: list[FileChange]) -> list[str]:
    """Parse file paths from structured change records, skipping generated artifacts."""
    files: list[str] = []
    seen: set[str] = set()
    for change in changes:
        if change.is_generated:
            continue
        for path in [change.old_path, change.path]:
            if path and path not in seen:
                files.append(path.removeprefix("a/").removeprefix("b/"))
                seen.add(path)
    return files


def area_for_path(path: str) -> str:
    """Return the top-level directory (or '(root)') that a path belongs to.

    This is a purely structural grouping used for the factual "changed
    areas" view -- it makes no claim about what engineering domain the area
    corresponds to (see ``impact.detect_domain_findings`` for that).
    """
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if len(parts) <= 1:
        return "(root)"
    return parts[0]


def get_repo_status(repo_path: str | Path) -> str:
    """Return git status output for a repository."""
    repo = normalize_repo_path(str(repo_path))
    return run_git_command(repo, ["status", "--short", "--branch"])
