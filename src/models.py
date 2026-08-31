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
    is_generated: bool = False
    exclude_pattern: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "old_path": self.old_path,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "is_binary": self.is_binary,
            "is_generated": self.is_generated,
            "exclude_pattern": self.exclude_pattern,
        }


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
            "changes": [change.as_dict() for change in self.changes],
        }


@dataclass(slots=True)
class DomainFinding:
    """A single engineering domain (e.g. Authentication, Database) potentially affected
    by the changes, together with the evidence and confidence behind the detection.

    This is a heuristic interpretation layered on top of the raw changed files/areas --
    it answers "what part of the system might this touch", not "what files changed".
    """

    domain: str
    evidence: list[str] = field(default_factory=list)
    confidence: str = "Medium"  # "High" (path-based evidence) or "Medium" (message-text only)

    def as_dict(self) -> dict[str, Any]:
        return {"domain": self.domain, "evidence": list(self.evidence), "confidence": self.confidence}


@dataclass(slots=True)
class RiskAssessment:
    """A qualitative potential-impact rating derived from an explicit, documented formula.

    This is deliberately not a numeric score: the level (Low/Medium/High) is
    always accompanied by the specific reasons and confidence behind it, so the
    rating is explainable rather than an opaque number.
    """

    level: str = "Low"  # "Low" | "Medium" | "High"
    reasons: list[str] = field(default_factory=list)
    confidence: str = "Low"  # "Low" | "Medium" | "High"

    def as_dict(self) -> dict[str, Any]:
        return {"level": self.level, "reasons": list(self.reasons), "confidence": self.confidence}


@dataclass(slots=True)
class ExcludedFile:
    """A file that was excluded from analysis because it looked like a generated/build artifact."""

    path: str
    pattern: str

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "pattern": self.pattern}


@dataclass(slots=True)
class AnalysisResult:
    """Summary statistics and findings computed from a set of commits.

    Fields are grouped by what kind of claim they make:
      - Facts: commit_count, contributors, hotspots, changed_areas, and the raw
        commit/file data on ``commits`` -- directly observed from Git output.
      - Detected changes: ``categories`` -- pattern-based commit classification.
      - Heuristic interpretation: ``domain_findings`` -- possible engineering
        domains affected, with evidence and confidence.
      - Potential impact: ``risk`` -- a qualitative, explainable risk rating.
    """

    commit_count: int
    revision_range: str = ""
    repository: str = ""
    contributors: list[str] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)
    hotspots: dict[str, int] = field(default_factory=dict)
    changed_areas: dict[str, int] = field(default_factory=dict)
    domain_findings: list[DomainFinding] = field(default_factory=list)
    risk: RiskAssessment = field(default_factory=RiskAssessment)
    summary: str = ""
    commits: list[Commit] = field(default_factory=list)
    excluded_files: list[ExcludedFile] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary representation."""
        return {
            "commit_count": self.commit_count,
            "revision_range": self.revision_range,
            "repository": self.repository,
            "contributors": self.contributors,
            "categories": self.categories,
            "hotspots": self.hotspots,
            "changed_areas": self.changed_areas,
            "domain_findings": [finding.as_dict() for finding in self.domain_findings],
            "risk": self.risk.as_dict(),
            "summary": self.summary,
            "commits": [commit.as_dict() for commit in self.commits],
            "excluded_files": [excluded.as_dict() for excluded in self.excluded_files],
        }
