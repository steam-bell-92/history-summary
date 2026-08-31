from __future__ import annotations

from collections import Counter

from .classifier import classify_commit
from .excludes import matched_exclude_pattern, resolve_patterns
from .impact import assess_risk, detect_domain_findings, merge_domain_findings
from .models import AnalysisResult, Commit, DomainFinding, ExcludedFile
from .summary import generate_summary


def analyze_commits(
    commits: list[Commit],
    diff_lookup: dict[str, str] | None = None,
    exclude_patterns: list[str] | None = None,
    include_generated: bool = False,
) -> AnalysisResult:
    """Analyze pre-fetched commit objects (with optional raw diff text) into an AnalysisResult.

    This is a lower-level entry point than ``git_engine.build_analysis`` for
    callers that already have ``Commit`` objects and/or raw diff text on hand
    (for example, when replaying previously captured Git output) rather than
    a live repository to query.
    """
    diff_lookup = diff_lookup or {}
    patterns = resolve_patterns(exclude_patterns, include_generated)

    contributors = sorted({commit.author for commit in commits if commit.author})
    categories: Counter[str] = Counter()
    hotspots: Counter[str] = Counter()
    changed_areas: Counter[str] = Counter()
    per_commit_domain_findings: list[DomainFinding] = []
    excluded: dict[str, str] = {}

    for commit in commits:
        diff_text = diff_lookup.get(commit.hash, commit.diff)

        for change in commit.changes:
            pattern = matched_exclude_pattern(change.path, patterns)
            if pattern is None and change.old_path:
                pattern = matched_exclude_pattern(change.old_path, patterns)
            change.is_generated = pattern is not None
            change.exclude_pattern = pattern
            if change.is_generated and pattern:
                excluded.setdefault(change.path, pattern)

        category = classify_commit(commit.message, commit.changes)
        categories[category] += 1

        file_names = extract_hotspots(diff_text, patterns) or [
            change.path for change in commit.changes if not change.is_generated
        ]
        for file_name in file_names:
            hotspots[file_name] += 1
            changed_areas[_area_for_path(file_name)] += 1

        per_commit_domain_findings.extend(detect_domain_findings(commit.message, commit.changes))

    domain_findings = merge_domain_findings(per_commit_domain_findings)
    risk = assess_risk(domain_findings, commits)

    result = AnalysisResult(
        commit_count=len(commits),
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
    result.summary = generate_summary(result)
    return result


def extract_hotspots(diff_text: str, patterns: tuple[str, ...] = ()) -> list[str]:
    """Extract file paths from a diff block, skipping generated/build artifacts."""
    paths: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3].removeprefix("b/")
                if path and path not in seen and matched_exclude_pattern(path, patterns) is None:
                    paths.append(path)
                    seen.add(path)
    return paths


def _area_for_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if len(parts) <= 1:
        return "(root)"
    return parts[0]
