from __future__ import annotations

import html as html_lib

from .models import AnalysisResult


def generate_html_report(result: AnalysisResult) -> str:
    """Generate a standalone HTML dashboard report using inline CSS only."""
    categories_html = build_category_rows(result.categories)
    hotspots_html = build_hotspot_rows(result.hotspots)
    contributors_html = build_contributor_rows(result.contributors)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>GitLens Zero Report</title>
  <style>
    :root {{
      --bg: #0f172a; --panel: #111827; --soft: #1f2937; --text: #e5e7eb; --muted: #9ca3af;
      --accent: #60a5fa; --success: #34d399; --warning: #fbbf24; --danger: #f87171; --border: #334155;
    }}
    body {{ font-family: Arial, sans-serif; margin: 0; background: linear-gradient(135deg, #020817, #0f172a); color: var(--text); }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 60px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }}
    .title {{ font-size: 2rem; font-weight: 700; }}
    .badge {{ background: var(--accent); color: #08111d; padding: 8px 14px; border-radius: 999px; font-weight: bold; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .card {{ background: rgba(17, 24, 39, 0.96); border: 1px solid var(--border); border-radius: 14px; padding: 18px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); }}
    .label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .value {{ font-size: 2rem; font-weight: 700; margin-top: 10px; }}
    .section {{ margin-top: 24px; }}
    .section h2 {{ margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--border); padding: 12px 10px; text-align: left; }}
    th {{ color: var(--muted); }}
    .summary {{ font-size: 1.1rem; line-height: 1.7; color: #dbeafe; }}
    ul {{ padding-left: 18px; }}
    li {{ margin-bottom: 8px; }}
    @media (max-width: 640px) {{ .header {{ flex-direction: column; align-items: flex-start; gap: 12px; }} }}
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <div class=\"title\">GitLens Zero</div>
      <div class=\"badge\">Project Overview</div>
    </div>

    <div class=\"grid\">
      <div class=\"card\"><div class=\"label\">Commit count</div><div class=\"value\">{result.commit_count}</div></div>
      <div class=\"card\"><div class=\"label\">Contributors</div><div class=\"value\">{len(result.contributors)}</div></div>
      <div class=\"card\"><div class=\"label\">Impact score</div><div class=\"value\">{result.impact_score}/10</div></div>
      <div class=\"card\"><div class=\"label\">Hotspots</div><div class=\"value\">{len(result.hotspots)}</div></div>
    </div>

    <div class=\"section\">
      <h2>Executive Summary</h2>
      <div class=\"card summary\">{html_lib.escape(result.summary)}</div>
    </div>

    <div class=\"section\">
      <h2>Contributor Table</h2>
      <div class=\"card\">
        <table>
          <thead><tr><th>Contributor</th></tr></thead>
          <tbody>{contributors_html}</tbody>
        </table>
      </div>
    </div>

    <div class=\"section\">
      <h2>Category Distribution</h2>
      <div class=\"card\">
        <table>
          <thead><tr><th>Category</th><th>Count</th></tr></thead>
          <tbody>{categories_html}</tbody>
        </table>
      </div>
    </div>

    <div class=\"section\">
      <h2>File Hotspots</h2>
      <div class=\"card\">
        <table>
          <thead><tr><th>File</th><th>Touches</th></tr></thead>
          <tbody>{hotspots_html}</tbody>
        </table>
      </div>
    </div>

    <div class=\"section\">
      <h2>Impact Analysis</h2>
      <div class=\"card\">
        <ul>{''.join(f'<li>{html_lib.escape(item)}</li>' for item in result.impacts)}</ul>
      </div>
    </div>
  </div>
</body>
</html>
"""


def build_category_rows(categories: dict[str, int]) -> str:
    """Render category rows for an HTML table."""
    if not categories:
        return "<tr><td colspan=\"2\">No categories available</td></tr>"
    return "".join(f"<tr><td>{html_lib.escape(category)}</td><td>{count}</td></tr>" for category, count in categories.items())


def build_hotspot_rows(hotspots: dict[str, int]) -> str:
    """Render hotspot rows for an HTML table."""
    if not hotspots:
        return "<tr><td colspan=\"2\">No hotspots available</td></tr>"
    return "".join(f"<tr><td>{html_lib.escape(path)}</td><td>{count}</td></tr>" for path, count in hotspots.items())


def build_contributor_rows(contributors: list[str]) -> str:
    """Render contributor rows for an HTML table."""
    if not contributors:
        return "<tr><td>No contributors recorded</td></tr>"
    return "".join(f"<tr><td>{html_lib.escape(name)}</td></tr>" for name in contributors)
