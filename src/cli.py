from __future__ import annotations

import argparse
import json
import sys
import webbrowser
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
    analyze_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    _add_exclude_arguments(analyze_parser)

    stats_parser = subparsers.add_parser("stats", help="Show summary statistics for a revision range.")
    stats_parser.add_argument("range", help="Revision range such as HEAD~10..HEAD or main..feature-auth")
    stats_parser.add_argument("--repo", dest="repo", help="Repository path. Defaults to current directory.")
    stats_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    _add_exclude_arguments(stats_parser)

    report_parser = subparsers.add_parser("report", help="Generate a standalone HTML report.")
    report_parser.add_argument("range", help="Revision range such as HEAD~10..HEAD or main..feature-auth")
    report_parser.add_argument("--repo", dest="repo", help="Repository path. Defaults to current directory.")
    report_parser.add_argument("--html", dest="html_path", help="Output file path for the HTML report.")
    report_parser.add_argument("--open", action="store_true", help="Open the generated report in a browser.")
    _add_exclude_arguments(report_parser)

    subparsers.add_parser("version", help="Print the program version.")

    return parser


def _add_exclude_arguments(subparser: argparse.ArgumentParser) -> None:
    """Add the shared, transparent generated/build artifact exclusion flags to a subcommand."""
    subparser.add_argument(
        "--exclude",
        dest="exclude_patterns",
        action="append",
        default=[],
        metavar="PATTERN",
        help=(
            "Additional glob pattern to treat as a generated/build artifact and exclude "
            "from analysis (repeatable). Applied on top of the built-in defaults "
            "(*.egg-info, build/, dist/, __pycache__, node_modules/, etc.)."
        ),
    )
    subparser.add_argument(
        "--include-generated",
        action="store_true",
        help=(
            "Do not exclude generated/build artifacts from analysis; treat every changed "
            "file as substantive. Excluded files are always listed transparently in output "
            "regardless of this flag -- this only controls whether they're counted."
        ),
    )


def run_cli(args: argparse.Namespace) -> int:
    """Dispatch the command to the relevant analysis workflow."""
    if not getattr(args, "command", None):
        return 0

    try:
        if args.command == "version":
            print("gitlens-zero 0.1.0")
            return 0

        repo_path = normalize_repo_path(getattr(args, "repo", None))
        range_spec = args.range
        exclude_patterns = getattr(args, "exclude_patterns", [])
        include_generated = getattr(args, "include_generated", False)

        if args.command == "analyze":
            result = build_analysis(repo_path, range_spec, exclude_patterns, include_generated)
            if getattr(args, "json", False):
                print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
            else:
                print(format_analysis_output(result))
            return 0

        if args.command == "stats":
            result = build_analysis(repo_path, range_spec, exclude_patterns, include_generated)
            if getattr(args, "json", False):
                print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
            else:
                print(format_stats_output(result))
            return 0

        if args.command == "report":
            result = build_analysis(repo_path, range_spec, exclude_patterns, include_generated)
            output = args.html_path or "reports/history.html"
            output_path = Path(output)
            if not output_path.is_absolute():
                output_path = (Path.cwd() / output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            html_report = generate_html_report(result)
            output_path.write_text(html_report, encoding="utf-8")
            print(f"Report saved to: {output_path}")
            if should_open_report(args):
                webbrowser.open(output_path.as_uri())
                print("Opened report in your browser.")
            return 0

        raise SystemExit(f"Unsupported command: {args.command}")
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def format_analysis_output(result) -> str:
    """Format a human-readable narrative analysis, keeping facts, detected changes,
    heuristic interpretation, and potential impact clearly separated."""
    lines = [
        f"Commit count: {result.commit_count}",
        f"Contributors: {', '.join(result.contributors) if result.contributors else 'None'}",
        f"Categories (detected): {_format_counts(result.categories)}",
        f"Changed areas (facts): {_format_counts(result.changed_areas)}",
        f"File hotspots (facts): {_format_counts(result.hotspots)}",
        "",
        "What Changed:",
        f"  {result.summary}",
        "",
        "Why It Matters (heuristic interpretation -- may affect, review recommended):",
    ]
    if result.domain_findings:
        for finding in result.domain_findings:
            evidence = "; ".join(finding.evidence) if finding.evidence else "no evidence recorded"
            lines.append(f"  - {finding.domain} (confidence: {finding.confidence}) -- {evidence}")
    else:
        lines.append("  - No engineering domains were confidently detected from paths or commit messages.")
    lines.append("")
    lines.append(f"Potential impact: {result.risk.level} (confidence: {result.risk.confidence})")
    for reason in result.risk.reasons:
        lines.append(f"  - {reason}")

    if result.excluded_files:
        lines.append("")
        lines.append(
            f"Excluded generated/build artifacts ({len(result.excluded_files)}) -- "
            "not counted in the statistics above:"
        )
        for excluded in result.excluded_files[:10]:
            lines.append(f"  - {excluded.path} (matched pattern: {excluded.pattern})")
        if len(result.excluded_files) > 10:
            lines.append(f"  ... and {len(result.excluded_files) - 10} more")

    return "\n".join(lines)


def format_stats_output(result) -> str:
    """Format a compact, fact-only statistics summary."""
    total_additions = sum(commit.insertions for commit in result.commits)
    total_deletions = sum(commit.deletions for commit in result.commits)
    total_files_changed = sum(commit.files_changed for commit in result.commits)
    lines = [
        f"Total commits: {result.commit_count}",
        f"Files changed: {total_files_changed}",
        f"Additions: {total_additions}",
        f"Deletions: {total_deletions}",
        f"Contributors: {len(result.contributors)}",
        f"Top categories: {_format_counts(result.categories)}",
        f"Changed areas: {_format_counts(result.changed_areas)}",
    ]
    if result.excluded_files:
        lines.append(f"Excluded generated/build artifacts: {len(result.excluded_files)} (not counted above)")
    return "\n".join(lines)


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "None"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{name}: {count}" for name, count in ordered)


def should_open_report(args: argparse.Namespace) -> bool:
    if getattr(args, "open", False):
        return True
    if not sys.stdin or not sys.stdin.isatty():
        return False

    try:
        response = input("Would you like to open the report in your browser? [y/N]: ").strip().lower()
    except (EOFError, OSError):
        return False
    return response in {"y", "yes"}
