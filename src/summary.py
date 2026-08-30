from __future__ import annotations

from collections import Counter

from .models import AnalysisResult


def generate_summary(result: AnalysisResult) -> str:
    """Build a concise human-readable summary from analysis results."""
    if result.commit_count == 0:
        return "No commit history is available for the selected range."

    dominant_category = max(result.categories.items(), key=lambda item: item[1])[0] if result.categories else "mixed work"
    hotspot = max(result.hotspots.items(), key=lambda item: item[1])[0] if result.hotspots else "project files"

    file_counts = Counter()
    for commit in result.commits:
        for change in commit.changes:
            file_counts[change.path] += 1
            if change.old_path:
                file_counts[change.old_path] += 1

    top_files = ", ".join(path for path, _ in file_counts.most_common(2)) if file_counts else hotspot
    subject = infer_subject(hotspot)
    contributor_text = ", ".join(result.contributors) if result.contributors else "no contributors recorded"
    return (
        f"The selected {result.commit_count} commits were dominated by {dominant_category.lower()} work and appeared to focus on {subject}. "
        f"The most frequently touched area was {hotspot}, with repeat changes in {top_files}. "
        f"Contributors included {contributor_text}."
    )


def infer_subject(path: str) -> str:
    lowered = path.lower()
    if any(token in lowered for token in ("auth", "login", "session", "token", "oauth", "jwt")):
        return "authentication"
    if any(token in lowered for token in ("api", "route", "endpoint", "handler")):
        return "API behavior"
    if any(token in lowered for token in ("db", "schema", "migration", "sql", "table")):
        return "database changes"
    if any(token in lowered for token in ("test", "spec")):
        return "testing"
    if lowered.endswith((".md", ".rst", ".txt")):
        return "documentation"
    return "project evolution"
