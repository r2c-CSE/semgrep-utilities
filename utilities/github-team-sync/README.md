# GitHub Team Sync for Semgrep

Syncs GitHub organization teams to Semgrep RBAC teams, including members and repositories.

> **Disclaimer:** This is a sample application that demonstrates how to use the Semgrep APIs. It is not officially supported by Semgrep. Use at your own risk.

## What it does

For each team in a GitHub organization, the script will:

- **Create** a matching Semgrep RBAC team if one does not already exist
- **Update** an existing Semgrep team to match the current GitHub team membership and repositories

Members are matched by GitHub login (username). Repositories are matched by full path (e.g., `my-org/my-repo`).

When updating an existing team, the script computes the diff and only adds or removes what has changed — it does not replace the entire team.

GitHub users or repositories not found in Semgrep are skipped with a warning.

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- A Semgrep API token with org-admin access
- A GitHub token with `read:org` scope (see [Creating a GitHub Token](#creating-a-github-token))

## Configuration

The script is configured via environment variables:

| Variable | Required | Description |
|---|---|---|
| `SEMGREP_APP_TOKEN` | Yes | Semgrep API token with org-admin access |
| `GITHUB_TOKEN` | Yes | GitHub token with `read:org` scope |
| `GITHUB_ORG` | Yes* | GitHub organization name |

*Can also be provided with the `--org` flag.

## Creating a GitHub Token

### Option A — Classic Personal Access Token (recommended)

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Select the **`read:org`** scope (under the `admin:org` group)
4. Generate and copy the token

### Option B — Fine-grained Personal Access Token

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Set **Resource owner** to your organization
4. Under **Organization permissions**, set **Members** to **Read-only**
5. Generate and copy the token

> Note: Fine-grained tokens scoped to an org may require approval from an org owner before they become active.

## Usage

```bash
# Install dependencies
pip install requests

# Set environment variables
export SEMGREP_APP_TOKEN=your_semgrep_token
export GITHUB_TOKEN=your_github_token
export GITHUB_ORG=your-github-org

# Preview changes without writing anything to Semgrep
python3 sync_github_teams.py --dry-run

# Apply changes
python3 sync_github_teams.py

# Alternatively, pass the org name as a flag
python3 sync_github_teams.py --org your-github-org --dry-run
```

## Options

| Flag | Description |
|---|---|
| `--org ORG` | GitHub organization name (overrides `GITHUB_ORG` env var) |
| `--dry-run` | Preview changes without writing anything to Semgrep |

## Example output

```
INFO: Fetching Semgrep deployment info...
INFO:   Deployment: my-org (id=1234)
INFO: Fetching Semgrep members...
INFO:   Found 42 Semgrep members
INFO: Fetching Semgrep projects...
INFO:   Found 87 Semgrep projects
INFO: Fetching existing Semgrep teams...
INFO:   Found 3 existing Semgrep teams
INFO: Fetching GitHub teams for org 'my-org'...
INFO:   Found 5 GitHub teams

INFO: Processing GitHub team: backend
INFO:   Creating team 'backend' with 8 users and 12 repos

INFO: Processing GitHub team: frontend
INFO:   Team 'frontend' is already up to date

INFO: Processing GitHub team: security
INFO:   Updating team 'security': +2/-1 users, +1/-0 repos

INFO: Sync complete.
```

## Notes

- Semgrep users are assigned the `TEAM_ROLE_MEMBER` role by default
- The script uses the Semgrep v2 permissions API (`/api/permissions/v2/...`) for all team operations
- GitHub users not found in Semgrep (e.g., users who haven't logged in yet) are skipped with a warning
- Repositories present in GitHub but not yet added to Semgrep are skipped with a warning
- The `--dry-run` flag fetches all data and logs what would change, but makes no API writes
