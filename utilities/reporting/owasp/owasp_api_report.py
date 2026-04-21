#!/usr/bin/env python3
"""
owasp_api_report.py

Fetch open, high-confidence SAST findings from the Semgrep API across all
projects and generate an HTML report aggregated by OWASP Top 10 category.

By default findings are grouped by repository. Use --team to group by Semgrep
Team instead, or pass one or more team names to filter to specific teams.

Authentication:
  Set SEMGREP_APP_TOKEN environment variable.

Usage:
  python owasp_api_report.py [--output owasp_api_report.html]
  python owasp_api_report.py --team                         # group by team (all teams)
  python owasp_api_report.py --team "Backend" "Frontend"    # filter to specific teams
"""

import argparse
import html
import os
import sys
from collections import defaultdict
from datetime import datetime

import requests

BASE_URL = "https://semgrep.dev/api/v1"
PERMISSIONS_BASE = "https://semgrep.dev/api/permissions/v2"

OWASP_ORDER = [
    "A01", "A02", "A03", "A04", "A05",
    "A06", "A07", "A08", "A09", "A10",
]

_SCA_FILES = frozenset({
    "package.json", "package-lock.json", "yarn.lock",
    "requirements.txt", "Pipfile", "Pipfile.lock", "poetry.lock",
    "pom.xml", "build.gradle", "build.gradle.kts",
    "Gemfile", "Gemfile.lock",
    "go.mod", "go.sum",
    "Cargo.toml", "Cargo.lock",
    "composer.json", "composer.lock",
    "*.csproj", "packages.config",
    "pyproject.toml", "setup.cfg", "setup.py",
})


def esc(s):
    return html.escape(str(s)) if s is not None else ""


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def make_session(token):
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    s.timeout = 30 * 60
    return s


def get_deployment_info(session):
    """Return (org_slug, deployment_id) from the v1 deployments endpoint."""
    resp = session.get(f"{BASE_URL}/deployments")
    resp.raise_for_status()
    deployments = resp.json().get("deployments", [])
    if not deployments:
        raise RuntimeError("No deployments found for this API token.")
    dep = deployments[0]
    slug = dep["slug"]
    deployment_id = str(dep["id"])
    print(f"Organization: {slug} (id: {deployment_id})", file=sys.stderr)
    return slug, deployment_id


def fetch_findings(session, org_slug):
    """Fetch all open, high-confidence findings across all projects (paginated)."""
    all_findings = []
    page = 0
    print("Fetching findings...", file=sys.stderr)
    while True:
        url = (
            f"{BASE_URL}/deployments/{org_slug}/findings"
            f"?page_size=3000&status=open&confidence=high&page={page}"
        )
        resp = session.get(url)
        if resp.status_code != 200:
            print(
                f"  Error on page {page}: HTTP {resp.status_code} — {resp.text[:200]}",
                file=sys.stderr,
            )
            break
        data = resp.json()
        page_findings = data.get("findings", [])
        all_findings.extend(page_findings)
        print(f"  Page {page}: {len(page_findings)} findings", file=sys.stderr)
        if len(page_findings) < 3000:
            break
        page += 1
    return all_findings


def fetch_project_id_map(session, org_slug):
    """Return {repo_id_str: repo_name} from the v1 projects endpoint."""
    resp = session.get(f"{BASE_URL}/deployments/{org_slug}/projects")
    if resp.status_code != 200:
        print(f"  Warning: could not fetch projects: {resp.status_code}", file=sys.stderr)
        return {}
    projects = resp.json().get("projects", [])
    return {str(p["id"]): p["name"] for p in projects if p.get("id") and p.get("name")}


def fetch_teams(session, deployment_id):
    """Return all teams for the deployment (cursor-paginated)."""
    url = f"{PERMISSIONS_BASE}/deployments/{deployment_id}/teams/list"
    teams = []
    cursor = ""
    print("Fetching teams...", file=sys.stderr)
    while True:
        payload = {"limit": "100", "cursor": cursor}
        resp = session.post(url, json=payload)
        if resp.status_code != 200:
            print(
                f"  Warning: failed to fetch teams: {resp.status_code} — {resp.text[:200]}",
                file=sys.stderr,
            )
            break
        data = resp.json()
        page_teams = data.get("teams", [])
        teams.extend(page_teams)
        cursor = data.get("cursor", "")
        if not cursor or len(page_teams) < 100:
            break
    print(f"  Found {len(teams)} teams", file=sys.stderr)
    return teams


def fetch_team_repo_ids(session, deployment_id, team_id):
    """Return list of repository IDs (as strings) belonging to a team."""
    url = f"{PERMISSIONS_BASE}/deployments/{deployment_id}/teams/{team_id}/repos"
    resp = session.get(url)
    if resp.status_code != 200:
        print(
            f"  Warning: failed to fetch repos for team {team_id}: {resp.status_code}",
            file=sys.stderr,
        )
        return []
    return [str(rid) for rid in resp.json().get("repositoryIds", [])]


def build_repo_to_team_map(session, deployment_id, org_slug, team_filter=None):
    """
    Return {repo_name: team_name} by combining the v2 teams API with the
    v1 projects endpoint (which maps numeric IDs to repo names).

    team_filter: optional set of team names/slugs to include; None = all teams.
    """
    teams = fetch_teams(session, deployment_id)
    if team_filter:
        teams = [
            t for t in teams
            if t.get("name") in team_filter or t.get("slug") in team_filter
        ]
        print(
            f"  Filtered to {len(teams)} team(s): {[t['name'] for t in teams]}",
            file=sys.stderr,
        )

    repo_id_to_name = fetch_project_id_map(session, org_slug)

    repo_to_team = {}
    for team in teams:
        team_name = team.get("name") or f"team-{team.get('id', '?')}"
        team_id = team["id"]
        repo_ids = fetch_team_repo_ids(session, deployment_id, team_id)
        mapped = sum(1 for rid in repo_ids if rid in repo_id_to_name)
        for rid in repo_ids:
            repo_name = repo_id_to_name.get(rid)
            if repo_name:
                repo_to_team[repo_name] = team_name
        print(
            f"  Team '{team_name}': {len(repo_ids)} repo IDs, {mapped} mapped to names",
            file=sys.stderr,
        )

    return repo_to_team


# ---------------------------------------------------------------------------
# SAST detection
# ---------------------------------------------------------------------------

def is_sast(finding):
    """Return True when a finding comes from a SAST scan (not SCA / Secrets)."""
    for field in ("product_type", "product", "sourced_from_type"):
        product = (finding.get(field) or "").lower()
        if product:
            return product in ("sast", "code")

    file_path = finding.get("location", {}).get("file_path", "")
    base = file_path.split("/")[-1] if file_path else ""
    if base in _SCA_FILES:
        return False

    return finding.get("location", {}).get("line") is not None


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def extract_owasp_names(finding):
    names = (finding.get("rule") or {}).get("owasp_names") or []
    return [str(n).strip() for n in names if n]


def owasp_sort_key(name):
    for i, code in enumerate(OWASP_ORDER):
        if name.startswith(code):
            return (0, i, name)
    return (1, 99, name)


def aggregate(findings, repo_to_team=None):
    """
    Aggregate findings by OWASP category.

    When repo_to_team is provided, group by team name instead of repo name.
    Repos with no team assignment are grouped under 'Unassigned'.

    Returns:
        owasp_data  – {owasp_name: {group: count}}
        group_data  – {group: {owasp_name: count}}
        sast_count  – int
    """
    owasp_data = defaultdict(lambda: defaultdict(int))
    group_data = defaultdict(lambda: defaultdict(int))
    sast_count = 0

    for f in findings:
        if not is_sast(f):
            continue

        repo_name = (
            (f.get("repository") or {}).get("name")
            or f.get("project_name")
            or "Unknown"
        )
        if repo_name.startswith("local_scan/"):
            continue

        sast_count += 1

        group = repo_to_team.get(repo_name, "Unassigned") if repo_to_team is not None else repo_name

        names = extract_owasp_names(f) or ["Unmapped to OWASP Top 10"]

        seen = set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            owasp_data[name][group] += 1
            group_data[group][name] += 1

    return owasp_data, group_data, sast_count


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_BAR_PALETTE = [
    "#38bdf8", "#818cf8", "#34d399", "#f472b6",
    "#fb923c", "#a78bfa", "#60a5fa", "#4ade80",
    "#facc15", "#f87171",
]


def _css():
    return """
<style>
  :root {
    --bg: #0b1220; --panel: #0f172a; --muted: #94a3b8;
    --text: #e2e8f0; --accent: #38bdf8; --border: #1f2937;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    color: var(--text);
    background: radial-gradient(1200px 700px at 20% -10%, #1e293b 0%, transparent 60%),
                radial-gradient(800px 400px at 120% 10%, #0ea5e9 0%, transparent 60%),
                linear-gradient(180deg, #020617 0%, #0b1220 100%);
    min-height: 100vh;
  }
  .container { max-width: 1200px; margin: 40px auto; padding: 0 24px; }
  .card {
    background: linear-gradient(180deg,rgba(255,255,255,.025),rgba(255,255,255,.01));
    border: 1px solid var(--border); border-radius: 16px; padding: 24px;
    box-shadow: 0 1px 0 rgba(255,255,255,.05) inset, 0 10px 30px rgba(2,6,23,.6);
    margin-bottom: 16px;
  }
  h1 { font-size: 28px; margin: 0 0 6px; letter-spacing: -.02em; }
  h2 { font-size: 20px; margin: 0 0 14px; letter-spacing: -.01em; }
  .subtle { color: var(--muted); font-size: 14px; }
  .badge {
    display: inline-flex; align-items: center; padding: 6px 14px;
    border-radius: 999px; border: 1px solid var(--border);
    background: #0b1424; color: #93c5fd; font-weight: 700;
  }
  .pill {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    border: 1px solid var(--border); background: #0b1424; color: #cbd5e1;
    font-size: 13px; font-weight: 600; white-space: nowrap;
  }
  .team-pill {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    border: 1px solid #334155; background: #1e293b; color: #7dd3fc;
    font-size: 13px; font-weight: 600; white-space: nowrap;
  }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; }
  th { color: #93c5fd; font-weight: 700; white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  .rank { color: var(--muted); font-size: 13px; margin-right: 6px; }
  .owasp-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .group-row { display: flex; align-items: center; gap: 10px; padding: 6px 0;
               border-bottom: 1px dashed var(--border); }
  .group-row:last-child { border-bottom: none; }
  .bar-bg { flex: 1; background: var(--border); border-radius: 4px; height: 8px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; }
  .group-name { min-width: 200px; max-width: 300px; font-size: 13px; overflow: hidden;
                text-overflow: ellipsis; white-space: nowrap; color: #e2e8f0; }
  .matrix th.rotate { width: 40px; vertical-align: bottom; white-space: nowrap; }
  .matrix th.rotate span {
    writing-mode: vertical-rl; transform: rotate(180deg);
    display: inline-block; max-height: 140px; font-size: 11px; font-weight: 600;
  }
  .matrix td { text-align: center; font-size: 13px; padding: 8px 6px; }
  .matrix td.row-label { text-align: left; font-size: 13px; max-width: 200px;
                          overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .matrix td.total { font-weight: 700; color: #38bdf8; }
  .cell-0 { color: var(--muted); }
  .footer { text-align: center; margin: 32px 0 0; color: var(--muted); font-size: 12px; }
  a { color: #7dd3fc; text-decoration: none; }
  a:hover { text-decoration: underline; }
</style>
"""


def _summary_card(sorted_owasp, total_by_owasp, org_slug, total_sast, now, team_context):
    total = sum(total_by_owasp.values())
    rows = ""
    for name in sorted_owasp[:10]:
        rows += (
            f'<tr><td>{esc(name)}</td>'
            f'<td style="text-align:right"><span class="pill">{total_by_owasp[name]}</span></td></tr>'
        )

    context_parts = [f"Organization: <strong>{esc(org_slug)}</strong>"]
    if team_context:
        context_parts.append(f"Teams: <strong>{esc(team_context)}</strong>")
    context_parts.append("Filter: open · high-confidence · SAST")
    context_parts.append(f"Generated: {esc(now)}")

    return f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;">
    <div>
      <h1>OWASP Top 10 Findings Report</h1>
      <div class="subtle">{" &nbsp;•&nbsp; ".join(context_parts)}</div>
    </div>
    <span class="badge">{total} findings across {len(total_by_owasp)} OWASP categories</span>
  </div>
  <div style="margin-top:20px;">
    <h2>OWASP Coverage Summary</h2>
    <table>
      <thead><tr><th>OWASP Category</th><th style="text-align:right">Findings</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
"""


def _matrix_table(all_groups, all_owasp_sorted, group_data, total_by_owasp, row_label):
    if not all_groups or not all_owasp_sorted:
        return ""

    header_cells = ""
    for name in all_owasp_sorted:
        code = name.split(" ")[0] if " " in name else name[:6]
        header_cells += f'<th class="rotate"><span title="{esc(name)}">{esc(code)}</span></th>'

    rows = ""
    for group in sorted(all_groups):
        group_total = sum(group_data[group].values())
        cells = ""
        for name in all_owasp_sorted:
            count = group_data[group].get(name, 0)
            cls = "cell-0" if count == 0 else ""
            cells += f'<td class="{cls}">{count if count else "—"}</td>'
        rows += (
            f'<tr><td class="row-label" title="{esc(group)}">{esc(group)}</td>'
            f'{cells}'
            f'<td class="total">{group_total}</td></tr>'
        )

    total_cells = ""
    for name in all_owasp_sorted:
        total_cells += f'<td style="font-weight:700;color:#38bdf8">{total_by_owasp.get(name, 0)}</td>'
    grand_total = sum(total_by_owasp.values())
    rows += (
        f'<tr style="border-top:2px solid #38bdf8">'
        f'<td class="row-label" style="font-weight:700;color:#38bdf8">TOTAL</td>'
        f'{total_cells}'
        f'<td class="total">{grand_total}</td></tr>'
    )

    return f"""
<div class="card" style="overflow-x:auto">
  <h2>{esc(row_label)} Findings by OWASP Category</h2>
  <table class="matrix">
    <thead>
      <tr>
        <th>{esc(row_label)}</th>
        {header_cells}
        <th>Total</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""


def _ranked_sections(sorted_owasp, owasp_data, total_by_owasp, row_label):
    sections = ""
    max_total = total_by_owasp[sorted_owasp[0]] if sorted_owasp else 1
    pill_class = "team-pill" if row_label == "Team" else "pill"

    for rank, name in enumerate(sorted_owasp, start=1):
        group_counts = owasp_data[name]
        total = total_by_owasp[name]
        color = _BAR_PALETTE[(rank - 1) % len(_BAR_PALETTE)]

        group_rows = ""
        for group, count in sorted(group_counts.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total else 0
            group_rows += f"""
      <div class="group-row">
        <span class="group-name" title="{esc(group)}">{esc(group)}</span>
        <div class="bar-bg">
          <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
        </div>
        <span class="{pill_class}">{count}</span>
      </div>"""

        header_pct = (total / max_total * 100) if max_total else 0
        sections += f"""
<div class="card">
  <div class="owasp-title">
    <span class="rank">#{rank}</span>
    <h2 style="margin:0;flex:1">{esc(name)}</h2>
    <span class="pill" style="font-size:15px">{total} finding{"s" if total != 1 else ""}</span>
  </div>
  <div class="bar-bg" style="margin:12px 0 16px;height:6px">
    <div class="bar-fill" style="width:{header_pct:.1f}%;background:{color}"></div>
  </div>
  {group_rows}
</div>
"""
    return sections


def build_html(owasp_data, group_data, total_by_owasp, total_sast, org_slug,
               row_label="Project", team_context=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    sorted_owasp = sorted(
        total_by_owasp,
        key=lambda n: (-total_by_owasp[n], owasp_sort_key(n)),
    )
    all_owasp_sorted = sorted(total_by_owasp, key=owasp_sort_key)
    all_groups = list(group_data.keys())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OWASP API Report — {esc(org_slug)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
{_css()}
</head>
<body>
<div class="container">
{_summary_card(sorted_owasp, total_by_owasp, org_slug, total_sast, now, team_context)}
{_matrix_table(all_groups, all_owasp_sorted, group_data, total_by_owasp, row_label)}
{_ranked_sections(sorted_owasp, owasp_data, total_by_owasp, row_label)}
<div class="footer">
  Semgrep API · open · high-confidence · SAST findings ·
  {total_sast} total findings · {esc(now)}
</div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Generate an OWASP Top 10 report from the Semgrep findings API."
    )
    ap.add_argument(
        "--output", "-o",
        default="owasp_api_report.html",
        help="Output HTML file (default: owasp_api_report.html)",
    )
    ap.add_argument(
        "--team", "-t",
        nargs="*",
        metavar="TEAM",
        help=(
            "Group findings by Semgrep Team. "
            "Omit team names to include all teams, or pass one or more "
            "team names/slugs to filter to specific teams."
        ),
    )
    args = ap.parse_args()

    token = os.environ.get("SEMGREP_APP_TOKEN")
    if not token:
        print("Error: SEMGREP_APP_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    session = make_session(token)

    try:
        org_slug, deployment_id = get_deployment_info(session)
    except Exception as e:
        print(f"Error fetching organization: {e}", file=sys.stderr)
        sys.exit(1)

    raw_findings = fetch_findings(session, org_slug)
    print(f"Total findings fetched: {len(raw_findings)}", file=sys.stderr)

    repo_to_team = None
    row_label = "Project"
    team_context = ""

    if args.team is not None:
        team_filter = set(args.team) if args.team else None
        try:
            repo_to_team = build_repo_to_team_map(
                session, deployment_id, org_slug, team_filter=team_filter,
            )
        except Exception as e:
            print(
                f"Warning: could not fetch teams ({e}). Falling back to project grouping.",
                file=sys.stderr,
            )
            repo_to_team = None

        if repo_to_team is not None:
            row_label = "Team"
            team_context = ", ".join(sorted(args.team)) if args.team else "all teams"

    owasp_data, group_data, sast_count = aggregate(raw_findings, repo_to_team=repo_to_team)
    print(f"SAST findings after filter: {sast_count}", file=sys.stderr)
    print(f"OWASP categories found: {len(owasp_data)}", file=sys.stderr)
    print(f"{row_label}s with findings: {len(group_data)}", file=sys.stderr)

    if sast_count == 0:
        print("No SAST findings matched the filters. The report will be empty.", file=sys.stderr)

    total_by_owasp = {
        name: sum(groups.values())
        for name, groups in owasp_data.items()
    }

    page = build_html(
        owasp_data, group_data, total_by_owasp, sast_count, org_slug,
        row_label=row_label,
        team_context=team_context,
    )

    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(page)
    except OSError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nReport written to: {args.output}", file=sys.stderr)
    print(f"  {sast_count} findings · {len(owasp_data)} categories · {len(group_data)} {row_label.lower()}s")


if __name__ == "__main__":
    main()
