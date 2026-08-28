from __future__ import annotations

import re
from typing import Iterable

from .models import Commit


def parse_git_log_output(output: str) -> list[Commit]:
    """Parse raw git log output into a list of Commit objects."""
    blocks: list[str] = split_commit_blocks(output)
    commits: list[Commit] = []

    for block in blocks:
        commit = parse_commit_block(block)
        if commit is not None:
            commits.append(commit)

    return commits


def split_commit_blocks(output: str) -> list[str]:
    """Split a git log stream into discrete commit blocks."""
    if not output.strip():
        return []

    blocks = re.split(r"\n(?=commit\s+[0-9a-fA-F]+)", output)
    cleaned = [block.strip() for block in blocks if block.strip()]
    return cleaned


def parse_commit_block(block: str) -> Commit | None:
    """Translate a single git log block into a Commit dataclass."""
    if not block.strip():
        return None

    hash_match = re.search(r"commit\s+([0-9a-fA-F]+)", block)
    author_match = re.search(r"Author:\s*(.+?)(?:\s*<.*?>)?\s*$", block, re.MULTILINE)
    date_match = re.search(r"Date:\s*(.+)$", block, re.MULTILINE)

    message = extract_message(block)
    if not message:
        message = "untitled commit"

    files_changed = extract_number(block, r"(\d+)\s+files changed")
    insertions = extract_number(block, r"(\d+)\s+insertions?\(\+\)")
    deletions = extract_number(block, r"(\d+)\s+deletions?\(-\)")

    return Commit(
        hash=hash_match.group(1) if hash_match else "unknown",
        author=(author_match.group(1) if author_match else "Unknown").strip(),
        date=(date_match.group(1) if date_match else "unknown").strip(),
        message=message,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        diff=block,
    )


def extract_message(block: str) -> str:
    """Extract the commit subject from a git log block."""
    lines = block.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("commit ") or stripped.startswith("Author:") or stripped.startswith("Date:"):
            continue
        if stripped.startswith("diff --git ") or stripped.startswith("--- ") or stripped.startswith("+++ "):
            continue
        if stripped.startswith("index "):
            continue
        if re.match(r"^\d+\s+files changed", stripped):
            continue
        if index > 0 and re.match(r"^[0-9]+\s+files? changed", stripped):
            continue
        if stripped.startswith("    "):
            return stripped.strip()
        return stripped
    return "untitled commit"


def extract_number(text: str, pattern: str) -> int:
    """Find a numeric value in the commit summary text."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def parse_commits_from_output(output: str) -> Iterable[Commit]:
    """Compatibility helper returning commit objects from a git log stream."""
    return parse_git_log_output(output)
