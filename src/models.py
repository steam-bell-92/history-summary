from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Commit:
    """Represents a single git commit extracted from repository history."""

    hash: str
    author: str
    date: str
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    diff: str = ""


@dataclass(slots=True)
class AnalysisResult:
    """Summary statistics computed from a set of commits."""

    commit_count: int
    contributors: list[str] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)
    hotspots: dict[str, int] = field(default_factory=dict)
    impact_score: int = 0
    summary: str = ""
    impacts: list[str] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        return {
            "commit_count": self.commit_count,
            "contributors": self.contributors,
            "categories": self.categories,
            "hotspots": self.hotspots,
            "impact_score": self.impact_score,
            "summary": self.summary,
            "impacts": self.impacts,
        }
