from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .git_engine import build_analysis
from .html_report import generate_html_report
from .utils import normalize_repo_path


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for GitLens Zero."""
    parser = argparse.ArgumentParser(
        prog="gitlens",
        description="Zero-dependency Git history explainer for commits and project evolution.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a git revision range.")
    analyze_parser.add_argument("range", help="Revision range such as HEAD~10..HEAD or main..feature-auth")
    analyze_parser.add_argument("--repo", dest="repo", help="Repository path. Defaults to current directory.")

    stats_parser = subparsers.add_parser("stats", help="Show summary statistics for a revision range.")
    stats_parser.add_argument("range", help="Revision range such as HEAD~10..HEAD or main..feature-auth")
    stats_parser.add_argument("--repo", dest="repo", help="Repository path. Defaults to current directory.")

    report_parser = subparsers.add_parser("report", help="Generate a standalone HTML report.")
    report_parser.add_argument("range", help="Revision range such as HEAD~10..HEAD or main..feature-auth")
    report_parser.add_argument("--repo", dest="repo", help="Repository path. Defaults to current directory.")
    report_parser.add_argument("--html", dest="html_path", help="Output file path for the HTML report.")

    version_parser = subparsers.add_parser("version", help="Print the program version.")

    return parser


def run_cli(args: argparse.Namespace) -> int:
    """Dispatch the command to the relevant analysis workflow."""
    if not getattr(args, "command", None):
        raise SystemExit("A command is required. Use --help for usage information.")

    if args.command == "version":
        print("gitlens-zero 0.1.0")
        return 0

    repo_path = normalize_repo_path(getattr(args, "repo", None))
    range_spec = args.range

    if args.command == "analyze":
        result = build_analysis(repo_path, range_spec)
        print(format_analysis_output(result))
        return 0

    if args.command == "stats":
        result = build_analysis(repo_path, range_spec)
        print(format_stats_output(result))
        return 0

    if args.command == "report":
        result = build_analysis(repo_path, range_spec)
        output = args.html_path or "report.html"
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = (Path.cwd() / output_path).resolve()
        html_report = generate_html_report(result)
        output_path.write_text(html_report, encoding="utf-8")
        print(f"HTML report written to {output_path}")
        return 0

    raise SystemExit(f"Unsupported command: {args.command}")


def format_analysis_output(result) -> str:
    """Format a human-readable narrative analysis."""
    return (
        f"Commit count: {result.commit_count}\n"
        f"Contributors: {', '.join(result.contributors) if result.contributors else 'None'}\n"
        f"Categories: {result.categories}\n"
        f"Hotspots: {result.hotspots}\n"
        f"Summary: {result.summary}\n"
        f"Impact score: {result.impact_score}\n"
        f"Impacts: {', '.join(result.impacts) if result.impacts else 'None'}"
    )


def format_stats_output(result) -> str:
    """Format a compact statistics summary."""
    total_additions = sum(commit.insertions for commit in result.commits)
    total_deletions = sum(commit.deletions for commit in result.commits)
    total_files_changed = sum(commit.files_changed for commit in result.commits)
    lines = [
        f"Total commits: {result.commit_count}",
        f"Files changed: {total_files_changed}",
        f"Additions: {total_additions}",
        f"Deletions: {total_deletions}",
        f"Contributors: {len(result.contributors)}",
        f"Top categories: {result.categories}",
    ]
    return "\n".join(lines)
