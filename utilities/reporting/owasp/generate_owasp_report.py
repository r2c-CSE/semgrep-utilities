#!/usr/bin/env python3

"""
generate_owasp_report.py

Create a beautiful OWASP Top 10 HTML report from a Semgrep JSON file.

Usage:
  semgrep ci --json --output report.json
  python generate_owasp_report.py --input report.json --output owasp_report.html
Optional:
  --title "Custom Title"
  --project-name "My Project"
  --fail-on-empty          (exit 2 if no findings were found)
"""

import argparse
import json
import sys
from collections import defaultdict, Counter
from datetime import datetime
import html
from pathlib import Path

# ----------------------------- Helpers -----------------------------

def escape(s):
    return html.escape(str(s)) if s is not None else ""

def get_meta(item, key, default=None):
    return item.get("extra", {}).get("metadata", {}).get(key, default)

def get_rule_url(item):
    meta = item.get("extra", {}).get("metadata", {})
    short = meta.get("shortlink")
    if short:
        return short
    src = meta.get("source")
    if isinstance(src, str):
        return src
    return None

def extract_owasp_tags(item):
    """
    Return list of tuples (code, year, name) from metadata.owasp
    Example tag formats handled:
      "A02:2021 - Cryptographic Failures"
      "A03:2017 - Injection"
      "A01 - Broken Access Control" (no year)
      "A01" (code only)
    """
    owasp_meta = get_meta(item, "owasp", [])
    if not owasp_meta:
        return []
    tags = []
    for t in owasp_meta:
        t = str(t)
        if " - " in t:
            code_part, name = t.split(" - ", 1)
            code_part = code_part.strip()
            name = name.strip()
            if ":" in code_part:
                code, year = code_part.split(":", 1)
                tags.append((code.strip(), year.strip(), name))
            else:
                tags.append((code_part.strip(), "", name))
        else:
            # "A01:2021" or "A01"
            if ":" in t:
                code, year = t.split(":", 1)
                tags.append((code.strip(), year.strip(), ""))
            else:
                tags.append((t.strip(), "", ""))
    return tags

def first_owasp_2021(item):
    """Prefer a mapping to OWASP 2021 if present; otherwise return the first mapping, else None."""
    tags = extract_owasp_tags(item)
    for code, year, name in tags:
        if str(year).startswith("2021"):
            return (code, year, name)
    return tags[0] if tags else None

def severity_color(sev):
    return {
        "CRITICAL": "#dc2626",
        "ERROR": "#ef4444",
        "WARNING": "#f59e0b",
        "INFO": "#0ea5e9",
        "LOW": "#22c55e",
        "MEDIUM": "#f59e0b",
        "HIGH": "#ef4444",
    }.get((sev or "").upper(), "#6b7280")

def sort_key_for_section(k):
    # Sort A01..A10 first in numeric order; "Unmapped..." last
    if k.startswith("A") and ":" not in k and k != "Unmapped to OWASP Top 10":
        try:
            num = int(k[1:3])
            return (0, num, k)
        except Exception:
            pass
    return (1, 99, k)

# ----------------------------- Core -----------------------------

def load_semgrep_results(json_data):
    """
    Return (results, project_name) from a Semgrep JSON object.
    Tries common locations for fields used by CLI and platform exports.
    """
    results = json_data.get("results")
    if results is None and "findings" in json_data:
        # Some exports might use "findings"
        results = json_data["findings"]
    if results is None:
        results = []

    project_name = (
        json_data.get("project_name")
        or json_data.get("repository")
        or json_data.get("repo")
        or json_data.get("scan_name")
        or "Unknown Project"
    )
    return results, project_name

def build_html(results, project_name, title=None):
    by_owasp = defaultdict(list)
    severity_counts = Counter()
    total_findings = 0

    for r in results:
        sev = r.get("extra", {}).get("severity") or r.get("severity") or "INFO"
        severity_counts[sev.upper()] += 1
        total_findings += 1
        owasp_tag = first_owasp_2021(r)
        if owasp_tag:
            code, year, name = owasp_tag
            key = f"{code} {name} ({year})" if name else f"{code} ({year})"
        else:
            key = "Unmapped to OWASP Top 10"
        by_owasp[key].append(r)

    sorted_sections = sorted(by_owasp.keys(), key=sort_key_for_section)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page_title = title or "OWASP Top 10 Security Report (from Semgrep)"

    # ----- HEAD -----
    head_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(page_title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {{
    --bg: #0b1220;
    --panel: #0f172a;
    --muted: #94a3b8;
    --text: #e2e8f0;
    --accent: #38bdf8;
    --border: #1f2937;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
    color: var(--text);
    background: radial-gradient(1200px 700px at 20% -10%, #1e293b 0%, transparent 60%), radial-gradient(800px 400px at 120% 10%, #0ea5e9 0%, transparent 60%), linear-gradient(180deg, #020617 0%, #0b1220 100%);
  }}
  .container {{ max-width: 1200px; margin: 40px auto; padding: 0 20px; }}
  .card {{
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(6px);
    box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 10px 30px rgba(2, 6, 23, 0.6);
  }}
  h1 {{ font-size: 28px; margin: 0 0 8px; letter-spacing: -0.02em; }}
  h2 {{ font-size: 22px; margin-top: 30px; letter-spacing: -0.01em; }}
  .subtle {{ color: var(--muted); }}
  .grid {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }}
  .col-8 {{ grid-column: span 8; }}
  .col-4 {{ grid-column: span 4; }}
  .badge {{ display:inline-flex; gap:8px; align-items:center; padding:6px 10px; border-radius:999px; border:1px solid var(--border); background:#0b1424; color:#93c5fd; font-weight:600; }}
  .summary {{ display:flex; flex-wrap:wrap; gap:10px; margin-top: 8px; }}
  .table {{ width:100%; border-collapse: collapse; margin-top: 10px; }}
  .table th, .table td {{ padding: 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
  .table th {{ color: #93c5fd; font-weight: 700; }}
  .chip {{ display:inline-block; padding:3px 8px; border-radius: 999px; border:1px solid var(--border); background:#0b1424; color:#e2e8f0; font-size: 12px; }}
  a {{ color: #7dd3fc; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .owasp-header {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
  .count-pill {{ font-weight:700; color:#cbd5e1; background:#0b1424; border:1px solid var(--border); padding:4px 10px; border-radius: 999px; }}
  .footer {{ text-align:center; margin: 28px 0; color: var(--muted); font-size: 12px; }}
</style>
</head>
<body>
  <div class="container">
"""

    # ----- SUMMARY (top card) -----
    summary_card_top = f"""
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;">
        <div>
          <h1>OWASP Top 10 Security Report</h1>
          <div class="subtle">Project: <strong>{escape(project_name)}</strong> • Generated: {escape(now)}</div>
        </div>
        <div class="badge">Total findings: {total_findings}</div>
      </div>
      <div class="grid" style="margin-top: 16px;">
        <div class="col-8 card">
          <h2 style="margin-top:0;">Severity breakdown</h2>
          <div class="summary">
    """

    for sev, count in sorted(severity_counts.items(), key=lambda x: (-x[1], x[0])):
        color = severity_color(sev)
        summary_card_top += f"""
            <span class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium" style="background: {color}20; color: {color}">
              <span class="w-2 h-2 rounded-full" style="background:{color}"></span>{escape(sev)}: {count}
            </span>
        """

    summary_card_top += """
          </div>
          <canvas id="severityChart" height="140" style="margin-top:14px;"></canvas>
        </div>
        <div class="col-4 card">
          <h2 style="margin-top:0;">OWASP coverage</h2>
          <p class="subtle" style="margin-top:4px;">Number of findings mapped to each OWASP Top 10 category.</p>
          <ul style="list-style:none; padding-left:0; margin:0;">
    """

    # list per OWASP section with counts
    for sec in sorted(sorted_sections, key=lambda s: sort_key_for_section(s)):
        summary_card_top += f'<li style="display:flex;justify-content:space-between;border-bottom:1px dashed var(--border);padding:6px 0;"><span>{escape(sec)}</span><span class="count-pill">{len(by_owasp[sec])}</span></li>'

    summary_card_top += """
          </ul>
        </div>
      </div>
    </div>
    """

    # ----- Detailed sections -----
    sections_html = ""
    for section in sorted_sections:
        section_html = f"""
    <div class="card" style="margin-top:16px;">
      <div class="owasp-header">
        <h2 style="margin:0;">{escape(section)}</h2>
        <span class="count-pill">{len(by_owasp[section])} finding(s)</span>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>Severity</th>
            <th>Rule</th>
            <th>Path</th>
            <th>Message</th>
            <th>OWASP / CWE</th>
          </tr>
        </thead>
        <tbody>
        """
        for item in by_owasp[section]:
            sev = (item.get("extra", {}).get("severity") or item.get("severity") or "INFO").upper()
            color = severity_color(sev)
            rule = escape(item.get("check_id", ""))
            rule_url = get_rule_url(item)
            path = escape(item.get("path", ""))
            start_line = escape(item.get("start", {}).get("line", "?"))
            start_col = escape(item.get("start", {}).get("col", "?"))
            message = escape(item.get("extra", {}).get("message", ""))
            owasp_list = get_meta(item, "owasp", []) or []
            cwe_list = get_meta(item, "cwe", []) or []
            owasp_html = ", ".join(escape(x) for x in owasp_list) if owasp_list else '<span class="subtle">—</span>'
            cwe_html = ", ".join(escape(x) for x in cwe_list)

            section_html += f"""
          <tr>
            <td><span class='chip' style='border-color:{color};color:{color}'> {escape(sev)} </span></td>
            <td>
              <div><strong>{rule}</strong></div>
            """
            if rule_url:
                section_html += f'<div><a href="{escape(rule_url)}" target="_blank" rel="noopener">rule reference</a></div>'
            section_html += f"""
            </td>
            <td>
              <div>{path}</div>
              <div class='subtle'>L{start_line}:{start_col}</div>
            </td>
            <td>{message}</td>
            <td>
              {owasp_html}<br/>
              <span class="subtle">{cwe_html}</span>
            </td>
          </tr>
            """
        section_html += """
        </tbody>
      </table>
    </div>
        """
        sections_html += section_html

    # ----- Chart script -----
    severity_labels = list(severity_counts.keys())
    severity_values = [severity_counts[k] for k in severity_labels]
    severity_colors = [severity_color(k) for k in severity_labels]

    import json as pyjson
    script_js = f"""
<script>
const sevData = {{
  labels: {pyjson.dumps(severity_labels)},
  datasets: [{{
    data: {pyjson.dumps(severity_values)},
    backgroundColor: {pyjson.dumps(severity_colors)},
  }}]
}};
const ctx = document.getElementById('severityChart').getContext('2d');
new Chart(ctx, {{
  type: 'doughnut',
  data: sevData,
  options: {{
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ color: '#cbd5e1' }} }}
    }},
    cutout: '60%'
  }}
}});
</script>
"""

    footer_html = """
    <div class="footer">Built from a Semgrep JSON report — OWASP mappings are taken from rule metadata when available.</div>
  </div>
</body>
</html>
"""
    return head_html + summary_card_top + sections_html + script_js + footer_html

def main():
    ap = argparse.ArgumentParser(description="Generate an OWASP Top 10 HTML report from a Semgrep JSON file.")
    ap.add_argument("--input", "-i", type=Path, required=True, help="Path to Semgrep JSON report")
    ap.add_argument("--output", "-o", type=Path, default=Path("owasp_report.html"), help="Path to output HTML file")
    ap.add_argument("--title", type=str, default=None, help="Custom HTML title")
    ap.add_argument("--project-name", type=str, default=None, help="Override project name shown in the header")
    ap.add_argument("--fail-on-empty", action="store_true", help="Exit with code 2 if there are no findings")
    args = ap.parse_args()

    # Load JSON
    try:
        with args.input.open("r", encoding="utf-8") as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error reading input JSON: {e}", file=sys.stderr)
        sys.exit(1)

    results, inferred_project = load_semgrep_results(json_data)
    if args.project_name:
        project_name = args.project_name
    else:
        project_name = inferred_project

    if (not results) and args.fail_on_empty:
        print("No findings present in the report. Exiting due to --fail-on-empty.", file=sys.stderr)
        sys.exit(2)

    html_content = build_html(results, project_name, title=args.title)
    try:
        args.output.write_text(html_content, encoding="utf-8")
    except Exception as e:
        print(f"Error writing output HTML: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Report written to: {args.output}")
    print(f"   Findings: {len(results)} • Project: {project_name}")

if __name__ == "__main__":
    main()
