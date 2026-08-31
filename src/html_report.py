from __future__ import annotations

from collections import Counter
import html as html_lib

from .models import AnalysisResult, Commit, DomainFinding, ExcludedFile

RISK_COLORS = {
    "Low": "#4ade80",
    "Medium": "#fbbf24",
    "High": "#f87171",
}


def generate_html_report(result: AnalysisResult) -> str:
    """Generate a polished, dependency-free HTML report.

    The report is organized so a reader can always tell what kind of claim
    each section is making: FACT (directly observed from Git), DETECTED
    (pattern-based classification of commits), HEURISTIC (interpreted
    engineering-domain findings with evidence/confidence), and POTENTIAL
    IMPACT (a qualitative, explainable risk rating -- never a bare number).
    """
    commit_count = result.commit_count
    contributors_count = len(result.contributors)
    additions = sum(commit.insertions for commit in result.commits)
    deletions = sum(commit.deletions for commit in result.commits)

    contributors_html = build_contributor_rows(result.commits)
    hotspots_html = build_hotspot_rows(result.hotspots)
    changed_areas_html = build_changed_areas_rows(result.changed_areas)
    timeline_html = build_timeline_rows(result.commits)
    what_changed_html = build_what_changed_rows(result)
    domain_findings_html = build_domain_findings_rows(result.domain_findings)
    risk_reasons_html = build_risk_reasons_rows(result.risk.reasons)
    category_bars_html = render_category_bars(result.categories)
    excluded_html = build_excluded_rows(result.excluded_files)
    risk_color = RISK_COLORS.get(result.risk.level, "#a7b4cc")

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "  <title>GitLens Zero Report</title>\n"
        "  <style>\n"
        "    :root {\n"
        "      --bg: #07111f;\n"
        "      --panel: rgba(11, 18, 32, 0.96);\n"
        "      --text: #edf3ff;\n"
        "      --muted: #a7b4cc;\n"
        "      --accent: #7dd3fc;\n"
        "      --accent-2: #c4b5fd;\n"
        "      --border: #26344a;\n"
        "      --risk: " + risk_color + ";\n"
        "    }\n"
        "    * { box-sizing: border-box; }\n"
        "    body { margin: 0; font-family: 'Segoe UI', 'Trebuchet MS', Arial, sans-serif; color: var(--text); background: radial-gradient(circle at top left, rgba(125, 211, 252, 0.16), transparent 24%), radial-gradient(circle at top right, rgba(196, 181, 253, 0.14), transparent 26%), linear-gradient(145deg, #030712, #07111f 45%, #0b1525); }\n"
        "    .container { max-width: 1240px; margin: 0 auto; padding: 28px 18px 56px; }\n"
        "    .hero { display: grid; gap: 18px; margin-bottom: 22px; }\n"
        "    .brand { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; }\n"
        "    .title { font-size: clamp(2rem, 4vw, 3.25rem); font-weight: 800; letter-spacing: -0.03em; }\n"
        "    .subtitle { color: var(--muted); max-width: 74ch; line-height: 1.6; margin-top: 8px; }\n"
        "    .pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(125, 211, 252, 0.12); color: var(--accent); border: 1px solid rgba(125, 211, 252, 0.24); }\n"
        "    .tag { display: inline-flex; align-items: center; padding: 3px 9px; border-radius: 999px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px; }\n"
        "    .tag-fact { background: rgba(125, 211, 252, 0.16); color: #7dd3fc; border: 1px solid rgba(125, 211, 252, 0.3); }\n"
        "    .tag-detected { background: rgba(196, 181, 253, 0.16); color: #c4b5fd; border: 1px solid rgba(196, 181, 253, 0.3); }\n"
        "    .tag-heuristic { background: rgba(251, 191, 36, 0.14); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }\n"
        "    .tag-impact { background: rgba(248, 113, 113, 0.14); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }\n"
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }\n"
        "    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 18px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24); }\n"
        "    .metric-label { color: var(--muted); font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; }\n"
        "    .metric-value { margin-top: 10px; font-size: 2rem; font-weight: 800; }\n"
        "    .section { margin-top: 22px; }\n"
        "    .section h2 { margin: 0 0 4px; font-size: 1.15rem; letter-spacing: 0.02em; }\n"
        "    .section-note { color: var(--muted); font-size: 0.85rem; margin: 0 0 12px; }\n"
        "    table { width: 100%; border-collapse: collapse; }\n"
        "    th, td { border-bottom: 1px solid var(--border); padding: 11px 10px; text-align: left; vertical-align: top; }\n"
        "    th { color: var(--muted); font-weight: 600; }\n"
        "    ul { margin: 0; padding-left: 18px; }\n"
        "    li { margin: 0 0 8px; line-height: 1.5; }\n"
        "    .summary { line-height: 1.7; color: #dbeafe; }\n"
        "    .muted { color: var(--muted); }\n"
        "    .two-col { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr); gap: 14px; }\n"
        "    .stack { display: grid; gap: 14px; }\n"
        "    .bars { display: grid; gap: 10px; }\n"
        "    .bar { display: grid; gap: 6px; }\n"
        "    .bar-track { height: 10px; border-radius: 999px; background: #102036; overflow: hidden; }\n"
        "    .bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }\n"
        "    .timeline-item { display: grid; gap: 5px; padding: 12px 0; border-bottom: 1px solid var(--border); }\n"
        "    .timeline-head { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; }\n"
        "    .timeline-message { font-weight: 600; }\n"
        "    .timeline-meta { color: var(--muted); font-size: 0.92rem; }\n"
        "    .badge-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }\n"
        "    .badge { padding: 6px 10px; border-radius: 999px; background: rgba(196, 181, 253, 0.11); border: 1px solid rgba(196, 181, 253, 0.2); color: #ddd6fe; }\n"
        "    .list-card ul { margin-top: 2px; }\n"
        "    .risk-value { margin-top: 10px; font-size: 2rem; font-weight: 800; color: var(--risk); }\n"
        "    .confidence-tag { font-size: 0.72rem; color: var(--muted); margin-left: 6px; font-weight: 600; }\n"
        "    code { background: #0d1a2c; border: 1px solid var(--border); border-radius: 6px; padding: 1px 6px; font-size: 0.9em; }\n"
        "    @media (max-width: 880px) { .two-col { grid-template-columns: 1fr; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <div class="container">\n'
        '    <div class="hero">\n'
        '      <div class="brand">\n'
        "        <div>\n"
        '          <div class="title">GitLens Zero</div>\n'
        '          <div class="subtitle">Zero-dependency Git history analysis. Facts, detected changes, heuristic interpretation, and potential impact are reported separately so nothing is overstated.</div>\n'
        "        </div>\n"
        f'        <div class="pill">Revision range: {html_lib.escape(result.revision_range or "(unspecified)")}</div>\n'
        "      </div>\n"
        '      <div class="grid">\n'
        f'        <div class="card"><div class="metric-label">Commit count</div><div class="metric-value">{commit_count}</div></div>\n'
        f'        <div class="card"><div class="metric-label">Contributors</div><div class="metric-value">{contributors_count}</div></div>\n'
        f'        <div class="card"><div class="metric-label">Additions / deletions</div><div class="metric-value">{additions} / {deletions}</div></div>\n'
        f'        <div class="card"><div class="metric-label">File hotspots</div><div class="metric-value">{len(result.hotspots)}</div></div>\n'
        "      </div>\n"
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>Project Overview</h2>\n"
        '      <p class="section-note">Directly observed counts from Git output -- no interpretation applied.</p>\n'
        '      <div class="two-col">\n'
        f'        <div class="card summary">{html_lib.escape(result.summary)}</div>\n'
        '        <div class="stack">\n'
        '          <div class="card">\n'
        '            <div class="metric-label">Category distribution (detected)</div>\n'
        f"            {category_bars_html}\n"
        "          </div>\n"
        '          <div class="card">\n'
        '            <div class="metric-label">Potential impact</div>\n'
        f'            <div class="risk-value">{html_lib.escape(result.risk.level)}<span class="confidence-tag">confidence: {html_lib.escape(result.risk.confidence)}</span></div>\n'
        '            <div class="muted">Explainable heuristic rating, not a formal risk certification. Review recommended.</div>\n'
        "          </div>\n"
        "        </div>\n"
        "      </div>\n"
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-detected">Detected Changes</span>\n'
        "      <h2>What Changed</h2>\n"
        '      <p class="section-note">Pattern-based grouping of the actual diffs: changed areas and most-touched files.</p>\n'
        f'      <div class="card list-card">{what_changed_html}</div>\n'
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-heuristic">Heuristic Interpretation</span>\n'
        "      <h2>Engineering Domains Potentially Affected</h2>\n"
        '      <p class="section-note">Inferred from path and commit-message patterns, each with evidence and a confidence level. This is an interpretation, not a fact.</p>\n'
        f'      <div class="card list-card">{domain_findings_html}</div>\n'
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-impact">Potential Impact</span>\n'
        "      <h2>Why It Matters</h2>\n"
        '      <p class="section-note">Cautious, explainable reasoning behind the potential-impact rating above. Review recommended before relying on this.</p>\n'
        f'      <div class="card list-card">{risk_reasons_html}</div>\n'
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>Excluded Generated/Build Artifacts</h2>\n"
        '      <p class="section-note">Files matching common generated/build artifact patterns (<code>*.egg-info</code>, <code>build/</code>, <code>dist/</code>, <code>__pycache__</code>, etc.) were excluded from the statistics above. Nothing is hidden -- every excluded file and the pattern that matched it is listed here. Use <code>--exclude</code> to add patterns or <code>--include-generated</code> to disable exclusion.</p>\n'
        f'      <div class="card list-card">{excluded_html}</div>\n'
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>Timeline</h2>\n"
        f'      <div class="card">{timeline_html}</div>\n'
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>File Hotspots</h2>\n"
        '      <div class="card">\n'
        "        <table>\n"
        "          <thead><tr><th>File</th><th>Touches</th></tr></thead>\n"
        f"          <tbody>{hotspots_html}</tbody>\n"
        "        </table>\n"
        "      </div>\n"
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>Changed Areas</h2>\n"
        '      <p class="section-note">Top-level directory groupings of changed files -- a structural fact, not a domain interpretation.</p>\n'
        '      <div class="card">\n'
        "        <table>\n"
        "          <thead><tr><th>Area</th><th>Touches</th></tr></thead>\n"
        f"          <tbody>{changed_areas_html}</tbody>\n"
        "        </table>\n"
        "      </div>\n"
        "    </div>\n"
        '    <div class="section">\n'
        '      <span class="tag tag-fact">Facts</span>\n'
        "      <h2>Contributor Activity</h2>\n"
        '      <div class="card">\n'
        "        <table>\n"
        "          <thead><tr><th>Contributor</th><th>Commits</th></tr></thead>\n"
        f"          <tbody>{contributors_html}</tbody>\n"
        "        </table>\n"
        "      </div>\n"
        "    </div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>\n"
    )


def build_hotspot_rows(hotspots: dict[str, int]) -> str:
    if not hotspots:
        return '<tr><td colspan="2">No hotspots available</td></tr>'
    ordered = sorted(hotspots.items(), key=lambda item: (-item[1], item[0].lower()))
    return "".join(f"<tr><td>{html_lib.escape(path)}</td><td>{count}</td></tr>" for path, count in ordered)


def build_changed_areas_rows(changed_areas: dict[str, int]) -> str:
    if not changed_areas:
        return '<tr><td colspan="2">No changed areas available</td></tr>'
    ordered = sorted(changed_areas.items(), key=lambda item: (-item[1], item[0].lower()))
    return "".join(f"<tr><td>{html_lib.escape(area)}</td><td>{count}</td></tr>" for area, count in ordered)


def build_contributor_rows(commits: list[Commit]) -> str:
    if not commits:
        return '<tr><td colspan="2">No contributors recorded</td></tr>'
    counts = Counter(commit.author for commit in commits if commit.author)
    if not counts:
        return '<tr><td colspan="2">No contributors recorded</td></tr>'
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
    return "".join(f"<tr><td>{html_lib.escape(name)}</td><td>{count}</td></tr>" for name, count in ordered)


def build_timeline_rows(commits: list[Commit]) -> str:
    if not commits:
        return '<div class="muted">No commits available for the selected range.</div>'

    chunks: list[str] = []
    for commit in commits:
        category = commit.message.split(":", 1)[0].strip() if ":" in commit.message else "Commit"
        chunks.append(
            '<div class="timeline-item">'
            f'<div class="timeline-head"><span class="timeline-message">{html_lib.escape(commit.message)}</span><span class="timeline-meta">{html_lib.escape(commit.date)} \u00b7 {html_lib.escape(commit.author)}</span></div>'
            f'<div class="timeline-meta">{html_lib.escape(commit.hash[:7])} \u00b7 {commit.files_changed} files \u00b7 +{commit.insertions} / -{commit.deletions}</div>'
            f'<div class="badge-row"><span class="badge">{html_lib.escape(category)}</span></div>'
            "</div>"
        )
    return "".join(chunks)


def build_what_changed_rows(result: AnalysisResult) -> str:
    if not result.commits:
        return '<div class="muted">No commit evidence was available.</div>'

    items: list[str] = []

    if result.changed_areas:
        top_areas = sorted(result.changed_areas.items(), key=lambda item: (-item[1], item[0]))[:8]
        areas_text = ", ".join(f"{html_lib.escape(area)} ({count})" for area, count in top_areas)
        items.append(f"<li>Changed areas: {areas_text}</li>")

    if result.hotspots:
        top_files = sorted(result.hotspots.items(), key=lambda item: (-item[1], item[0]))[:8]
        files_text = ", ".join(f"{html_lib.escape(path)} ({count}x)" for path, count in top_files)
        items.append(f"<li>Most changed files: {files_text}</li>")

    if result.categories:
        items.append(f"<li>Commit categories (detected): {html_lib.escape(_format_counts(result.categories))}</li>")

    if not items:
        return '<div class="muted">No file evidence was available.</div>'

    return "<ul>" + "".join(items) + "</ul>"


def build_domain_findings_rows(domain_findings: list[DomainFinding]) -> str:
    if not domain_findings:
        return '<div class="muted">No engineering domains were confidently detected from paths or commit messages.</div>'
    items = []
    for finding in domain_findings:
        evidence = "; ".join(html_lib.escape(item) for item in finding.evidence) if finding.evidence else "no evidence recorded"
        items.append(
            f"<li><strong>{html_lib.escape(finding.domain)}</strong> "
            f'<span class="confidence-tag">confidence: {html_lib.escape(finding.confidence)}</span><br>{evidence}</li>'
        )
    return "<ul>" + "".join(items) + "</ul>"


def build_risk_reasons_rows(reasons: list[str]) -> str:
    if not reasons:
        return '<div class="muted">Insufficient evidence to infer potential impact.</div>'
    return "<ul>" + "".join(f"<li>{html_lib.escape(reason)}</li>" for reason in reasons) + "</ul>"


def build_excluded_rows(excluded_files: list[ExcludedFile]) -> str:
    if not excluded_files:
        return '<div class="muted">No generated/build artifacts were detected in this range.</div>'
    items = "".join(
        f"<li><code>{html_lib.escape(excluded.path)}</code> \u2014 matched pattern <code>{html_lib.escape(excluded.pattern)}</code></li>"
        for excluded in excluded_files
    )
    return "<ul>" + items + "</ul>"


def render_category_bars(categories: dict[str, int]) -> str:
    if not categories:
        return '<div class="muted">No category data available.</div>'

    total = sum(categories.values()) or 1
    ordered = sorted(categories.items(), key=lambda item: (-item[1], item[0].lower()))
    rows = []
    for category, count in ordered:
        width = max(8, round((count / total) * 100))
        rows.append(
            f'<div class="bar"><div class="timeline-meta">{html_lib.escape(category)} \u00b7 {count}</div><div class="bar-track"><div class="bar-fill" style="width: {width}%"></div></div></div>'
        )
    return '<div class="bars">' + "".join(rows) + "</div>"


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "None"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{name}: {count}" for name, count in ordered)
