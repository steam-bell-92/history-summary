from __future__ import annotations

import fnmatch

# Default patterns for generated/build artifacts. These are common outputs of
# packaging, caching, and dependency tooling rather than hand-authored source.
# They are excluded from hotspot, classification, and domain analysis by
# default -- but never silently: every excluded file is reported back to the
# caller via ``AnalysisResult.excluded_files`` so nothing is hidden.
DEFAULT_EXCLUDE_PATTERNS: tuple[str, ...] = (
    "*.egg-info",
    "*.egg-info/*",
    "*.egg",
    ".eggs",
    ".eggs/*",
    "build",
    "build/*",
    "dist",
    "dist/*",
    "__pycache__",
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".pytest_cache/*",
    ".mypy_cache",
    ".mypy_cache/*",
    ".ruff_cache",
    ".ruff_cache/*",
    ".tox",
    ".tox/*",
    "node_modules",
    "node_modules/*",
    ".venv",
    ".venv/*",
    "venv",
    "venv/*",
    ".DS_Store",
    "*.min.js",
    "*.map",
)


def matched_exclude_pattern(path: str, patterns: tuple[str, ...] | list[str] = DEFAULT_EXCLUDE_PATTERNS) -> str | None:
    """Return the first pattern that identifies ``path`` as a generated artifact, or ``None``.

    A path matches a pattern either as a whole (``fnmatch`` against the full,
    forward-slash-normalized path) or through any single path segment matching
    the pattern's first component (so a bare directory pattern like ``build``
    or ``__pycache__`` matches that directory at any depth, e.g.
    ``src/pkg/build/output.txt``).
    """
    if not patterns:
        return None

    normalized = path.replace("\\", "/").lstrip("/")
    segments = [segment for segment in normalized.split("/") if segment]

    for pattern in patterns:
        pattern_normalized = pattern.replace("\\", "/")
        if fnmatch.fnmatch(normalized, pattern_normalized):
            return pattern
        base_pattern = pattern_normalized.split("/", 1)[0]
        if any(fnmatch.fnmatch(segment, base_pattern) for segment in segments):
            return pattern

    return None


def is_generated_artifact(path: str, patterns: tuple[str, ...] | list[str] = DEFAULT_EXCLUDE_PATTERNS) -> bool:
    """Return True if ``path`` matches a generated/build artifact pattern."""
    return matched_exclude_pattern(path, patterns) is not None


def resolve_patterns(extra_patterns: list[str] | None, include_generated: bool) -> tuple[str, ...]:
    """Resolve the effective exclusion pattern set from CLI-style options.

    ``include_generated=True`` disables exclusion entirely (returns no
    patterns), regardless of any extra patterns supplied -- this keeps the
    override explicit and predictable rather than partially applying it.
    """
    if include_generated:
        return ()
    return tuple(DEFAULT_EXCLUDE_PATTERNS) + tuple(extra_patterns or ())
