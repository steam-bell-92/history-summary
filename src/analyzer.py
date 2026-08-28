from __future__ import annotations

from collections import Counter

from .classifier import classify_commit
from .impact import assess_impact, detect_impacts
from .models import AnalysisResult, Commit
from .summary import generate_summary


def analyze_commits(commits: list[Commit], diff_lookup: dict[str, str] | None = None) -> AnalysisResult:
    """Analyze commit objects to produce summary metrics, categories, and hotspots."""
    diff_lookup = diff_lookup or {}
    contributors = sorted({commit.author for commit in commits if commit.author})
    categories: Counter[str] = Counter()
    hotspots: Counter[str] = Counter()
    impacts: list[str] = []

    for commit in commits:
        diff_text = diff_lookup.get(commit.hash, commit.diff)
        category = classify_commit(commit.message, diff_text)
        categories[category] += 1

        for file_name in extract_hotspots(diff_text):
            hotspots[file_name] += 1
        impacts.extend(detect_impacts(commit.message, diff_text))

    result = AnalysisResult(
        commit_count=len(commits),
        contributors=contributors,
        categories=dict(categories),
        hotspots=dict(hotspots),
        impact_score=assess_impact(impacts),
        summary="",
        impacts=sorted(set(impacts)),
        commits=commits,
    )
    result.summary = generate_summary(result)
    return result


def extract_hotspots(diff_text: str) -> list[str]:
    """Extract file paths from a diff block."""
    paths: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3].removeprefix("a/")
                if path and path not in seen:
                    paths.append(path)
                    seen.add(path)
    return paths
