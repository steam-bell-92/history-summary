from __future__ import annotations

from collections import Counter


def detect_impacts(message: str, diff_text: str) -> list[str]:
    """Infer domain impacts from commit text and diff content."""
    combined = f"{message} {diff_text or ''}".lower()
    impacts: list[str] = []

    if any(term in combined for term in ["auth", "jwt", "login", "token", "session", "oauth", "permission"]):
        impacts.append("Authentication")
    if any(term in combined for term in ["db", "database", "schema", "migration", "sql", "orm", "table"]):
        impacts.append("Database")
    if any(term in combined for term in ["api", "endpoint", "route", "http", "rest", "request", "response"]):
        impacts.append("API")
    if any(term in combined for term in ["ui", "frontend", "react", "template", "css", "html", "component", "page"]):
        impacts.append("Frontend")
    if any(term in combined for term in ["test", "spec", "pytest", "unit", "assert", "integration"]):
        impacts.append("Tests")
    if any(term in combined for term in ["doc", "readme", "guide", "markdown", "docs"]):
        impacts.append("Documentation")

    return impacts


def assess_impact(impacts: list[str]) -> int:
    """Convert impact domains into a numeric risk/importance score."""
    score = len(set(impacts))
    return min(score * 2, 10)
