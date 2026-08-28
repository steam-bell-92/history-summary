from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Sequence


def run_git_command(repo_path: str | Path, args: Sequence[str]) -> str:
    """Execute a git command in a repository and return stdout as text."""
    repository = Path(repo_path)
    command = ["git", *list(args)]
    result = subprocess.run(
        command,
        cwd=str(repository),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"Git command failed: {' '.join(command)} :: {message}")
    return result.stdout


def normalize_repo_path(path: str | None) -> Path:
    """Resolve a repository path from user input or the current directory."""
    if path:
        return Path(path).expanduser().resolve()
    return Path.cwd().resolve()


def parse_file_hotspots(diff_text: str) -> list[str]:
    """Extract file paths mentioned in a diff."""
    files: list[str] = []
    seen: set[str] = set()

    for line in diff_text.splitlines():
        match = re.search(r"^(?:diff --git a/|--- a/|\+\+\+ b/)(.+)$", line)
        if match:
            file_name = match.group(1).strip()
            if file_name and file_name not in seen:
                files.append(file_name)
                seen.add(file_name)

    for line in diff_text.splitlines():
        if line.startswith("index "):
            continue
        if line.startswith("diff --git "):
            continue

    return files


def sanitize_text(value: str) -> str:
    """Convert raw git output into plain text without control characters."""
    return re.sub(r"\s+", " ", value).strip()


def path_to_display(path: str) -> str:
    """Return a clean display path for the CLI and HTML report."""
    return path.replace("\\", "/")


def ensure_dir(path: str | os.PathLike[str]) -> Path:
    """Create a directory if it does not already exist."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target
