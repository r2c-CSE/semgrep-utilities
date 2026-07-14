#!/usr/bin/env python3
"""
Sync GitHub organization teams to Semgrep RBAC teams.

For each GitHub team:
  - Creates a matching Semgrep team if one does not exist
  - Updates an existing Semgrep team to match GitHub members and repos

Members are matched by GitHub login (username).
Repos are matched by full path (e.g., my-org/my-repo).

Usage:
    python3 sync_github_teams.py [--org ORG_NAME] [--dry-run]

Required environment variables:
    SEMGREP_APP_TOKEN   Semgrep API token with org-admin access
    GITHUB_TOKEN        GitHub token with read:org scope
    GITHUB_ORG          GitHub organization name (or use --org flag)
"""

import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
SEMGREP_API_URL = "https://semgrep.dev/api"


# ── GitHub ───────────────────────────────────────────────────────────────────

def _gh_paginate(url, headers):
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        yield from data
        if len(data) < 100:
            break
        page += 1


def get_github_teams(org, headers):
    return list(_gh_paginate(f"{GITHUB_API_URL}/orgs/{org}/teams", headers))


def get_team_members(org, team_slug, headers):
    return list(_gh_paginate(f"{GITHUB_API_URL}/orgs/{org}/teams/{team_slug}/members", headers))


def get_team_repos(org, team_slug, headers):
    return list(_gh_paginate(f"{GITHUB_API_URL}/orgs/{org}/teams/{team_slug}/repos", headers))


# ── Semgrep ──────────────────────────────────────────────────────────────────

def get_deployment_info(semgrep_headers):
    """Returns (deployment_id, deployment_slug)."""
    resp = requests.get(f"{SEMGREP_API_URL}/v1/deployments", headers=semgrep_headers)
    resp.raise_for_status()
    deployments = resp.json().get("deployments", [])
    if not deployments:
        sys.exit("No Semgrep deployments found for this token.")
    d = deployments[0]
    return str(d["id"]), d["slug"]


def get_semgrep_members(deployment_id, semgrep_headers):
    """Returns dict mapping github_login -> semgrep_user_id."""
    login_to_id = {}
    page_token = ""
    while True:
        resp = requests.post(
            f"{SEMGREP_API_URL}/agent/deployments/{deployment_id}/users/list",
            headers=semgrep_headers,
            json={
                "deploymentId": deployment_id,
                "options": {"pageSize": 500, "pageToken": page_token},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        for user in data.get("users", []):
            login = user.get("login")
            user_id = user.get("id")
            if login and user_id:
                login_to_id[login] = str(user_id)
        page_token = data.get("pageToken", "")
        if not page_token:
            break
    return login_to_id


def get_semgrep_projects(deployment_slug, semgrep_headers):
    """Returns dict mapping project full-path name -> semgrep project id."""
    name_to_id = {}
    page = 0
    while True:
        resp = requests.get(
            f"{SEMGREP_API_URL}/v1/deployments/{deployment_slug}/projects",
            headers=semgrep_headers,
            params={"page_size": 200, "page": page},
        )
        resp.raise_for_status()
        projects = resp.json().get("projects", [])
        if not projects:
            break
        for project in projects:
            name = project.get("name")
            proj_id = project.get("id")
            if name and proj_id:
                name_to_id[name] = str(proj_id)
        page += 1
    return name_to_id


def get_semgrep_teams(deployment_id, semgrep_headers):
    """Returns dict mapping team_name -> team object (includes 'id')."""
    name_to_team = {}
    cursor = ""
    while True:
        resp = requests.post(
            f"{SEMGREP_API_URL}/permissions/v2/deployments/{deployment_id}/teams/list",
            headers=semgrep_headers,
            json={"limit": "100", "cursor": cursor},
        )
        resp.raise_for_status()
        data = resp.json()
        for team in data.get("teams", []):
            name_to_team[team["name"]] = team
        cursor = data.get("cursor", "")
        if not cursor:
            break
    return name_to_team


def get_team_current_user_ids(deployment_id, team_id, semgrep_headers):
    """Returns set of user IDs currently assigned to the Semgrep team."""
    user_ids = set()
    cursor = ""
    while True:
        resp = requests.get(
            f"{SEMGREP_API_URL}/permissions/v2/deployments/{deployment_id}/teams/{team_id}/members",
            headers=semgrep_headers,
            params={"limit": 100, "cursor": cursor},
        )
        resp.raise_for_status()
        data = resp.json()
        for user in data.get("users", []):
            user_ids.add(str(user["userId"]))
        cursor = data.get("cursor", "")
        if not cursor:
            break
    return user_ids


def get_team_current_repo_ids(deployment_id, team_id, semgrep_headers):
    """Returns set of repository IDs currently assigned to the Semgrep team."""
    repo_ids = set()
    cursor = ""
    while True:
        resp = requests.get(
            f"{SEMGREP_API_URL}/permissions/v2/deployments/{deployment_id}/teams/{team_id}/repos",
            headers=semgrep_headers,
            params={"limit": 100, "cursor": cursor},
        )
        resp.raise_for_status()
        data = resp.json()
        for rid in data.get("repositoryIds", []):
            repo_ids.add(str(rid))
        cursor = data.get("cursor", "")
        if not cursor:
            break
    return repo_ids


def create_semgrep_team(deployment_id, name, user_ids, repo_ids, semgrep_headers, dry_run):
    logger.info(f"  Creating team '{name}' with {len(user_ids)} users and {len(repo_ids)} repos")
    if dry_run:
        return
    payload = {
        "team": {
            "name": name,
            "repositoryIds": list(repo_ids),
            "users": [{"userId": uid, "role": "TEAM_ROLE_MEMBER"} for uid in user_ids],
        }
    }
    resp = requests.post(
        f"{SEMGREP_API_URL}/permissions/v2/deployments/{deployment_id}/teams",
        headers=semgrep_headers,
        json=payload,
    )
    resp.raise_for_status()


def update_semgrep_team(
    deployment_id, team_id, team_name,
    desired_user_ids, desired_repo_ids,
    current_user_ids, current_repo_ids,
    semgrep_headers, dry_run,
):
    users_to_add = desired_user_ids - current_user_ids
    users_to_remove = current_user_ids - desired_user_ids
    repos_to_add = desired_repo_ids - current_repo_ids
    repos_to_remove = current_repo_ids - desired_repo_ids

    if not any([users_to_add, users_to_remove, repos_to_add, repos_to_remove]):
        logger.info(f"  Team '{team_name}' is already up to date")
        return

    logger.info(
        f"  Updating team '{team_name}': "
        f"+{len(users_to_add)}/-{len(users_to_remove)} users, "
        f"+{len(repos_to_add)}/-{len(repos_to_remove)} repos"
    )
    if dry_run:
        return

    user_actions = (
        [{"userId": uid, "action": "UPDATE_ACTION_ADD", "role": "TEAM_ROLE_MEMBER"} for uid in users_to_add]
        + [{"userId": uid, "action": "UPDATE_ACTION_REMOVE"} for uid in users_to_remove]
    )
    repo_actions = (
        [{"repositoryId": rid, "action": "UPDATE_ACTION_ADD"} for rid in repos_to_add]
        + [{"repositoryId": rid, "action": "UPDATE_ACTION_REMOVE"} for rid in repos_to_remove]
    )

    team_update = {}
    if user_actions:
        team_update["users"] = user_actions
    if repo_actions:
        team_update["repositories"] = repo_actions

    resp = requests.patch(
        f"{SEMGREP_API_URL}/permissions/v2/deployments/{deployment_id}/teams/{team_id}",
        headers=semgrep_headers,
        json={"team": team_update},
    )
    resp.raise_for_status()


# ── Main ─────────────────────────────────────────────────────────────────────

def sync_teams(github_org, dry_run):
    semgrep_token = os.environ.get("SEMGREP_APP_TOKEN")
    github_token = os.environ.get("GITHUB_TOKEN")

    if not semgrep_token:
        sys.exit("SEMGREP_APP_TOKEN environment variable is required.")
    if not github_token:
        sys.exit("GITHUB_TOKEN environment variable is required.")

    semgrep_headers = {
        "Authorization": f"Bearer {semgrep_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    github_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    if dry_run:
        logger.info("DRY RUN — no changes will be written to Semgrep")

    logger.info("Fetching Semgrep deployment info...")
    deployment_id, deployment_slug = get_deployment_info(semgrep_headers)
    logger.info(f"  Deployment: {deployment_slug} (id={deployment_id})")

    logger.info("Fetching Semgrep members...")
    semgrep_login_to_id = get_semgrep_members(deployment_id, semgrep_headers)
    logger.info(f"  Found {len(semgrep_login_to_id)} Semgrep members")

    logger.info("Fetching Semgrep projects...")
    semgrep_name_to_id = get_semgrep_projects(deployment_slug, semgrep_headers)
    logger.info(f"  Found {len(semgrep_name_to_id)} Semgrep projects")

    logger.info("Fetching existing Semgrep teams...")
    semgrep_teams = get_semgrep_teams(deployment_id, semgrep_headers)
    logger.info(f"  Found {len(semgrep_teams)} existing Semgrep teams")

    logger.info(f"Fetching GitHub teams for org '{github_org}'...")
    github_teams = get_github_teams(github_org, github_headers)
    logger.info(f"  Found {len(github_teams)} GitHub teams")

    for gh_team in github_teams:
        team_name = gh_team["name"]
        team_slug = gh_team["slug"]
        logger.info(f"\nProcessing GitHub team: {team_name}")

        gh_members = get_team_members(github_org, team_slug, github_headers)
        gh_repos = get_team_repos(github_org, team_slug, github_headers)

        desired_user_ids = set()
        for member in gh_members:
            login = member["login"]
            semgrep_id = semgrep_login_to_id.get(login)
            if semgrep_id:
                desired_user_ids.add(semgrep_id)
            else:
                logger.warning(f"  GitHub user '{login}' not found in Semgrep, skipping")

        desired_repo_ids = set()
        for repo in gh_repos:
            full_name = repo["full_name"]
            semgrep_id = semgrep_name_to_id.get(full_name)
            if semgrep_id:
                desired_repo_ids.add(semgrep_id)
            else:
                logger.warning(f"  Repo '{full_name}' not found in Semgrep, skipping")

        existing_team = semgrep_teams.get(team_name)
        if existing_team:
            team_id = str(existing_team["id"])
            current_user_ids = get_team_current_user_ids(deployment_id, team_id, semgrep_headers)
            current_repo_ids = get_team_current_repo_ids(deployment_id, team_id, semgrep_headers)
            update_semgrep_team(
                deployment_id, team_id, team_name,
                desired_user_ids, desired_repo_ids,
                current_user_ids, current_repo_ids,
                semgrep_headers, dry_run,
            )
        else:
            create_semgrep_team(
                deployment_id, team_name,
                desired_user_ids, desired_repo_ids,
                semgrep_headers, dry_run,
            )

    logger.info("\nSync complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync GitHub org teams to Semgrep RBAC teams.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
environment variables:
  SEMGREP_APP_TOKEN   Semgrep API token with org-admin access (required)
  GITHUB_TOKEN        GitHub token with read:org scope (required)
  GITHUB_ORG          GitHub organization name (required unless --org is set)
        """,
    )
    parser.add_argument("--org", help="GitHub organization name (overrides GITHUB_ORG env var)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to Semgrep")
    args = parser.parse_args()

    org = args.org or os.environ.get("GITHUB_ORG")
    if not org:
        sys.exit("GitHub org name is required: set GITHUB_ORG or use --org.")

    sync_teams(org, args.dry_run)
