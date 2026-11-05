# Semgrep Bulk Triage

A Python script that bulk-triages Semgrep findings listed in a CSV file, using the [Bulk Triage API](https://docs.semgrep.dev/api-reference/v1/triageservice/bulk-triage).

Use it to set a triage state and/or add a note on a large, explicit list of findings, for example to reopen issues that were incorrectly ignored.

## Features

- Reads issue IDs (and optionally issue types) from a CSV file.
- Supports SAST, SCA, and Secrets findings in the same CSV.
- Sends up to 3000 issues per request (configurable with `--limit`).
- Skips queued issues that Semgrep already triaged as branch siblings of an earlier batch.
- Writes the unprocessed queue to a CSV on failure so the run can be resumed.
- Writes submitted issues the API did not report as triaged to a CSV for review.
- Dry-run mode.
- Retries temporary API failures and rate-limit responses.

## Requirements

- Python 3.9+
- A Semgrep API token with the Web API scope for the deployment

Install the required Python package:

```bash
pip install requests
```

## Authentication

The script reads the Semgrep API token from, in order:

1. The `SEMGREP_APP_TOKEN` environment variable.
2. The `api_token` saved in `~/.semgrep/settings.yml` by `semgrep login`.

```bash
export SEMGREP_APP_TOKEN="your-semgrep-token"
```

The environment variable takes precedence, so set it to use a different token than the one saved by `semgrep login`.

Whichever source is used, the token must have the Web API scope. A token saved by `semgrep login` may not; if requests fail with HTTP 401 or 403, set `SEMGREP_APP_TOKEN` to a token with Web API scope.

Do not hard-code the token in the script or commit it to source control.

## Input CSV

The CSV must have an `issue_id` column. An optional `issue_type` column (`sast`, `sca`, or `secrets`) overrides `--issue-type` for that row.

```csv
issue_id,issue_type
12345,sast
12346,
67890,sca
```

- Blank `issue_type` values use `--issue-type` (default `sast`).
- Duplicate rows are ignored.
- Issues are submitted in CSV order, grouped by issue type.

Issue ID files should not be committed alongside the script.

## Usage

### Dry run

Dry run shows how many requests would be sent. No findings are modified and no token is required.

```bash
python3 bulk_triage.py --deployment-slug my-org --csv issues.csv --state reopened --dry-run
```

Because sibling removal depends on API responses, the real run may need fewer requests than the dry run reports.

### Triage

```bash
python3 bulk_triage.py \
  --deployment-slug my-org \
  --csv issues.csv \
  --state reopened \
  --note "Reopen incorrectly ignored issues"
```

Ignore findings with a reason:

```bash
python3 bulk_triage.py --deployment-slug my-org --csv issues.csv --state ignored --reason false_positive
```

Add a note without changing the triage state:

```bash
python3 bulk_triage.py --deployment-slug my-org --csv issues.csv --note "Reviewed in Q3 audit"
```

### Options

| Option | Description |
|--------|-------------|
| `--deployment-slug` | Deployment **slug** (e.g. `my-org`), not the numeric deployment ID (required). Shown in Semgrep under Settings, or as `slug` in `GET /api/v1/deployments`. |
| `--csv` | Input CSV (required). |
| `--state` | `ignored`, `reviewing`, `fixing`, `reopened`, or `provisionally_ignored`. |
| `--note` | Note to attach, max 3000 characters. At least one of `--state` or `--note` is required. |
| `--reason` | `acceptable_risk`, `false_positive`, `no_time`, `no_triage_reason`, or `duplicate`. Only valid with `--state ignored`. |
| `--issue-type` | Issue type for rows without one. Default `sast`. |
| `--limit` | Issues per request, 1–3000. Default 3000. |
| `--delay` | Seconds between requests. Default 1. |
| `--remaining-csv` | Where to write the unprocessed queue on failure. Default `bulk_triage_remaining.csv`. |
| `--not-triaged-csv` | Where to write submitted issues not reported as triaged. Default `bulk_triage_not_triaged.csv`. |
| `--dry-run` | Print planned requests without sending them. |

## Branch siblings

When Semgrep triages a finding, it also triages findings with the same fingerprint on other branches. The response's `triaged_issues` list can therefore contain more IDs than were submitted, and more than `--limit`.

After each request, the script reports every additional sibling that was triaged, and removes any that are still waiting in its queue so they are not submitted again. The next batch is filled from the remaining queue.

For example, with `--limit 2` and a CSV of `1, 2, 3, 4, 5, 6`, if triaging `1` also triages sibling `4` (in the CSV) and sibling `99` (not in the CSV):

```text
[1] sast: submitting 2 issue(s) -> 4 triaged; 2 additional sibling(s) triaged (1 removed from queue); ...   # issues 1, 2 (+4, +99)
[2] sast: submitting 2 issue(s) -> ...                                                                       # issues 3, 5
[3] sast: submitting 1 issue(s) -> ...                                                                       # issue 6
```

Note:

- Siblings are only matched within the same issue type.
- Siblings that are not in the CSV are still triaged by Semgrep. The script cannot prevent this; the triage scope of a run may be larger than the CSV.

## Output files

### Not triaged

Submitted issues that are missing from the API's `triaged_issues` response are written to `--not-triaged-csv` at the end of the run. They are not retried. Review them before rerunning; possible causes include a wrong deployment or issue type.

### Remaining (resume)

If a request fails, the script stops and writes every issue still in the queue (excluding siblings already triaged) to `--remaining-csv`. Resume with:

```bash
python3 bulk_triage.py --deployment-slug my-org --csv bulk_triage_remaining.csv --state reopened
```

## Error handling

The script retries requests for temporary failures including:

- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504

Any other non-200 response, or a request that still fails after retries, stops the run and writes the remaining queue.

## Testing

Unit tests use the standard library and mock the API; they do not contact Semgrep.

```bash
python3 -m unittest test_bulk_triage
```

## Recommended workflow

1. Export `SEMGREP_APP_TOKEN`, or run `semgrep login`.
2. Run with `--dry-run` to check the CSV parses and the request count.
3. Run against a small CSV with `--limit 1` and review the output and the findings in Semgrep.
4. Run the full CSV.
5. Review `bulk_triage_not_triaged.csv`, if written.

## Security

- Never commit `SEMGREP_APP_TOKEN`.
- Do not commit issue ID CSVs (input or output) alongside the script.
