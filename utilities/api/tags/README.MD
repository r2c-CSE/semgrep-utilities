# Semgrep Team Repository Tagger

A Python script that automatically tags Semgrep projects (repositories) with the names of the teams they belong to.

The script retrieves the deployment automatically, reads all teams and their repositories, builds a repository-to-team mapping, and adds the corresponding team names as repository tags.

## Features

- Automatically retrieves the Semgrep deployment ID.
- Retrieves all teams using cursor-based pagination.
- Retrieves all repositories assigned to each team.
- Supports repositories belonging to multiple teams.
- Adds all relevant team names to a repository in a single PATCH request.
- Skips the default project team.
- Skips teams whose names start with `[old]`.
- Recursively skips all subteams of teams whose names start with `[old]`.
- Supports team names or team slugs as tags.
- Dry-run mode by default.
- Retries temporary API failures and rate-limit responses.

## Requirements

- Python 3.9+
- A Semgrep API token with permission to:
  - Read deployments
  - Read teams
  - Read team repository assignments
  - Update repository tags

Install the required Python package:

```bash
pip install requests
```

## Authentication

The script reads the Semgrep API token from the `SEMGREP_APP_TOKEN` environment variable.

```bash
export SEMGREP_APP_TOKEN="your-semgrep-token"
```

Do not hard-code the token in the script or commit it to source control.

## Usage

### Dry run

Dry run is the default mode. No repositories are modified.

```bash
python3 semgrep_team_tags.py
```

Example output:

```text
Retrieving deployment...

======================================
 Semgrep Team -> Repository Tag Sync
======================================

Deployment: My Company Name (1605)
Tag source: name
Mode: DRY RUN

Retrieving teams...
Retrieved 100 teams
Retrieved 23 teams

Found 123 teams before filtering.

Skipping default team: Default
Skipping old team hierarchy: [old] Legacy
Skipping subteam of [old] hierarchy: Legacy Backend
Skipping subteam of [old] hierarchy: Legacy Frontend

119 teams remain after filtering.
4 teams excluded.

[1/119] Reading repositories for team 'Platform' (1234)...
    Found 25 repositories

...

Repository -> tags
------------------
1111: Platform
2222: Backend, Platform
3333: Security

DRY RUN - no repositories were modified.
```

### Apply changes

After reviewing the dry-run output, run:

```bash
python3 semgrep_team_tags.py --apply
```

This sends the PATCH requests that add the team tags to each repository.

## Tag source

By default, the script uses the team's `name` as the repository tag.

For example:

```text
Platform Engineering
Security
Payments
```

To use team slugs instead:

```bash
python3 semgrep_team_tags.py --tag-field slug
```

To apply slug-based tags:

```bash
python3 semgrep_team_tags.py --tag-field slug --apply
```

## Team filtering

The script intentionally ignores some teams.

### Default team

Any team where:

```json
"isProjectDefault": true
```

is excluded.

Only the default team itself is excluded. Its child teams are still processed unless another exclusion rule applies to them.

### Old teams

Any team whose name starts with:

```text
[old]
```

is excluded.

The comparison is case-insensitive, so these are all considered old teams:

```text
[old] Legacy
[OLD] Legacy
[Old] Legacy
```

All descendants of an old team are also excluded recursively.

For example:

```text
Engineering
├── Backend
├── Frontend
└── [old] Legacy
    ├── Legacy Java
    └── Legacy PHP

Platform
```

The script processes:

```text
Engineering
Backend
Frontend
Platform
```

and ignores:

```text
[old] Legacy
Legacy Java
Legacy PHP
```

## Repository membership

A repository may belong to more than one team.

For example:

```text
repo-1 -> Platform
repo-2 -> Platform, Security
repo-3 -> Payments
```

The script first builds the complete repository-to-team mapping and then performs at most one tagging PATCH request per repository.

For `repo-2`, the tag update would contain:

```json
{
  "tagsChanges": [
    {
      "operation": "ADD_TAGS",
      "tags": [
        "Platform",
        "Security"
      ]
    }
  ]
}
```

## API flow

The script uses the following Semgrep API endpoints.

### 1. Retrieve deployment

```http
GET /api/v2/deployments
```

The deployment ID is discovered automatically from the API token.

If the token has access to no deployments, the script stops.

If the token has access to more than one deployment, the script also stops rather than selecting one automatically.

### 2. Retrieve teams

```http
POST /api/permissions/v2/deployments/{deploymentId}/teams/list
```

Pagination is handled using the returned cursor.

### 3. Retrieve repositories assigned to a team

```http
GET /api/permissions/v2/deployments/{deploymentId}/teams/{teamId}/repos
```

Pagination is also handled for repository membership.

### 4. Add repository tags

```http
PATCH /api/agent/deployments/{deploymentId}/repos/{repositoryId}
```

The request contains only the tag changes required by this script:

```json
{
  "deploymentId": 1605,
  "idOrName": 12345,
  "tagsChanges": [
    {
      "operation": "ADD_TAGS",
      "tags": [
        "Platform",
        "Security"
      ]
    }
  ]
}
```

## Important behavior

The script currently **adds tags only**.

It does not remove tags when a repository is removed from a team.

For example, if a repository previously belonged to:

```text
Payments
```

and later belongs only to:

```text
Platform
```

running the script will add `Platform`, but it will not automatically remove `Payments`.

This behavior is intentional because existing repository tags may have been created manually, and the script cannot safely determine which tags it owns.

If bidirectional synchronization is needed in the future, consider using namespaced tags such as:

```text
team:Payments
team:Platform
team:Security
```

The script could then safely distinguish automatically managed team tags from other repository tags.

## Error handling

The script retries requests for temporary failures including:

- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504

If an individual repository PATCH fails during apply mode, the script reports the error and continues processing the remaining repositories.

At the end it prints the number of successful and failed updates.

## Recommended workflow

1. Export `SEMGREP_APP_TOKEN`.
2. Run the script in dry-run mode.
3. Review the teams that were excluded.
4. Review the repository-to-team tag mapping.
5. Run again with `--apply`.
6. Review the success/failure summary.

Example:

```bash
export SEMGREP_APP_TOKEN="..."

python3 semgrep_team_tags.py

python3 semgrep_team_tags.py --apply
```

## Security

- Never commit `SEMGREP_APP_TOKEN`.
- Prefer storing the token in your CI/CD platform's secret manager.
- Run the script with the minimum Semgrep permissions required.
- Always use dry-run mode before applying changes in a new deployment.
