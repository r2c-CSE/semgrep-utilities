#!/usr/bin/env python3

import argparse
import os
import sys
import time
from collections import defaultdict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://semgrep.dev/api"
PAGE_SIZE = 100
OLD_TEAM_PREFIX = "[old]"


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
        allowed_methods=["GET", "POST", "PATCH"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    return session


def get_deployment(session: requests.Session) -> dict:
    url = f"{BASE_URL}/v2/deployments"

    response = session.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    deployments = data.get("deployments", [])

    if not deployments:
        raise RuntimeError(
            "No Semgrep deployments were returned for this token."
        )

    if len(deployments) > 1:
        deployment_list = "\n".join(
            f"  - {deployment['id']}: {deployment.get('name', '')}"
            for deployment in deployments
        )

        raise RuntimeError(
            "The token has access to multiple deployments.\n"
            "Refusing to select one automatically:\n"
            f"{deployment_list}"
        )

    return deployments[0]


def get_all_teams(
    session: requests.Session,
    deployment_id: int,
) -> list[dict]:
    url = (
        f"{BASE_URL}/permissions/v2/deployments/"
        f"{deployment_id}/teams/list"
    )

    teams = []
    cursor = ""

    while True:
        payload = {
            "limit": str(PAGE_SIZE),
            "cursor": cursor,
        }

        response = session.post(
            url,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        page_teams = data.get("teams", [])
        teams.extend(page_teams)

        print(f"Retrieved {len(page_teams)} teams")

        cursor = data.get("cursor", "")

        if not cursor:
            break

    return teams


def filter_teams(teams: list[dict]) -> list[dict]:
    """
    Exclude:

    1. The project default team.
    2. Teams whose names start with "[old]".
    3. All descendants of "[old]" teams.

    Descendants of the default team are NOT automatically excluded.
    """

    teams_by_id = {
        str(team["id"]): team
        for team in teams
    }

    children_by_parent = defaultdict(list)

    for team in teams:
        team_id = str(team["id"])
        parent_id = team.get("parentTeamId")

        if parent_id is None:
            continue

        parent_id = str(parent_id)

        # Some root teams may point to themselves.
        if parent_id == team_id:
            continue

        children_by_parent[parent_id].append(team_id)

    excluded_ids = set()

    #
    # Exclude the default project team itself.
    #

    for team in teams:
        if team.get("isProjectDefault", False):
            team_id = str(team["id"])
            excluded_ids.add(team_id)

            print(
                f"Skipping default team: "
                f"{team.get('name', team_id)}"
            )

    #
    # Find all [old] root teams.
    #

    old_team_ids = set()

    for team in teams:
        team_name = team.get("name", "")

        if team_name.lower().startswith(
            OLD_TEAM_PREFIX.lower()
        ):
            team_id = str(team["id"])
            old_team_ids.add(team_id)

            print(
                f"Skipping old team hierarchy: "
                f"{team_name}"
            )

    #
    # Recursively find descendants of every [old] team.
    #

    stack = list(old_team_ids)

    while stack:
        team_id = stack.pop()

        if team_id in excluded_ids:
            # Still need to traverse its children, so don't continue here.
            pass

        excluded_ids.add(team_id)

        for child_id in children_by_parent.get(team_id, []):
            if child_id not in excluded_ids:
                stack.append(child_id)

    #
    # Show descendants excluded because of their parent.
    #

    descendant_ids = excluded_ids - old_team_ids

    for team_id in sorted(descendant_ids):
        team = teams_by_id.get(team_id)

        if not team:
            continue

        # Avoid reporting the default team here unless it is actually
        # below an [old] hierarchy.
        if team.get("isProjectDefault", False):
            continue

        print(
            f"Skipping subteam of [old] hierarchy: "
            f"{team.get('name', team_id)}"
        )

    filtered_teams = [
        team
        for team in teams
        if str(team["id"]) not in excluded_ids
    ]

    return filtered_teams


def get_team_repositories(
    session: requests.Session,
    deployment_id: int,
    team_id: str,
) -> list[int]:
    url = (
        f"{BASE_URL}/permissions/v2/deployments/"
        f"{deployment_id}/teams/{team_id}/repos"
    )

    repository_ids = []
    cursor = ""

    while True:
        params = {
            "limit": PAGE_SIZE,
        }

        if cursor:
            params["cursor"] = cursor

        response = session.get(
            url,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        repository_ids.extend(
            data.get("repositoryIds", [])
        )

        cursor = data.get("cursor", "")

        if not cursor:
            break

    return repository_ids


def build_repository_team_mapping(
    session: requests.Session,
    deployment_id: int,
    teams: list[dict],
    tag_field: str,
) -> dict[int, set[str]]:
    repo_teams = defaultdict(set)

    for index, team in enumerate(teams, start=1):
        team_id = team["id"]
        team_name = team.get("name", "")
        team_slug = team.get("slug", "")

        tag = (
            team_name
            if tag_field == "name"
            else team_slug
        )

        if not tag:
            print(
                f"WARNING: Team {team_id} has no "
                f"{tag_field}. Skipping.",
                file=sys.stderr,
            )
            continue

        print(
            f"[{index}/{len(teams)}] "
            f"Reading repositories for team "
            f"'{team_name}' ({team_id})..."
        )

        repository_ids = get_team_repositories(
            session,
            deployment_id,
            team_id,
        )

        print(
            f"    Found {len(repository_ids)} repositories"
        )

        for repo_id in repository_ids:
            repo_teams[repo_id].add(tag)

    return repo_teams


def tag_repository(
    session: requests.Session,
    deployment_id: int,
    repo_id: int,
    tags: set[str],
) -> dict:
    url = (
        f"{BASE_URL}/agent/deployments/"
        f"{deployment_id}/repos/{repo_id}"
    )

    payload = {
        "deploymentId": deployment_id,
        "idOrName": repo_id,
        "tagsChanges": [
            {
                "operation": "ADD_TAGS",
                "tags": sorted(tags),
            }
        ],
    }

    response = session.patch(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Tag Semgrep repositories with the teams "
            "they belong to."
        )
    )

    parser.add_argument(
        "--tag-field",
        choices=["name", "slug"],
        default="name",
        help=(
            "Team property to use as repository tag. "
            "Default: name"
        ),
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually modify repositories. "
            "Without this flag the script performs a dry run."
        ),
    )

    args = parser.parse_args()

    token = os.getenv("SEMGREP_APP_TOKEN")

    if not token:
        print(
            "ERROR: SEMGREP_APP_TOKEN environment "
            "variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    session = create_session(token)

    try:
        #
        # Step 1 - Deployment
        #

        print("Retrieving deployment...")

        deployment = get_deployment(session)

        deployment_id = deployment["id"]
        deployment_name = deployment.get("name", "")

        print()
        print("======================================")
        print(" Semgrep Team -> Repository Tag Sync")
        print("======================================")
        print()
        print(
            f"Deployment: {deployment_name} "
            f"({deployment_id})"
        )
        print(f"Tag source: {args.tag_field}")
        print(
            f"Mode: "
            f"{'APPLY' if args.apply else 'DRY RUN'}"
        )
        print()

        #
        # Step 2 - Teams
        #

        print("Retrieving teams...")

        all_teams = get_all_teams(
            session,
            deployment_id,
        )

        print()
        print(
            f"Found {len(all_teams)} teams before filtering."
        )
        print()

        #
        # Step 3 - Filter teams
        #

        teams = filter_teams(all_teams)

        print()
        print(
            f"{len(teams)} teams remain after filtering."
        )
        print(
            f"{len(all_teams) - len(teams)} teams excluded."
        )
        print()

        #
        # Step 4 - Build repository -> teams mapping
        #

        repo_teams = build_repository_team_mapping(
            session,
            deployment_id,
            teams,
            args.tag_field,
        )

        print()
        print(
            f"Found {len(repo_teams)} repositories "
            "associated with at least one relevant team."
        )
        print()

        #
        # Step 5 - Proposed changes
        #

        print("Repository -> tags")
        print("------------------")

        for repo_id in sorted(repo_teams):
            tags = sorted(repo_teams[repo_id])

            print(
                f"{repo_id}: {', '.join(tags)}"
            )

        if not args.apply:
            print()
            print(
                "DRY RUN - no repositories were modified."
            )
            print()
            print(
                "Run again with --apply to add the tags:"
            )
            print()
            print(
                "  python3 semgrep_team_tags.py --apply"
            )
            return

        #
        # Step 6 - Apply
        #

        print()
        print("Applying tags...")
        print()

        successful = 0
        failed = 0
        total = len(repo_teams)

        for index, (repo_id, tags) in enumerate(
            sorted(repo_teams.items()),
            start=1,
        ):
            print(
                f"[{index}/{total}] "
                f"Repository {repo_id}: "
                f"{', '.join(sorted(tags))}"
            )

            try:
                result = tag_repository(
                    session,
                    deployment_id,
                    repo_id,
                    tags,
                )

                repo = result.get("repo", {})

                print(
                    f"    OK: "
                    f"{repo.get('name', repo_id)}"
                )

                successful += 1

            except requests.HTTPError as exc:
                failed += 1

                print(
                    f"    ERROR: {exc}",
                    file=sys.stderr,
                )

                if exc.response is not None:
                    print(
                        f"    Response: "
                        f"{exc.response.text}",
                        file=sys.stderr,
                    )

            time.sleep(0.05)

        print()
        print("======================================")
        print(" Finished")
        print("======================================")
        print(f"Successful: {successful}")
        print(f"Failed:     {failed}")

    except requests.HTTPError as exc:
        print(
            f"ERROR: Semgrep API request failed: {exc}",
            file=sys.stderr,
        )

        if exc.response is not None:
            print(
                f"Response: {exc.response.text}",
                file=sys.stderr,
            )

        sys.exit(1)

    except RuntimeError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
