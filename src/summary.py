from __future__ import annotations

from .models import AnalysisResult


def generate_summary(result: AnalysisResult) -> str:
    """Build a concise human-readable summary from analysis results."""
    if result.commit_count == 0:
        return "No commit history is available for the selected range."

    commit_count = result.commit_count
    categories = result.categories
    contributors = result.contributors
    dominant_category = max(categories.items(), key=lambda item: item[1])[0] if categories else "Feature"
    hotspot = max(result.hotspots.items(), key=lambda item: item[1])[0] if result.hotspots else "project files"

    primary_topic = hotspot.lower().replace("/", " ").replace(".py", "").replace(".js", "").replace(".ts", "").strip()
    if "auth" in primary_topic or "login" in primary_topic or "session" in primary_topic:
        subject = "authentication"
    elif "api" in primary_topic or "route" in primary_topic:
        subject = "API"
    elif "db" in primary_topic or "schema" in primary_topic or "migration" in primary_topic:
        subject = "database"
    else:
        subject = "project evolution"

    contributor_text = ", ".join(contributors) if contributors else "the project team"
    return (
        f"The last {commit_count} commits primarily focused on {subject}. "
        f"The dominant category was {dominant_category}, with emphasis on {hotspot}. "
        f"Contributors included {contributor_text}."
    )
