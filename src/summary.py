from __future__ import annotations

from .models import AnalysisResult


def generate_summary(result: AnalysisResult) -> str:
    """Build a concise, fact-based summary of the analyzed range.

    Every sentence here is derived directly from computed statistics
    (commit/file/line counts, classification counts, hotspot and area
    counts). No claims about intent, purpose, or subject matter are
    invented -- domain interpretation and potential impact are reported
    separately (see ``impact.py``) precisely so this summary can stick to
    what was actually observed.
    """
    if result.commit_count == 0:
        return "No commit history is available for the selected range."

    total_additions = sum(commit.insertions for commit in result.commits)
    total_deletions = sum(commit.deletions for commit in result.commits)
    total_file_touches = sum(commit.files_changed for commit in result.commits)
    contributor_text = ", ".join(result.contributors) if result.contributors else "no recorded contributors"

    sentences = [
        f"{result.commit_count} commit(s) from {contributor_text} touched {total_file_touches} file(s) "
        f"(+{total_additions}/-{total_deletions} lines)."
    ]

    if result.categories:
        dominant_category, dominant_count = max(result.categories.items(), key=lambda item: (item[1], item[0]))
        sentences.append(
            f"The dominant commit category was {dominant_category} ({dominant_count} of {result.commit_count} commits)."
        )

    top_files = sorted(result.hotspots.items(), key=lambda item: (-item[1], item[0]))[:3]
    if top_files:
        files_text = ", ".join(f"{path} ({count}x)" for path, count in top_files)
        sentences.append(f"Most frequently touched file(s): {files_text}.")

    top_areas = sorted(result.changed_areas.items(), key=lambda item: (-item[1], item[0]))[:3]
    if top_areas:
        areas_text = ", ".join(f"{area} ({count})" for area, count in top_areas)
        sentences.append(f"Most changed area(s): {areas_text}.")

    if result.excluded_files:
        sentences.append(
            f"{len(result.excluded_files)} generated/build artifact file(s) were excluded from this analysis "
            "(see the exclusion report for the full list and matched patterns)."
        )

    return " ".join(sentences)
