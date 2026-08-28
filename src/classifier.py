from __future__ import annotations

import re


def classify_commit(message: str, diff: str) -> str:
    """Assign a commit category based on the commit subject and diff text."""
    text = f"{message} {diff or ''}".lower()
    normalized = message.lower()

    if re.search(r"\b(?:config|settings|env|yaml|toml|requirements|docker|deploy|chore|ci|build)\b", normalized):
        return "Configuration"
    if any(keyword in text for keyword in ["feat", "feature", "add ", "new ", "implement", "introduce", "support"]):
        return "Feature"
    if re.search(r"\b(?:fix|fixes|fixed|bug|issue|patch|resolve|resolved|error|handle|crash)\b", normalized):
        return "Bug Fix"
    if any(keyword in text for keyword in ["refactor", "cleanup", "simplify", "restructure", "rename", "optimize"]):
        return "Refactor"
    if any(keyword in text for keyword in ["docs", "doc", "readme", "guide", "documentation", "markdown"]):
        return "Documentation"
    if any(keyword in text for keyword in ["test", "tests", "unit", "spec", "coverage", "assert", "fixture"]):
        return "Test"
    if any(keyword in text for keyword in ["security", "auth", "jwt", "token", "oauth", "permission", "vuln", "cve", "secure"]):
        return "Security"

    return "Feature"
