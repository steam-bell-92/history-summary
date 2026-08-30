from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import Commit, FileChange


@dataclass(slots=True)
class ImpactAssessment:
    """Explain how impact domains map to a risk score."""

    domains: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    score: int = 0

DOMAIN_PATTERNS = {
    "Authentication": ["auth", "login", "session", "token", "oauth", "jwt", "permission"],
    "Database": ["db", "database", "schema", "migration", "sql", "orm", "table"],
    "API": ["api", "endpoint", "route", "http", "rest", "request", "response"],
    "Frontend": ["frontend", "ui", "react", "template", "css", "html", "component", "page"],
    "Tests": ["test", "tests", "spec", "pytest", "unit", "assert", "integration"],
    "Documentation": ["doc", "readme", "guide", "markdown", "docs"],
}


def detect_change_domains(message: str, changes: list[FileChange]) -> tuple[list[str], list[str]]:
    """Detect change domains using commit message and structured file paths only."""
    message_tokens = path_tokens(message)
    domains: list[str] = []
    reasons: list[str] = []

    for domain, terms in DOMAIN_PATTERNS.items():
        matched_paths = [change.path for change in changes if path_matches(change.path, terms) or path_matches(change.old_path or "", terms)]
        matched_message = [term for term in terms if term.lower() in message_tokens]
        if matched_paths or matched_message:
            domains.append(domain)
            evidence = []
            if matched_message:
                evidence.append(f"message terms: {', '.join(sorted(set(matched_message)))}")
            if matched_paths:
                evidence.append(f"paths: {', '.join(sorted(set(matched_paths)))}")
            reasons.append(f"{domain}: {'; '.join(evidence)}")

    return domains, reasons


def assess_impact(impacts: list[str], commits: list[Commit] | None = None) -> int:
    """Convert impact domains and change breadth into a numeric score."""
    unique_impacts = set(impacts)
    score = len(unique_impacts) * 2
    if len(commits or []) >= 10:
        score += 1
    if any(commit.insertions + commit.deletions > 200 for commit in commits or []):
        score += 2
    if any(commit.files_changed >= 5 for commit in commits or []):
        score += 1
    return min(score, 10)


def explain_impact_score(score: int, impacts: list[str], reasons: list[str], commits: list[Commit] | None = None) -> list[str]:
    """Describe why the final impact score was assigned."""
    explanations: list[str] = []
    unique_impacts = sorted(set(impacts))
    if unique_impacts:
        explanations.append(f"Detected domains: {', '.join(unique_impacts)}")
    if reasons:
        explanations.extend(reasons)
    if commits:
        large_changes = [commit.hash[:7] for commit in commits if commit.insertions + commit.deletions > 200]
        if large_changes:
            explanations.append(f"Large diff volume in commits: {', '.join(large_changes)}")
        wide_changes = [commit.hash[:7] for commit in commits if commit.files_changed >= 5]
        if wide_changes:
            explanations.append(f"Broad file spread in commits: {', '.join(wide_changes)}")
    explanations.append(f"Final score: {score}/10")
    return explanations


def path_matches(path: str, terms: list[str]) -> bool:
    tokens = path_tokens(path)
    return any(term.lower() in tokens for term in terms)


def path_tokens(path: str) -> set[str]:
    normalized = path.replace("\\", "/").lower()
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", normalized)
    return {token for token in re.split(r"[^a-z0-9]+", normalized) if token}
