from __future__ import annotations

import re
from collections import OrderedDict
from typing import Iterable

from .models import Commit, FileChange


RECORD_SEPARATOR = "\x1e"
FIELD_SEPARATOR = "\x1f"


def parse_git_log_output(output: str) -> list[Commit]:
    """Parse raw git log output into a list of Commit objects."""
    if FIELD_SEPARATOR in output or RECORD_SEPARATOR in output:
        return parse_structured_git_log_output(output)

    blocks: list[str] = split_commit_blocks(output)
    commits: list[Commit] = []

    for block in blocks:
        commit = parse_commit_block(block)
        if commit is not None:
            commits.append(commit)

    return commits


def parse_structured_git_log_output(output: str) -> list[Commit]:
    """Parse machine-readable git log output into commit objects."""
    commits: list[Commit] = []
    for record in output.split(RECORD_SEPARATOR):
        record = record.strip("\n\r\t ")
        if not record:
            continue
        fields = record.split(FIELD_SEPARATOR)
        if len(fields) < 4:
            continue
        commits.append(
            Commit(
                hash=fields[0].strip() or "unknown",
                author=fields[1].strip() or "Unknown",
                date=fields[2].strip() or "unknown",
                message=fields[3].strip() or "untitled commit",
            )
        )
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


def parse_name_status_output(output: str) -> list[FileChange]:
    """Parse `git diff-tree --name-status -z` output into file changes."""
    tokens = [token for token in output.split("\0") if token]
    changes: list[FileChange] = []
    index = 0

    while index < len(tokens):
        status = tokens[index].strip()
        index += 1
        if not status:
            continue

        if status.startswith(("R", "C")):
            if index + 1 >= len(tokens):
                break
            old_path = tokens[index]
            new_path = tokens[index + 1]
            index += 2
            changes.append(FileChange(path=new_path, old_path=old_path, status=status))
            continue

        if index >= len(tokens):
            break
        path = tokens[index]
        index += 1
        changes.append(FileChange(path=path, status=status))

    return changes


def parse_numstat_output(output: str) -> list[FileChange]:
    """Parse `git diff-tree --numstat -z` output into file changes."""
    tokens = [token for token in output.split("\0") if token]
    changes: list[FileChange] = []
    index = 0

    while index < len(tokens):
        record = tokens[index]
        index += 1
        parts = record.split("\t")
        if len(parts) < 2:
            continue

        additions = parse_numstat_value(parts[0])
        deletions = parse_numstat_value(parts[1])

        if len(parts) >= 3 and parts[2]:
            path = "\t".join(parts[2:])
            changes.append(
                FileChange(
                    path=path,
                    additions=additions,
                    deletions=deletions,
                    is_binary=additions < 0 or deletions < 0,
                )
            )
            continue

        if index + 1 > len(tokens):
            break
        old_path = tokens[index] if index < len(tokens) else ""
        new_path = tokens[index + 1] if index + 1 < len(tokens) else old_path
        index += 2
        changes.append(
            FileChange(
                path=new_path or old_path,
                old_path=old_path or None,
                additions=additions,
                deletions=deletions,
                is_binary=additions < 0 or deletions < 0,
            )
        )

    return changes


def parse_numstat_value(value: str) -> int:
    """Convert a numstat field into an integer, preserving binary markers."""
    if value == "-":
        return -1
    try:
        return int(value)
    except ValueError:
        return 0


def merge_file_changes(name_status_changes: list[FileChange], numstat_changes: list[FileChange]) -> list[FileChange]:
    """Merge structured name-status and numstat records by file path."""
    merged: OrderedDict[tuple[str | None, str], FileChange] = OrderedDict()

    for change in name_status_changes:
        key = (change.old_path, change.path)
        merged[key] = FileChange(
            path=change.path,
            old_path=change.old_path,
            status=change.status,
            additions=change.additions,
            deletions=change.deletions,
            is_binary=change.is_binary,
        )

    for change in numstat_changes:
        key = (change.old_path, change.path)
        existing = merged.get(key)
        if existing is None:
            merged[key] = FileChange(
                path=change.path,
                old_path=change.old_path,
                status=change.status,
                additions=change.additions,
                deletions=change.deletions,
                is_binary=change.is_binary,
            )
            continue
        existing.additions = change.additions
        existing.deletions = change.deletions
        existing.is_binary = change.is_binary

    return list(merged.values())


def extract_number(text: str, pattern: str) -> int:
    """Find a numeric value in the commit summary text."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def parse_commits_from_output(output: str) -> Iterable[Commit]:
    """Compatibility helper returning commit objects from a git log stream."""
    return parse_git_log_output(output)
