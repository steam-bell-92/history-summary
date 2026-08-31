from __future__ import annotations

import re

from .models import FileChange


def classify_commit(message: str, changes: list[FileChange] | str | None = None) -> str:
    """Assign a commit category using message text, changed paths, and diff shape.

    Files flagged as generated/build artifacts (``FileChange.is_generated``)
    are excluded from path-based heuristics so that, for example, a commit
    that only regenerates ``*.egg-info`` isn't misclassified as meaningful
    "Configuration" work. If every changed file in a commit is a generated
    artifact, the commit is classified as "Build Artifacts" instead.
    """
    normalized = message.lower()
    if isinstance(changes, str):
        changes = []
    changes = changes or []

    substantive_changes = [change for change in changes if not getattr(change, "is_generated", False)]
    if changes and not substantive_changes:
        return "Build Artifacts"
    changes = substantive_changes

    if any(is_config_path(change.path) or is_config_path(change.old_path or "") for change in changes) or re.search(r"\b(?:config|settings|env|yaml|toml|requirements|docker|deploy|chore|ci|build)\b", normalized):
        return "Configuration"
    if re.search(r"\b(?:fix|fixes|fixed|bug|issue|patch|resolve|resolved|error|handle|crash)\b", normalized):
        return "Bug Fix"
    if any(is_test_path(change.path) or is_test_path(change.old_path or "") for change in changes) or re.search(r"\b(?:test|tests|unit|spec|coverage|assert|fixture)\b", normalized):
        return "Test"
    if any(is_doc_path(change.path) or is_doc_path(change.old_path or "") for change in changes) or re.search(r"\b(?:docs|doc|readme|guide|documentation|markdown)\b", normalized):
        return "Documentation"
    if any(is_security_path(change.path) or is_security_path(change.old_path or "") for change in changes) or re.search(r"\b(?:security|auth|jwt|token|oauth|permission|vuln|cve|secure)\b", normalized):
        return "Security"
    if re.search(r"\b(?:refactor|cleanup|simplify|restructure|rename|optimize)\b", normalized) or any(change.status.startswith(("R", "C")) for change in changes):
        return "Refactor"

    if re.search(r"\b(?:feat|feature|implement|introduce|support)\b", normalized):
        return "Feature"
    if any(is_api_path(change.path) or is_api_path(change.old_path or "") for change in changes):
        return "Feature"
    if any(is_frontend_path(change.path) or is_frontend_path(change.old_path or "") for change in changes):
        return "Feature"
    if any(change.path.endswith((".py", ".js", ".ts", ".tsx", ".jsx")) for change in changes):
        return "Feature"

    return "Feature"


def is_test_path(path: str) -> bool:
    return path_contains_term(path, "test") or path_contains_term(path, "tests")


def is_doc_path(path: str) -> bool:
    return path_contains_term(path, "docs") or path_contains_term(path, "doc") or path_contains_term(path, "readme") or path.endswith((".md", ".rst"))


def is_config_path(path: str) -> bool:
    return any(path_contains_term(path, token) for token in ["pyproject", "requirements", "setup", "dockerfile", "package", "config", "settings", "env"])


def is_security_path(path: str) -> bool:
    return any(path_contains_term(path, token) for token in ["auth", "login", "session", "token", "oauth", "jwt", "permission", "security"])


def is_api_path(path: str) -> bool:
    return any(path_contains_term(path, token) for token in ["api", "route", "routes", "endpoint", "handler", "controller", "server"])


def is_frontend_path(path: str) -> bool:
    return any(path_contains_term(path, token) for token in ["frontend", "ui", "component", "view", "template", "page", "tsx", "jsx", "html", "css"])


def path_contains_term(path: str, term: str) -> bool:
    tokens = path_tokens(path)
    return term.lower() in tokens


def path_tokens(path: str) -> set[str]:
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", path.replace("\\", "/").lower())
    parts = re.split(r"[^a-z0-9]+", normalized)
    return {part for part in parts if part}
