# Semgrep Security Reporter (Python Version)

A Python implementation of the Semgrep Security Report Generator that produces PDF security reports from Semgrep findings.

## Features

- **Semgrep API Integration**: Fetches findings with pagination and fallback to dummy data
- **Business Logic**: Security scoring, OWASP Top 10 2021 mapping, and Semgrep Levels (SL1–SL5)
- **Configuration System**: JSON-based configuration with customer branding support
- **Flexible Project Modes**: Individual projects, consolidated org reports, or auto-discovery
- **Demo Mode**: Generates realistic dummy data when no API token is provided

## Quick Start

### Prerequisites

- Python 3.8+
- Semgrep API token (from [Semgrep Settings](https://semgrep.dev/orgs/[your-org]/settings/tokens))

### Installation

```bash
pip install -r requirements.txt
```

### Set your API token

```bash
export SEMGREP_APP_TOKEN=your_token_here
```

Or create a `.env` file in the project root:

```
SEMGREP_APP_TOKEN=your_token_here
```

### Run

```bash
# Use default sample config
python main.py

# Use a custom config file
python main.py config/my-org-config.json
```

Reports are saved to the `output/` directory with a timestamped filename.

## Configuration

Copy and edit the sample config to get started:

```bash
cp config/sample-config.json config/my-org-config.json
```

Key sections of the config file:

| Section | Description |
|---|---|
| `customer` | Organization name, industry, and reporting contact |
| `projects` | List of Semgrep project IDs to include |
| `applicationSettings` | Business criticality, compliance requirements, risk tolerance |
| `reportConfiguration` | PDF sections, severity thresholds, branding |
| `semgrepConfiguration` | Required scan types, rulesets, minimum Semgrep Level |
| `organizationSettings` | Org name and optional API token (prefer env var) |

### Project Modes

The `semgrepProjectId` field supports three modes:

| Value | Behavior |
|---|---|
| A project ID (e.g. `"1234567"`) | Fetch findings for that specific project |
| `"consolidated-org-report"` | Fetch all projects and merge into one report |
| `"auto-discover-all"` | Auto-discover and include all projects in the org |

### Demo Mode

When no API token is provided (via env var or config), the app generates dummy data to demonstrate functionality. Leave `apiToken` empty in the config and omit the env var.

## Project Structure

```
report-generator-python/
├── main.py                        # Entry point
├── requirements.txt
├── config/
│   └── sample-config.json         # Example configuration
├── models/                        # Data models
│   ├── semgrep_finding.py
│   └── report_configuration.py
├── services/                      # Core business logic
│   ├── semgrep_api_client.py      # API calls, pagination, dummy data
│   ├── configuration_manager.py   # Config loading and validation
│   └── scoring_engine.py          # Security scoring and Semgrep Levels
└── pdf/
    └── basic_pdf_generator.py     # PDF report generation
```

## Output

Generated PDF reports include:

1. **Executive Summary**: High-level security assessment overview
2. **Project Summary**: Per-project statistics and security levels
3. **Findings Details**: Vulnerability listings with OWASP mapping and severity breakdown

## Technology Stack

- **ReportLab**: PDF generation
- **Requests**: HTTP client for Semgrep API calls
- **python-dotenv**: `.env` file support
- **Pillow**: Image handling for branding/logos

---

Generated with love by Semgrep Solutions Engineering
