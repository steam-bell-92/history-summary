from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FileChange:
    """Represents a single file-level change captured from Git."""

    path: str
    old_path: str | None = None
    status: str = "M"
    additions: int = 0
    deletions: int = 0
    is_binary: bool = False


@dataclass(slots=True)
class CommitStats:
    """Aggregate commit-level stats derived from Git output."""

    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


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
    changes: list[FileChange] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "hash": self.hash,
            "author": self.author,
            "date": self.date,
            "message": self.message,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "changes": [
                {
                    "path": change.path,
                    "old_path": change.old_path,
                    "status": change.status,
                    "additions": change.additions,
                    "deletions": change.deletions,
                    "is_binary": change.is_binary,
                }
                for change in self.changes
            ],
        }


@dataclass(slots=True)
class AnalysisResult:
    """Summary statistics computed from a set of commits."""

    commit_count: int
    revision_range: str = ""
    repository: str = ""
    contributors: list[str] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)
    hotspots: dict[str, int] = field(default_factory=dict)
    impact_score: int = 0
    impact_reasons: list[str] = field(default_factory=list)
    summary: str = ""
    impacts: list[str] = field(default_factory=list)
    commits: list[Commit] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        return {
            "commit_count": self.commit_count,
            "revision_range": self.revision_range,
            "repository": self.repository,
            "contributors": self.contributors,
            "categories": self.categories,
            "hotspots": self.hotspots,
            "impact_score": self.impact_score,
            "impact_reasons": self.impact_reasons,
            "summary": self.summary,
            "impacts": self.impacts,
            "commits": [commit.as_dict() for commit in self.commits],
        }
