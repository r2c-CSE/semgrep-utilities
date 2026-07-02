#!/usr/bin/env python3

# Semgrep -> Linear issue creation for findings on a subset of repos.
#
# This script REUSES the Semgrep finding-gathering logic from semgrep_to_jira.py
# (project listing, prefix filtering, and paginated/severity-filtered findings
# retrieval) and then, as a second step, inserts one issue per finding into a
# Linear project.
#
# Logic
# 1) List all projects in a Semgrep deployment (reused SemgrepClient).
# 2) Keep only projects starting with PROJECT_PREFIX (e.g., "sebasrevuelta/").
# 3) For each matching project, fetch findings filtered by repo/severity/type.
# 4) For each finding, create one Linear issue in the configured Linear project
#    via the Linear GraphQL API (issueCreate mutation).
#
# Unlike the JIRA variant (which delegates to Semgrep's native POST /tickets
# endpoint), Linear is not a native Semgrep ticketing target, so this script
# builds the issue itself and talks to Linear's GraphQL API directly.
#
# Requirements:
#   pip install requests
#
# Environment variables:
#   SEMGREP_TOKEN     : Semgrep API token (required)
#   DEPLOYMENT_SLUG   : deploymentSlug (required; may be overridden by --deployment)
#   PROJECT_PREFIX    : Repository name prefix filter, e.g. "myorg/" (required)
#   LINEAR_API_KEY    : Linear API key (required)
#   LINEAR_PROJECT_ID : Linear project ID where issues are created (required)
# Optional:
#   LINEAR_TEAM_ID    : Linear team ID. If omitted, the team is resolved from
#                       the Linear project (first team the project belongs to).
#   LINEAR_API_URL    : default https://api.linear.app/graphql
#   SEMGREP_BASE_URL  : default https://semgrep.dev
#   (Retry/timeout env vars from semgrep_to_jira.py are reused.)
#
# NOTE ON DATA HANDLING: this script transmits Semgrep findings (scan output) to
# Linear. Confirm Linear is an approved integration for your org before running
# live (i.e. with --no-dry-run) against real findings.


from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

import requests

# Reuse the Semgrep-side logic and configuration from the JIRA script so the
# "gather findings" behaviour stays identical across both integrations.
import semgrep_to_jira as sj


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# =========================
# Linear configuration
# =========================
LINEAR_API_URL = os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql").rstrip("/")
LINEAR_PROJECT_ID = os.getenv("LINEAR_PROJECT_ID", "").strip()
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID", "").strip()

# Reuse the retry/timeout tuning from the JIRA module.
REQUEST_TIMEOUT_S = sj.REQUEST_TIMEOUT_S
RATE_LIMIT_SLEEP_S = sj.RATE_LIMIT_SLEEP_S
MAX_RETRIES = sj.MAX_RETRIES
MAX_BACKOFF_S = sj.MAX_BACKOFF_S

# Semgrep severity -> Linear priority (0 none, 1 urgent, 2 high, 3 medium, 4 low)
SEVERITY_TO_PRIORITY = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "info": 0,
}


# =========================
# Linear GraphQL client
# =========================
class LinearClient:
    def __init__(self, api_url: str, api_key: str, timeout_s: int = 30) -> None:
        self.api_url = api_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        # Linear personal API keys are passed directly in the Authorization
        # header (no "Bearer" prefix). OAuth access tokens use "Bearer <token>".
        auth = api_key if api_key.startswith("Bearer ") else api_key
        self.session.headers.update(
            {
                "Authorization": auth,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout_s,
                )
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"POST {self.api_url} failed after {MAX_RETRIES} attempts due to a network timeout/connection error: {exc}"
                    ) from exc
                sleep_s = min(MAX_BACKOFF_S, RATE_LIMIT_SLEEP_S * attempt)
                logger.warning(
                    "Linear GraphQL network error on attempt %d/%d: %s. Retrying in %ss.",
                    attempt,
                    MAX_RETRIES,
                    exc,
                    sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"Linear GraphQL failed after {MAX_RETRIES} attempts with retryable HTTP status {resp.status_code}\n{resp.text}"
                    )
                sleep_s = min(MAX_BACKOFF_S, RATE_LIMIT_SLEEP_S * attempt)
                logger.warning(
                    "Linear GraphQL returned %d on attempt %d/%d. Retrying in %ss.",
                    resp.status_code,
                    attempt,
                    MAX_RETRIES,
                    sleep_s,
                )
                time.sleep(sleep_s)
                continue

            if not resp.ok:
                raise RuntimeError(f"Linear GraphQL failed: {resp.status_code}\n{resp.text}")

            try:
                data = resp.json()
            except ValueError as exc:
                raise RuntimeError(f"Linear GraphQL returned a non-JSON response: {resp.text}") from exc

            if data.get("errors"):
                raise RuntimeError(f"Linear GraphQL returned errors: {data['errors']}")

            return data.get("data", {})

        raise RuntimeError("Linear GraphQL failed after retries.")

    def resolve_project(self, project_ref: str) -> Dict[str, Any]:
        """
        Resolve a project reference (UUID or URL slug id) to its canonical UUID
        and first team. The Linear `project(id:)` lookup accepts either form, but
        `issueCreate` / issue filters require the UUID.
        """
        query = """
        query ProjectLookup($id: String!) {
          project(id: $id) {
            id
            name
            teams(first: 1) { nodes { id name } }
          }
        }
        """
        data = self._graphql(query, {"id": project_ref})
        project = data.get("project") or {}
        nodes = (project.get("teams") or {}).get("nodes") or []
        team = nodes[0] if nodes else {}
        return {
            "id": project.get("id"),
            "name": project.get("name"),
            "team_id": team.get("id"),
            "team_name": team.get("name"),
        }

    def find_existing_issue(self, project_id: str, marker: str) -> bool:
        """True if an issue whose title contains `marker` already exists in the project."""
        query = """
        query FindIssue($filter: IssueFilter!) {
          issues(filter: $filter, first: 1) {
            nodes { id identifier title }
          }
        }
        """
        variables = {
            "filter": {
                "project": {"id": {"eq": project_id}},
                "title": {"contains": marker},
            }
        }
        data = self._graphql(query, variables)
        nodes = (data.get("issues") or {}).get("nodes") or []
        return bool(nodes)

    def create_issue(
        self,
        *,
        team_id: str,
        project_id: str,
        title: str,
        description: str,
        priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue { id identifier url title }
          }
        }
        """
        issue_input: Dict[str, Any] = {
            "teamId": team_id,
            "projectId": project_id,
            "title": title,
            "description": description,
        }
        if priority is not None:
            issue_input["priority"] = priority

        data = self._graphql(mutation, {"input": issue_input})
        return data.get("issueCreate") or {}


# =========================
# Finding -> Linear content
# =========================
def _first_str(obj: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        val = obj.get(k)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def extract_linear_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort extraction of the fields we need to build a readable Linear
    issue. Builds on the JIRA script's extractor for issue_id/issue_type and
    probes multiple key paths for the richer display fields.
    """
    base = sj.extract_finding_fields(finding)
    out: Dict[str, Any] = dict(base)  # issue_id, issue_type (best-effort)

    rule = finding.get("rule") if isinstance(finding.get("rule"), dict) else {}
    location = finding.get("location") if isinstance(finding.get("location"), dict) else {}
    repository = finding.get("repository") if isinstance(finding.get("repository"), dict) else {}
    metadata = finding.get("metadata") if isinstance(finding.get("metadata"), dict) else {}
    assistant = finding.get("assistant") if isinstance(finding.get("assistant"), dict) else {}

    out["rule_name"] = (
        _first_str(finding, ["rule_name", "check_id", "rule_id"])
        or _first_str(rule, ["name", "id"])
    )
    out["severity"] = (
        _first_str(finding, ["severity"])
        or _first_str(rule, ["severity"])
    )
    out["message"] = (
        _first_str(finding, ["rule_message", "message"])
        or _first_str(rule, ["message"])
    )
    out["path"] = (
        _first_str(location, ["file_path", "path"])
        or _first_str(finding, ["path", "file_path"])
    )
    out["repo"] = (
        _first_str(repository, ["name"])
        or _first_str(finding, ["repository_name", "repo"])
    )
    out["url"] = _first_str(finding, ["line_of_code_url", "url", "permalink"])

    line = location.get("line") or location.get("start_line")
    start = location.get("start") if isinstance(location.get("start"), dict) else {}
    if line is None:
        line = start.get("line")
    out["line"] = line if isinstance(line, int) else None

    ref = _first_str(metadata, ["shortlink", "source"])
    if ref:
        out["reference"] = ref

    # Confidence of the Semgrep rule (e.g. "high"/"medium"/"low"). Top-level on
    # the finding, with a fallback to the rule/metadata objects.
    out["confidence"] = (
        _first_str(finding, ["confidence"])
        or _first_str(rule, ["confidence"])
        or _first_str(metadata, ["confidence"])
    )

    # When the finding was first created/seen.
    out["created_at"] = _first_str(
        finding, ["created_at", "created", "first_seen_at", "relevant_since"]
    )

    # Guidance on how to fix, produced by Semgrep Assistant. The guidance object
    # carries a short summary and step-by-step instructions; prefer instructions
    # but fall back to summary (or a plain-string guidance field).
    guidance = assistant.get("guidance") if isinstance(assistant.get("guidance"), dict) else {}
    out["guidance_summary"] = _first_str(guidance, ["summary"])
    out["guidance"] = (
        _first_str(guidance, ["instructions", "summary"])
        or _first_str(assistant, ["guidance"])
    )

    return out


def build_issue_content(
    fields: Dict[str, Any],
    repo: str,
    *,
    issue_type: str,
    deployment_slug: str,
) -> Dict[str, Any]:
    """Return {title, description, priority, marker} for a Linear issue."""
    issue_id = fields.get("issue_id")
    rule_name = fields.get("rule_name") or "Semgrep finding"
    severity = (fields.get("severity") or "").lower()
    confidence = (fields.get("confidence") or "").lower()
    created_at = fields.get("created_at")
    path = fields.get("path")
    line = fields.get("line")

    # Stable marker embedded in the title so re-runs can de-dupe idempotently.
    marker = f"[Semgrep #{issue_id}]"

    # Title uses a human-readable name derived from the last segment of the rule
    # id (dashes -> spaces, title-cased). e.g.
    # "...active-debug-code-getstacktrace" -> "Active Debug Code Getstacktrace".
    display_name = " ".join(w.capitalize() for w in rule_name.split(".")[-1].split("-")) or rule_name

    location_str = ""
    if path:
        location_str = f" — {path}" + (f":{line}" if isinstance(line, int) else "")

    title = f"{marker} {display_name}{location_str}"
    # Linear title limit is generous, but keep it reasonable.
    if len(title) > 250:
        title = title[:247] + "..."

    # Rule field links to the rule on the Semgrep registry.
    if fields.get("rule_name"):
        rule_field = f"[{rule_name}]({sj.SEMGREP_BASE_URL}/r?q={rule_name})"
    else:
        rule_field = rule_name

    description_lines = [
        f"**Semgrep finding ID:** {issue_id}",
        f"**Rule:** {rule_field}",
        f"**Severity:** {severity or 'unknown'}",
        f"**Confidence:** {confidence or 'unknown'}",
        f"**Issue type:** {issue_type}",
        f"**Repository:** {fields.get('repo') or repo}",
    ]
    if created_at:
        description_lines.append(f"**Created at:** {created_at}")
    if path:
        loc = path + (f":{line}" if isinstance(line, int) else "")
        # Location links to the source line (same target as "View the code").
        loc_field = f"[{loc}]({fields['url']})" if fields.get("url") else loc
        description_lines.append(f"**Location:** {loc_field}")
    if fields.get("message"):
        description_lines.append("")
        description_lines.append("**Details:**")
        description_lines.append(fields["message"])
    # Fix guidance from Semgrep Assistant (finding.assistant.guidance).
    if fields.get("guidance"):
        description_lines.append("")
        description_lines.append("**How to fix (Semgrep Assistant):**")
        summary = fields.get("guidance_summary")
        if summary and summary != fields["guidance"]:
            description_lines.append(f"_{summary}_")
            description_lines.append("")
        description_lines.append(fields["guidance"])
    if fields.get("url"):
        description_lines.append("")
        description_lines.append(f"[View the code]({fields['url']})")
    # Link to the finding's details page on the Semgrep platform.
    finding_url = f"{sj.SEMGREP_BASE_URL}/orgs/{deployment_slug}/findings/{issue_id}"
    description_lines.append("")
    description_lines.append(f"[View in Semgrep]({finding_url})")

    priority = SEVERITY_TO_PRIORITY.get(severity)

    return {
        "title": title,
        "description": "\n".join(description_lines),
        "priority": priority,
        "marker": marker,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Linear issues from Semgrep findings.")
    parser.add_argument(
        "--repo",
        metavar="REPO",
        default=None,
        help="Process a single repo instead of all prefix-matching projects.",
    )
    parser.add_argument(
        "--severities",
        metavar="SEV",
        nargs="+",
        default=["critical"],
        help="Severity levels to fetch and file (default: critical).",
    )
    parser.add_argument(
        "--issue-type",
        choices=["sast", "sca", "secrets"],
        default="sast",
        help="Issue type to filter findings (sast, sca or secrets, default: sast).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Log actions without creating Linear issues (default: True). Pass --no-dry-run to create issues.",
    )
    parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually create Linear issues (disables dry run mode).",
    )
    args = parser.parse_args()

    target_severities: List[str] = [s.strip().lower() for s in args.severities if s.strip()]
    if not target_severities:
        logger.error("--severities must include at least one value.")
        return 2

    issue_type: str = args.issue_type
    dry_run: bool = args.dry_run

    # --- Semgrep side (reused config) ---
    token = os.getenv("SEMGREP_TOKEN", "").strip()
    if not token:
        logger.error("SEMGREP_TOKEN env var is required.")
        return 2

    # --- Linear side ---
    linear_api_key = os.getenv("LINEAR_API_KEY", "").strip()
    if not linear_api_key:
        logger.error("LINEAR_API_KEY env var is required.")
        return 2

    if not LINEAR_PROJECT_ID:
        logger.error("LINEAR_PROJECT_ID env var is required.")
        return 2

    semgrep_client = sj.SemgrepClient(sj.SEMGREP_BASE_URL, token, timeout_s=REQUEST_TIMEOUT_S)
    linear_client = LinearClient(LINEAR_API_URL, linear_api_key, timeout_s=REQUEST_TIMEOUT_S)

    # Deployment slug: use DEPLOYMENT_SLUG if set, otherwise auto-discover it
    # from the /api/v1/deployments endpoint.
    deployment_slug: str = sj.DEPLOYMENT_SLUG or (semgrep_client.get_default_deployment_slug() or "")
    if not deployment_slug:
        logger.error("Could not determine a deployment slug (no deployments accessible to this token).")
        return 2

    logger.info("Semgrep base URL:  %s", sj.SEMGREP_BASE_URL)
    logger.info("Deployment slug:   %s", deployment_slug)
    logger.info("Project prefix:    %s", sj.PROJECT_PREFIX or "(all projects)")
    logger.info("Severities:        %s", target_severities)
    logger.info("Issue type:        %s", issue_type)
    logger.info("Linear API URL:    %s", LINEAR_API_URL)
    logger.info("Linear project ID: %s", LINEAR_PROJECT_ID)
    logger.info("DRY_RUN:           %s", dry_run)

    # Resolve the Linear project reference (UUID or URL slug id) to its canonical
    # UUID, which issueCreate and issue filters require. Also derive the team.
    project = linear_client.resolve_project(LINEAR_PROJECT_ID)
    project_uuid = project.get("id") or ""
    if not project_uuid:
        logger.error(
            "Could not resolve Linear project %r. Check LINEAR_PROJECT_ID.",
            LINEAR_PROJECT_ID,
        )
        return 2
    logger.info("Linear project UUID: %s (%s)", project_uuid, project.get("name") or "?")

    team_id = LINEAR_TEAM_ID or (project.get("team_id") or "")
    if not team_id:
        logger.error(
            "Could not determine a Linear team. Set LINEAR_TEAM_ID or ensure "
            "LINEAR_PROJECT_ID is valid and belongs to a team."
        )
        return 2
    logger.info("Linear team ID:    %s", team_id)

    # 1) Determine the list of repos to process (reused prefix filtering).
    if args.repo:
        matching = [args.repo.strip()]
        logger.info("Single-repo mode: %s", matching[0])
    else:
        projects = semgrep_client.list_projects(deployment_slug)
        project_names: List[str] = []
        for p in projects:
            name = sj.get_project_name(p)
            if name:
                project_names.append(name)

        matching = [pn for pn in project_names if pn.startswith(sj.PROJECT_PREFIX)]
        if not matching:
            logger.info("No matching projects found. Exiting.")
            return 0

        logger.info("Found %d projects; %d match prefix.", len(project_names), len(matching))

    # In-run de-dupe of issue IDs (mirrors the JIRA script).
    filed_issue_ids: Set[int] = set()

    # 2) For each repo -> fetch findings -> one Linear issue per finding.
    for repo in sorted(set(matching)):
        logger.info("[REPO] %s", repo)

        findings = semgrep_client.list_findings_for_repo(
            deployment_slug,
            repo,
            severities=target_severities,
            issue_type=issue_type,
            status=sj.FINDINGS_STATUS,
            page_size=sj.FINDINGS_PAGE_SIZE,
        )

        if not findings:
            logger.info("  - No findings.")
            continue

        success_count = 0
        skipped_count = 0
        failure_count = 0
        for f in findings:
            fields = extract_linear_finding(f)
            issue_id = fields.get("issue_id")

            if not isinstance(issue_id, int):
                continue
            if issue_id in filed_issue_ids:
                continue
            filed_issue_ids.add(issue_id)

            content = build_issue_content(
                fields, repo, issue_type=issue_type, deployment_slug=deployment_slug
            )

            if dry_run:
                logger.info(
                    "  - DRY_RUN would create Linear issue: %s (priority=%s)",
                    content["title"],
                    content["priority"],
                )
                continue

            # Idempotency: skip if an issue with this finding's marker exists.
            try:
                if linear_client.find_existing_issue(project_uuid, content["marker"]):
                    skipped_count += 1
                    logger.info("  - Skipped (already exists): %s", content["marker"])
                    continue
            except RuntimeError as exc:
                logger.warning("  - Duplicate check failed for %s: %s", content["marker"], exc)

            try:
                resp = linear_client.create_issue(
                    team_id=team_id,
                    project_id=project_uuid,
                    title=content["title"],
                    description=content["description"],
                    priority=content["priority"],
                )
            except RuntimeError as exc:
                failure_count += 1
                logger.info("  - Issue create failed issue_id=%d: %s", issue_id, exc)
                continue

            if resp.get("success"):
                success_count += 1
                issue = resp.get("issue") or {}
                logger.info(
                    "  - Created %s (%s)",
                    issue.get("identifier") or "issue",
                    issue.get("url") or "",
                )
                # Mark the Semgrep finding as "To Fix" now that it's tracked in Linear.
                try:
                    semgrep_client.triage_findings(
                        deployment_slug,
                        [issue_id],
                        issue_type=issue_type,
                        new_triage_state="fixing",
                    )
                    logger.info("  - Marked finding %d as To Fix.", issue_id)
                except RuntimeError as exc:
                    logger.warning("  - Failed to mark finding %d as To Fix: %s", issue_id, exc)
            else:
                failure_count += 1
                logger.info("  - Issue create returned success=false issue_id=%d", issue_id)

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
