from __future__ import annotations

from collections import Counter
import html as html_lib

from .models import AnalysisResult, Commit


def generate_html_report(result: AnalysisResult) -> str:
    """Generate a polished, dependency-free HTML report."""
    commit_count = result.commit_count
    contributors_count = len(result.contributors)
    additions = sum(commit.insertions for commit in result.commits)
    deletions = sum(commit.deletions for commit in result.commits)
    contributors_html = build_contributor_rows(result.commits)
    hotspots_html = build_hotspot_rows(result.hotspots)
    timeline_html = build_timeline_rows(result.commits)
    what_changed_html = build_what_changed_rows(result.commits)
    why_it_matters_html = build_why_it_matters_rows(result.impact_reasons)
    impact_html = build_impact_rows(result.impacts)
    category_bars_html = render_category_bars(result.categories)

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
        "    }\n"
        "    * { box-sizing: border-box; }\n"
        "    body { margin: 0; font-family: 'Segoe UI', 'Trebuchet MS', Arial, sans-serif; color: var(--text); background: radial-gradient(circle at top left, rgba(125, 211, 252, 0.16), transparent 24%), radial-gradient(circle at top right, rgba(196, 181, 253, 0.14), transparent 26%), linear-gradient(145deg, #030712, #07111f 45%, #0b1525); }\n"
        "    .container { max-width: 1240px; margin: 0 auto; padding: 28px 18px 56px; }\n"
        "    .hero { display: grid; gap: 18px; margin-bottom: 22px; }\n"
        "    .brand { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; }\n"
        "    .title { font-size: clamp(2rem, 4vw, 3.25rem); font-weight: 800; letter-spacing: -0.03em; }\n"
        "    .subtitle { color: var(--muted); max-width: 74ch; line-height: 1.6; margin-top: 8px; }\n"
        "    .pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(125, 211, 252, 0.12); color: var(--accent); border: 1px solid rgba(125, 211, 252, 0.24); }\n"
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }\n"
        "    .card { background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 18px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24); }\n"
        "    .metric-label { color: var(--muted); font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase; }\n"
        "    .metric-value { margin-top: 10px; font-size: 2rem; font-weight: 800; }\n"
        "    .section { margin-top: 22px; }\n"
        "    .section h2 { margin: 0 0 12px; font-size: 1.15rem; letter-spacing: 0.02em; }\n"
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
        "    @media (max-width: 880px) { .two-col { grid-template-columns: 1fr; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <div class="container">\n'
        '    <div class="hero">\n'
        '      <div class="brand">\n'
        "        <div>\n"
        "          <div class=\"title\">GitLens Zero</div>\n"
        "          <div class=\"subtitle\">Zero-dependency Git history analysis with explainable summaries, timeline context, and reportable evidence from the selected revision range.</div>\n"
        "        </div>\n"
        f'        <div class="pill">Revision range: {html_lib.escape(result.revision_range or "(unspecified)")}</div>\n'
        "      </div>\n"
        "      <div class=\"grid\">\n"
        f'        <div class="card"><div class="metric-label">Commit count</div><div class="metric-value">{commit_count}</div></div>\n'
        f'        <div class="card"><div class="metric-label">Contributors</div><div class="metric-value">{contributors_count}</div></div>\n'
        f'        <div class="card"><div class="metric-label">Additions / deletions</div><div class="metric-value">{additions} / {deletions}</div></div>\n'
        f'        <div class="card"><div class="metric-label">File hotspots</div><div class="metric-value">{len(result.hotspots)}</div></div>\n'
        "      </div>\n"
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>Project Overview</h2>\n"
        "      <div class=\"two-col\">\n"
        f'        <div class="card summary">{html_lib.escape(result.summary)}</div>\n'
        "        <div class=\"stack\">\n"
        "          <div class=\"card\">\n"
        "            <div class=\"metric-label\">Category distribution</div>\n"
        f"            {category_bars_html}\n"
        "          </div>\n"
        "          <div class=\"card\">\n"
        "            <div class=\"metric-label\">Impact score</div>\n"
        f'            <div class="metric-value">{result.impact_score}/10</div>\n'
        "            <div class=\"muted\">Explainable heuristics only, not a formal risk rating.</div>\n"
        "          </div>\n"
        "        </div>\n"
        "      </div>\n"
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>What Changed</h2>\n"
        f'      <div class="card list-card">{what_changed_html}</div>\n'
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>Why It Matters</h2>\n"
        f'      <div class="card list-card">{why_it_matters_html}</div>\n'
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>Impact Analysis</h2>\n"
        f'      <div class="card list-card">{impact_html}</div>\n'
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>Timeline</h2>\n"
        f'      <div class="card">{timeline_html}</div>\n'
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>File Hotspots</h2>\n"
        "      <div class=\"card\">\n"
        "        <table>\n"
        "          <thead><tr><th>File</th><th>Touches</th></tr></thead>\n"
        f"          <tbody>{hotspots_html}</tbody>\n"
        "        </table>\n"
        "      </div>\n"
        "    </div>\n"
        "    <div class=\"section\">\n"
        "      <h2>Contributor Activity</h2>\n"
        "      <div class=\"card\">\n"
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
        return "<tr><td colspan=\"2\">No hotspots available</td></tr>"
    ordered = sorted(hotspots.items(), key=lambda item: (-item[1], item[0].lower()))
    return "".join(f"<tr><td>{html_lib.escape(path)}</td><td>{count}</td></tr>" for path, count in ordered)


def build_contributor_rows(commits: list[Commit]) -> str:
    if not commits:
        return "<tr><td colspan=\"2\">No contributors recorded</td></tr>"
    counts = Counter(commit.author for commit in commits if commit.author)
    if not counts:
        return "<tr><td colspan=\"2\">No contributors recorded</td></tr>"
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
    return "".join(f"<tr><td>{html_lib.escape(name)}</td><td>{count}</td></tr>" for name, count in ordered)


def build_timeline_rows(commits: list[Commit]) -> str:
    if not commits:
        return '<div class="muted">No commits available for the selected range.</div>'

    chunks: list[str] = []
    for commit in commits:
        category = commit.message.split(":", 1)[0].strip() if ":" in commit.message else "Commit"
        chunks.append(
            "<div class=\"timeline-item\">"
            f"<div class=\"timeline-head\"><span class=\"timeline-message\">{html_lib.escape(commit.message)}</span><span class=\"timeline-meta\">{html_lib.escape(commit.date)} · {html_lib.escape(commit.author)}</span></div>"
            f"<div class=\"timeline-meta\">{html_lib.escape(commit.hash[:7])} · {commit.files_changed} files · +{commit.insertions} / -{commit.deletions}</div>"
            f"<div class=\"badge-row\"><span class=\"badge\">{html_lib.escape(category)}</span></div>"
            "</div>"
        )
    return "".join(chunks)


def build_what_changed_rows(commits: list[Commit]) -> str:
    if not commits:
        return '<div class="muted">No commit evidence was available.</div>'

    counter = Counter()
    for commit in commits:
        for change in commit.changes:
            counter[change.path.split("/", 1)[0]] += 1

    if not counter:
        return '<div class="muted">No file evidence was available.</div>'

    return "<ul>" + "".join(f"<li>{html_lib.escape(path)}: {count} touches</li>" for path, count in counter.most_common(8)) + "</ul>"


def build_why_it_matters_rows(reasons: list[str]) -> str:
    if not reasons:
        return '<div class="muted">Insufficient evidence to infer downstream impact.</div>'
    return "<ul>" + "".join(f"<li>{html_lib.escape(reason)}</li>" for reason in reasons) + "</ul>"


def build_impact_rows(impacts: list[str]) -> str:
    if not impacts:
        return '<div class="muted">No clear impacted domains detected.</div>'
    return "<ul>" + "".join(f"<li>{html_lib.escape(item)}</li>" for item in impacts) + "</ul>"


def render_category_bars(categories: dict[str, int]) -> str:
    if not categories:
        return '<div class="muted">No category data available.</div>'

    total = sum(categories.values()) or 1
    ordered = sorted(categories.items(), key=lambda item: (-item[1], item[0].lower()))
    rows = []
    for category, count in ordered:
        width = max(8, round((count / total) * 100))
        rows.append(
            f'<div class="bar"><div class="timeline-meta">{html_lib.escape(category)} · {count}</div><div class="bar-track"><div class="bar-fill" style="width: {width}%"></div></div></div>'
        )
    return '<div class="bars">' + ''.join(rows) + '</div>'