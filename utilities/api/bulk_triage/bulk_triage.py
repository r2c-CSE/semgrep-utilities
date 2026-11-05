#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://semgrep.dev/api/v1/deployments"
MAX_LIMIT = 3000
ISSUE_TYPES = ["sast", "sca", "secrets"]
TRIAGE_STATES = ["ignored", "reviewing", "fixing", "reopened", "provisionally_ignored"]
TRIAGE_REASONS = ["acceptable_risk", "false_positive", "no_time", "no_triage_reason", "duplicate"]
MAX_NOTE_LENGTH = 3000
SEMGREP_SETTINGS_PATH = Path.home() / ".semgrep" / "settings.yml"


def get_token():
    """Return SEMGREP_APP_TOKEN, falling back to the api_token saved by `semgrep login`."""
    token = os.getenv("SEMGREP_APP_TOKEN")
    if token:
        return token

    # Look for the .semgrep/settings.yml where we keep login tokens if no ENV var
    try:
        with open(SEMGREP_SETTINGS_PATH) as semgrep_settings:
            for line in semgrep_settings:
                # the line we want starts with api_token
                if line.startswith("api_token:"):
                    return line.split(":", 1)[1].strip().strip("'\"") or None
    except OSError:
        pass

    return None


def create_session(token: str) -> requests.Session:
    session = requests.Session()

    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    return session


def limit_arg(value: str) -> int:
    limit = int(value)
    if not 1 <= limit <= MAX_LIMIT:
        raise argparse.ArgumentTypeError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def read_issues(csv_path: str, default_issue_type: str) -> dict:
    """Read issue IDs from a CSV and group them by issue type, preserving order.

    The CSV must have an `issue_id` column. An optional `issue_type` column
    overrides the default issue type for that row.
    """
    # dict-as-ordered-set: keeps CSV order and makes removal O(1)
    issues_by_type = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "issue_id" not in reader.fieldnames:
            raise ValueError(f"{csv_path} must have an 'issue_id' column")

        for line_number, row in enumerate(reader, start=2):
            raw_id = (row.get("issue_id") or "").strip()
            if not raw_id:
                continue
            try:
                issue_id = int(raw_id)
            except ValueError:
                raise ValueError(f"{csv_path}:{line_number}: invalid issue_id {raw_id!r}")

            issue_type = (row.get("issue_type") or "").strip() or default_issue_type
            if issue_type not in ISSUE_TYPES:
                raise ValueError(f"{csv_path}:{line_number}: invalid issue_type {issue_type!r}")

            issues_by_type.setdefault(issue_type, {})[issue_id] = None

    return issues_by_type


def write_issues_csv(path: str, issues: list) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["issue_id", "issue_type"])
        for issue_type, issue_id in issues:
            writer.writerow([issue_id, issue_type])


def bulk_triage(session: requests.Session, deployment_slug: str, payload: dict) -> dict:
    url = f"{BASE_URL}/{deployment_slug}/triage"

    response = session.post(url, json=payload, timeout=300)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bulk-triage Semgrep findings listed in a CSV file. "
        "Semgrep also triages findings with the same fingerprint on other branches; "
        "any such sibling that appears later in the CSV is dropped from the queue "
        "instead of being submitted again."
    )
    parser.add_argument(
        "--deployment-slug",
        required=True,
        help="Deployment slug (e.g. 'my-org'), NOT the numeric deployment ID. "
        "Shown in Semgrep under Settings, or as 'slug' in GET /api/v1/deployments",
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="CSV with an 'issue_id' column and an optional 'issue_type' column",
    )
    parser.add_argument("--state", choices=TRIAGE_STATES, help="New triage state")
    parser.add_argument(
        "--issue-type",
        default="sast",
        choices=ISSUE_TYPES,
        help="Issue type for rows without an 'issue_type' value (default: sast)",
    )
    parser.add_argument("--note", help=f"Note to attach (max {MAX_NOTE_LENGTH} characters)")
    parser.add_argument(
        "--reason",
        choices=TRIAGE_REASONS,
        help="Triage reason (only valid with --state ignored)",
    )
    parser.add_argument(
        "--limit",
        type=limit_arg,
        default=MAX_LIMIT,
        help=f"Issues submitted per request, 1-{MAX_LIMIT} (default: {MAX_LIMIT}). "
        "Responses may include more IDs than this because of branch siblings.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between requests (default: 1)",
    )
    parser.add_argument(
        "--remaining-csv",
        default="bulk_triage_remaining.csv",
        help="Where to write unprocessed issues if a request fails "
        "(default: bulk_triage_remaining.csv)",
    )
    parser.add_argument(
        "--not-triaged-csv",
        default="bulk_triage_not_triaged.csv",
        help="Where to write submitted issues the API did not report as triaged "
        "(default: bulk_triage_not_triaged.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned requests without sending them. "
        "Sibling removal can't be predicted, so the real run may need fewer requests.",
    )
    args = parser.parse_args()

    if not args.state and not args.note:
        parser.error("at least one of --state or --note is required")
    if args.reason and args.state != "ignored":
        parser.error("--reason is only valid with --state ignored")
    if args.note and len(args.note) > MAX_NOTE_LENGTH:
        parser.error(f"--note must be at most {MAX_NOTE_LENGTH} characters")

    token = get_token()
    if not token and not args.dry_run:
        print(
            "No token found - set the environment variable SEMGREP_APP_TOKEN "
            f"or use `semgrep login` to save one in {SEMGREP_SETTINGS_PATH}",
            file=sys.stderr,
        )
        return 1

    try:
        issues_by_type = read_issues(args.csv, args.issue_type)
    except (OSError, ValueError) as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    total = sum(len(ids) for ids in issues_by_type.values())
    print(f"{total} unique issue(s) to process in deployment slug '{args.deployment_slug}'")
    if not total:
        return 0

    session = create_session(token) if not args.dry_run else None

    request_count = 0
    triaged_count = 0
    sibling_count = 0
    queued_sibling_count = 0
    not_triaged = []

    for issue_type, pending in issues_by_type.items():
        while pending:
            batch = list(pending)[: args.limit]

            payload = {
                "issue_type": issue_type,
                "issue_ids": batch,
                "limit": args.limit,
            }
            if args.state:
                payload["new_triage_state"] = args.state
            if args.reason:
                payload["new_triage_reason"] = args.reason
            if args.note:
                payload["new_note"] = args.note

            request_count += 1
            label = f"[{request_count}] {issue_type}: submitting {len(batch)} issue(s)"

            if args.dry_run:
                print(f"{label} (dry run)")
                for issue_id in batch:
                    del pending[issue_id]
                continue

            if request_count > 1:
                time.sleep(args.delay)

            try:
                result = bulk_triage(session, args.deployment_slug, payload)
            except (requests.RequestException, RuntimeError) as e:
                remaining = [
                    (remaining_type, issue_id)
                    for remaining_type, remaining_ids in issues_by_type.items()
                    for issue_id in remaining_ids
                ]
                write_issues_csv(args.remaining_csv, remaining)
                if not_triaged:
                    write_issues_csv(args.not_triaged_csv, not_triaged)
                print(f"{label} FAILED: {e}", file=sys.stderr)
                print(
                    f"{len(remaining)} unprocessed issue(s) written to {args.remaining_csv}; "
                    f"rerun with --csv {args.remaining_csv} to resume",
                    file=sys.stderr,
                )
                return 1

            triaged_ids = set(result.get("triaged_issues", []))
            triaged_count += result.get("num_triaged", len(triaged_ids))

            batch_ids = set(batch)
            batch_missing = [issue_id for issue_id in batch if issue_id not in triaged_ids]
            not_triaged.extend((issue_type, issue_id) for issue_id in batch_missing)

            # Siblings triaged via shared fingerprint; any that are still queued
            # don't need to be submitted again.
            siblings = triaged_ids - batch_ids
            siblings_in_queue = [issue_id for issue_id in siblings if issue_id in pending]
            for issue_id in batch:
                del pending[issue_id]
            for issue_id in siblings_in_queue:
                del pending[issue_id]
            sibling_count += len(siblings)
            queued_sibling_count += len(siblings_in_queue)

            print(
                f"{label} -> {result.get('num_triaged', len(triaged_ids))} triaged; "
                f"{len(siblings)} additional sibling(s) triaged "
                f"({len(siblings_in_queue)} removed from queue); "
                f"{len(batch_missing)} submitted issue(s) not reported as triaged; "
                f"{len(pending)} {issue_type} issue(s) left"
            )

    if args.dry_run:
        print(f"Dry run: up to {request_count} request(s) would be sent")
        return 0

    print(
        f"Done: {request_count} request(s), {triaged_count} issue(s) triaged, "
        f"including {sibling_count} additional sibling(s) not submitted "
        f"({queued_sibling_count} of them removed from queue)"
    )
    if not_triaged:
        write_issues_csv(args.not_triaged_csv, not_triaged)
        print(
            f"{len(not_triaged)} submitted issue(s) were not reported as triaged; "
            f"written to {args.not_triaged_csv}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
