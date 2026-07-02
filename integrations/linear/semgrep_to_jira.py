#!/usr/bin/env python3

# Semgrep -> JIRA ticket creation for findings on a subset of repos.

# Logic
# 1) List all projects in a Semgrep deployment.
# 2) Keep only projects starting with PROJECT_PREFIX (e.g., "sebasrevuelta/").
# 3) For each matching project, fetch findings filtered by repo name and severity.
# 4) For each finding, create one Semgrep "ticket" (JIRA) via POST /tickets.

# Notes / assumptions (don't skip these):
# - The Semgrep v1 endpoints typically paginate. This script supports cursor-style pagination when present.
# - One POST request is made per finding.
# - You must prevent duplicate tickets somehow (tagging, checking existing tickets, or only sending new issue_ids).
#   This script includes a simple in-memory de-dupe you can extend.

# Requirements:
#   pip install requests

# Environment variables:
#   SEMGREP_TOKEN    : Semgrep API token (required)
#   DEPLOYMENT_SLUG  : deploymentSlug (string used in URL path, required)
#   JIRA_PROJECT_ID  : JIRA project ID (required; always included in payload)
#   PROJECT_PREFIX   : Repository name prefix filter, e.g. "myorg/" (required)
# Optional:
#   SEMGREP_BASE_URL : default https://semgrep.dev


from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import urljoin

import requests


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _get_env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r; using default %d", name, raw, default)
        return default
    if value < minimum:
        logger.warning("%s=%d is below minimum %d; using default %d", name, value, minimum, default)
        return default
    return value


# =========================
# Constants (edit these)
# =========================
SEMGREP_BASE_URL = os.getenv("SEMGREP_BASE_URL", "https://semgrep.dev").rstrip("/")
DEPLOYMENT_SLUG = os.getenv("DEPLOYMENT_SLUG", "").strip()

PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "").strip()  # only projects starting with this prefix

# JIRA project ID (optional; included only when provided)
JIRA_PROJECT_ID = os.getenv("JIRA_PROJECT_ID", "").strip()

# Findings query behavior
FINDINGS_PAGE_SIZE = 200
PROJECTS_PAGE_SIZE = 100
# The findings API takes a single `status` per request; we query each of these
# and merge. "fixing" is the status shown as "To Fix" in the Semgrep UI.
FINDINGS_STATUSES = ["open", "reviewing", "fixing"]

# Misc
REQUEST_TIMEOUT_S = _get_env_int("SEMGREP_REQUEST_TIMEOUT_S", 30)
RATE_LIMIT_SLEEP_S = _get_env_int("SEMGREP_RETRY_SLEEP_S", 2)   # base backoff on 429/5xx/network errors
MAX_RETRIES = _get_env_int("SEMGREP_MAX_RETRIES", 5)
MAX_BACKOFF_S = _get_env_int("SEMGREP_MAX_BACKOFF_S", 30)


# =========================
# Helpers / types
# =========================
class SemgrepClient:
    def __init__(self, base_url: str, token: str, timeout_s: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json: Any = None) -> Dict[str, Any]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=self.timeout_s,
                )
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"{method} {url} failed after {MAX_RETRIES} attempts due to a network timeout/connection error: {exc}"
                    ) from exc
                sleep_s = min(MAX_BACKOFF_S, RATE_LIMIT_SLEEP_S * attempt)
                logger.warning(
                    "%s %s network error on attempt %d/%d: %s. Retrying in %ss.",
                    method,
                    url,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    sleep_s,
                )
                time.sleep(sleep_s)
                continue

            # Basic backoff for rate limiting / transient errors
            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"{method} {url} failed after {MAX_RETRIES} attempts with retryable HTTP status {resp.status_code}\n{resp.text}"
                    )
                sleep_s = min(MAX_BACKOFF_S, RATE_LIMIT_SLEEP_S * attempt)
                logger.warning(
                    "%s %s returned %d on attempt %d/%d. Retrying in %ss.",
                    method,
                    url,
                    resp.status_code,
                    attempt,
                    MAX_RETRIES,
                    sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if not resp.ok:
                raise RuntimeError(
                    f"{method} {url} failed: {resp.status_code}\n{resp.text}"
                )

            try:
                return resp.json()
            except ValueError as exc:
                raise RuntimeError(
                    f"{method} {url} returned a non-JSON response: {resp.text}"
                ) from exc

        raise RuntimeError(f"{method} {url} failed after retries.")

    def list_deployments(self) -> List[Dict[str, Any]]:
        data = self._request("GET", "/api/v1/deployments")
        batch = (
            data.get("deployments")
            or data.get("data")
            or data.get("results")
            or []
        )
        if isinstance(batch, list):
            return batch
        raise RuntimeError(f"Unexpected deployments response shape: {data.keys()}")

    def get_default_deployment_slug(self) -> Optional[str]:
        """Return the slug of the first deployment accessible to the token."""
        for d in self.list_deployments():
            slug = d.get("slug") or d.get("name")
            if isinstance(slug, str) and slug.strip():
                return slug.strip()
        return None

    def list_projects(self, deployment_slug: str) -> List[Dict[str, Any]]:
        path = f"/api/v1/deployments/{deployment_slug}/projects"

        # Projects are paginated via a zero-based `page` param (not a cursor).
        # Stop when a page comes back empty; the "no new items" guard also stops
        # us if the API caps page_size or ignores `page`, so we never loop
        # forever or silently drop projects.
        projects: List[Dict[str, Any]] = []
        seen_names: Set[str] = set()
        page = 0

        while True:
            params: Dict[str, Any] = {"page": page, "page_size": PROJECTS_PAGE_SIZE}
            data = self._request("GET", path, params=params)

            batch = (
                data.get("projects")
                or data.get("data")
                or data.get("results")
                or []
            )
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected projects response shape: {data.keys()}")
            if not batch:
                break

            new_count = 0
            for p in batch:
                name = get_project_name(p) if isinstance(p, dict) else None
                if isinstance(name, str):
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                new_count += 1
                projects.append(p)

            if new_count == 0:
                break
            page += 1

        return projects

    def list_findings_for_repo(
        self,
        deployment_slug: str,
        repo: str,
        *,
        severities: Optional[Iterable[str]] = None,
        issue_type: Optional[str] = None,
        statuses: Optional[Iterable[str]] = None,
        page_size: int = 200,
    ) -> List[Dict[str, Any]]:
        path = f"/api/v1/deployments/{deployment_slug}/findings"

        # The findings API accepts a single `status` per request, so query each
        # requested status separately and de-dupe by finding id. Results are
        # paginated via a zero-based `page` param (not a cursor); we stop on an
        # empty page, and the "no new items" guard stops us if the API caps
        # page_size or ignores `page` (so no infinite loop, no dropped pages).
        status_list: List[Optional[str]] = list(statuses) if statuses else [None]

        findings: List[Dict[str, Any]] = []
        seen_ids: Set[int] = set()

        for status in status_list:
            page = 0
            while True:
                params: Dict[str, Any] = {
                    "repos": repo,
                    "page": page,
                    "page_size": page_size,
                }
                if status:
                    params["status"] = status
                if severities:
                    params["severities"] = ",".join(severities)
                if issue_type:
                    params["issue_type"] = issue_type

                data = self._request("GET", path, params=params)

                batch = (
                    data.get("findings")
                    or data.get("data")
                    or data.get("results")
                    or []
                )
                if not isinstance(batch, list):
                    raise RuntimeError(f"Unexpected findings response shape: {data.keys()}")
                if not batch:
                    break

                new_count = 0
                for f in batch:
                    fid = f.get("id") if isinstance(f, dict) else None
                    if isinstance(fid, int):
                        if fid in seen_ids:
                            continue
                        seen_ids.add(fid)
                    new_count += 1
                    findings.append(f)

                if new_count == 0:
                    break
                page += 1

        return findings

    def create_ticket(self, deployment_slug: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        path = f"/api/v1/deployments/{deployment_slug}/tickets"
        return self._request("POST", path, json=payload)

    def triage_findings(
        self,
        deployment_slug: str,
        issue_ids: List[int],
        *,
        issue_type: str,
        new_triage_state: str,
    ) -> Dict[str, Any]:
        """Bulk-triage findings to a new triage state via POST /triage.

        e.g. new_triage_state="fixing" sets the finding's status to "To Fix".
        Valid states: ignored, reviewing, fixing, reopened, provisionally_ignored.
        """
        path = f"/api/v1/deployments/{deployment_slug}/triage"
        payload = {
            "issue_ids": issue_ids,
            "issue_type": issue_type,
            "new_triage_state": new_triage_state,
        }
        return self._request("POST", path, json=payload)


def get_project_name(project_obj: Dict[str, Any]) -> Optional[str]:
    for key in ("name", "project_name", "repo", "repository", "full_name", "slug"):
        val = project_obj.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def extract_finding_fields(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort extraction of ticket-relevant fields from a finding object.
    Because schemas vary, this intentionally probes multiple key paths.
    """
    out: Dict[str, Any] = {}

    # Issue ID (Semgrep finding / issue id)
    for k in ("id", "issue_id", "finding_id"):
        if isinstance(finding.get(k), int):
            out["issue_id"] = finding[k]
            break

    # Issue type (SAST/SCA/Secrets) best-effort
    issue_type = (
        finding.get("issue_type")
        or finding.get("type")
        or finding.get("category")
        or finding.get("metadata", {}).get("issue_type")
    )
    if isinstance(issue_type, str) and issue_type.strip():
        out["issue_type"] = issue_type.strip().lower()

    return out


def build_ticket_payload(
    *,
    issue_type: str,
    issue_id: int,
    jira_project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Mandatory fields: issue_type and issue_ids.
    Optional field: jira_project_id.
    """
    payload: Dict[str, Any] = {
        "issue_type": issue_type,
        "issue_ids": [issue_id],
    }
    if jira_project_id:
        payload["jira_project_id"] = jira_project_id
    return payload


def _bucket_contains_issue_id(bucket: Any, issue_id: int) -> bool:
    if isinstance(bucket, list):
        for item in bucket:
            if isinstance(item, int) and item == issue_id:
                return True
            if isinstance(item, str) and item.isdigit() and int(item) == issue_id:
                return True
            if isinstance(item, dict):
                nested_ids = item.get("issue_ids")
                if isinstance(nested_ids, list):
                    for nested_id in nested_ids:
                        if isinstance(nested_id, int) and nested_id == issue_id:
                            return True
                        if isinstance(nested_id, str) and nested_id.isdigit() and int(nested_id) == issue_id:
                            return True
                for key in ("issue_id", "id"):
                    value = item.get(key)
                    if isinstance(value, int) and value == issue_id:
                        return True
                    if isinstance(value, str) and value.isdigit() and int(value) == issue_id:
                        return True
    return False


def get_ticket_creation_status(resp: Dict[str, Any], issue_id: int) -> str:
    """
    Classify Semgrep ticket creation response for a specific issue_id.
    """
    if _bucket_contains_issue_id(resp.get("succeeded"), issue_id):
        return "success"
    if _bucket_contains_issue_id(resp.get("skipped"), issue_id):
        return "skipped"
    if _bucket_contains_issue_id(resp.get("failed"), issue_id):
        return "failure"

    # Fallback when issue IDs are not echoed by API response.
    if isinstance(resp.get("failed"), list) and resp.get("failed"):
        return "failure"
    if isinstance(resp.get("succeeded"), list) and resp.get("succeeded"):
        return "success"
    if isinstance(resp.get("skipped"), list) and resp.get("skipped"):
        return "skipped"
    return "unknown"


def get_ticket_creation_failure_reason(resp: Dict[str, Any], issue_id: int) -> Optional[str]:
    """
    Extract a human-readable failure reason from the "failed" response bucket.
    """
    failed_bucket = resp.get("failed")
    if not isinstance(failed_bucket, list):
        return None

    matched_item: Optional[Dict[str, Any]] = None
    for item in failed_bucket:
        if not isinstance(item, dict):
            continue
        if _bucket_contains_issue_id([item], issue_id):
            matched_item = item
            break

    # Fall back to first failed entry if we cannot match by issue_id.
    if matched_item is None:
        for item in failed_bucket:
            if isinstance(item, dict):
                matched_item = item
                break

    if matched_item is None:
        return None

    for key in ("message", "error", "reason", "detail", "details"):
        value = matched_item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    nested_error = matched_item.get("errors")
    if isinstance(nested_error, list):
        texts: List[str] = []
        for entry in nested_error:
            if isinstance(entry, str) and entry.strip():
                texts.append(entry.strip())
            elif isinstance(entry, dict):
                for key in ("message", "error", "reason", "detail"):
                    value = entry.get(key)
                    if isinstance(value, str) and value.strip():
                        texts.append(value.strip())
                        break
        if texts:
            return "; ".join(texts)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Create JIRA tickets from Semgrep findings.")
    parser.add_argument(
        "--deployment",
        metavar="SLUG",
        default=None,
        help="Semgrep deployment slug. Overrides the DEPLOYMENT_SLUG env var.",
    )
    parser.add_argument(
        "--repo",
        metavar="REPO",
        default=None,
        help="Process a single repo (e.g. sebasrevuelta/AmazingRepo) instead of all prefix-matching projects.",
    )
    parser.add_argument(
        "--severities",
        metavar="SEV",
        nargs="+",
        default=["critical"],
        help="Severity levels to fetch and ticket (default: high critical).",
    )
    parser.add_argument(
        "--issue-type",
        choices=["sast", "sca"],
        default="sast",
        help="Issue type to filter findings and set on tickets (sast or sca, default: sast).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Log actions without creating tickets (default: True). Pass --no-dry-run to create tickets.",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually create tickets (disables dry run mode).",
    )
    args = parser.parse_args()

    target_severities: List[str] = [s.strip().lower() for s in args.severities if s.strip()]
    if not target_severities:
        logger.error("--severities must include at least one value.")
        return 2

    issue_type: str = args.issue_type
    dry_run: bool = args.dry_run

    token = os.getenv("SEMGREP_TOKEN", "").strip()
    if not token:
        logger.error("SEMGREP_TOKEN env var is required.")
        return 2

    deployment_slug: str = (args.deployment or "").strip() or DEPLOYMENT_SLUG
    if not deployment_slug:
        logger.error("A deployment slug is required (--deployment or DEPLOYMENT_SLUG env var).")
        return 2

    if not PROJECT_PREFIX:
        logger.error("PROJECT_PREFIX env var is required.")
        return 2

    jira_project_id: str = JIRA_PROJECT_ID

    client = SemgrepClient(SEMGREP_BASE_URL, token, timeout_s=REQUEST_TIMEOUT_S)

    logger.info("Semgrep base URL: %s", SEMGREP_BASE_URL)
    logger.info("Deployment slug:  %s", deployment_slug)
    logger.info("Project prefix:   %s", PROJECT_PREFIX)
    logger.info("Severities:       %s", target_severities)
    logger.info("Issue type:       %s", issue_type)
    logger.info("JIRA project ID:  %s", jira_project_id if jira_project_id else "(not set)")
    logger.info("DRY_RUN:          %s", dry_run)
    logger.info("Timeout (s):      %d", REQUEST_TIMEOUT_S)
    logger.info("Max retries:      %d", MAX_RETRIES)
    logger.info("Retry sleep (s):  %d", RATE_LIMIT_SLEEP_S)
    logger.info("Max backoff (s):  %d", MAX_BACKOFF_S)

    # 1) Determine the list of repos to process
    if args.repo:
        matching = [args.repo.strip()]
        logger.info("Single-repo mode: %s", matching[0])
    else:
        projects = client.list_projects(deployment_slug)
        project_names: List[str] = []
        for p in projects:
            name = get_project_name(p)
            if name:
                project_names.append(name)

        matching = [pn for pn in project_names if pn.startswith(PROJECT_PREFIX)]
        if not matching:
            logger.info("No matching projects found. Exiting.")
            return 0

        logger.info("Found %d projects; %d match prefix.", len(project_names), len(matching))

    # Track already-ticketed issue IDs in this run to avoid duplicates
    ticketed_issue_ids: Set[int] = set()

    # 2) For each repo -> fetch findings (API-filtered by severity) -> one ticket per finding
    for repo in sorted(set(matching)):
        logger.info("[REPO] %s", repo)

        findings = client.list_findings_for_repo(
            deployment_slug,
            repo,
            severities=target_severities,
            issue_type=issue_type,
            statuses=FINDINGS_STATUSES,
            page_size=FINDINGS_PAGE_SIZE,
        )

        if not findings:
            logger.info("  - No findings.")
            continue

        success_count = 0
        skipped_count = 0
        failure_count = 0
        for f in findings:
            fields = extract_finding_fields(f)
            issue_id = fields.get("issue_id")

            if not isinstance(issue_id, int):
                continue
            if issue_id in ticketed_issue_ids:
                continue

            payload = build_ticket_payload(
                issue_type=issue_type,
                issue_id=issue_id,
                jira_project_id=jira_project_id,
            )

            if dry_run:
                logger.info("  - DRY_RUN would create ticket: issue_id=%d issue_type=%s", issue_id, issue_type)
            else:
                resp = client.create_ticket(deployment_slug, payload)
                status = get_ticket_creation_status(resp, issue_id)
                if status == "success":
                    success_count += 1
                elif status == "skipped":
                    skipped_count += 1
                elif status == "failure":
                    failure_count += 1
                if status == "failure":
                    reason = get_ticket_creation_failure_reason(resp, issue_id)
                    if reason:
                        logger.info(
                            "  - Ticket create status=%s issue_id=%d issue_type=%s reason=%s",
                            status,
                            issue_id,
                            issue_type,
                            reason,
                        )
                    else:
                        logger.info(
                            "  - Ticket create status=%s issue_id=%d issue_type=%s reason=unknown (inspect API response)",
                            status,
                            issue_id,
                            issue_type,
                        )
                else:
                    logger.info(
                        "  - Ticket create status=%s issue_id=%d issue_type=%s",
                        status,
                        issue_id,
                        issue_type,
                    )

            ticketed_issue_ids.add(issue_id)

        logger.info(
            "  - Done. success=%d skipped=%d failure=%d",
            success_count,
            skipped_count,
            failure_count,
        )

    logger.info("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
