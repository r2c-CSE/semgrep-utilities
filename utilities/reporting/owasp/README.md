# OWASP API Report

Generates an HTML report of open, high-confidence SAST findings from the Semgrep API, aggregated by OWASP Top 10 category. Findings can be grouped by repository (default) or by Semgrep Team.

## Requirements

```bash
pip install requests
```

## Authentication

Set your Semgrep API token as an environment variable:

```bash
export SEMGREP_APP_TOKEN=<your-token>
```

## Usage

### Group by repository (default)

```bash
python3 owasp_api_report.py
```

### Group by team (all teams)

```bash
python3 owasp_api_report.py --team
```

### Group by team, filter to specific teams

```bash
python3 owasp_api_report.py --team "Backend" "Platform"
```

### Custom output file

```bash
python3 owasp_api_report.py --output my_report.html
```

### All options

```
usage: owasp_api_report.py [-h] [--output OUTPUT] [--team [TEAM ...]]

options:
  --output, -o  Output HTML file (default: owasp_api_report.html)
  --team,   -t  Group by Semgrep Team. Omit names for all teams, or pass
                one or more team names/slugs to filter to specific teams.
```

## Report contents

1. **OWASP Coverage Summary** — total finding count per category, ranked by volume
2. **Findings Matrix** — rows are projects or teams, columns are OWASP categories, with totals
3. **Per-category detail** — each OWASP category ranked by finding count, with a breakdown bar chart showing contribution per project or team

Findings with no OWASP mapping in their rule metadata are grouped under `Unmapped to OWASP Top 10`.

## Filters applied

| Filter | Value |
|--------|-------|
| Status | Open |
| Confidence | High |
| Product | SAST only |
| Projects | Excludes `local_scan/*` |
