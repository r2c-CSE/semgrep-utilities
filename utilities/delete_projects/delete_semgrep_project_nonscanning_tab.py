import argparse
import os
import sys
from getpass import getpass

import requests


API_BASE_URL = "https://semgrep.dev/api/agent/deployments"
REQUEST_TIMEOUT = 30
REPOSITORY_PAGE_LIMIT = 1000


def get_token(parser):
    token = os.environ.get("SEMGREP_JWT", "").strip()
    if not token and sys.stdin.isatty():
        token = getpass("Semgrep JWT (without Bearer): ").strip()
    if not token or any(char.isspace() for char in token):
        parser.error("Provide the raw JWT via SEMGREP_JWT or the interactive prompt.")
    return token


def fetch_repositories(deployment_id, token):
    url = f"{API_BASE_URL}/{deployment_id}/repos/search"
    repositories = []
    cursor = ""
    seen_cursors = set()
    page_number = 0

    while True:
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "cursor": cursor,
                    "limit": REPOSITORY_PAGE_LIMIT,
                    "filters": {"search": "", "setup": False, "archived": False},
                },
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            print(
                f"Request failed ({type(exc).__name__}) while fetching repository "
                f"page {page_number + 1}. Check deployment status before retrying.",
                file=sys.stderr,
            )
            return None

        if not 200 <= response.status_code < 300:
            print(
                f"Repository search page {page_number + 1} failed: "
                f"HTTP {response.status_code}.",
                file=sys.stderr,
            )
            return None

        try:
            page = response.json()
        except ValueError:
            print(
                f"Repository search page {page_number + 1} returned invalid JSON.",
                file=sys.stderr,
            )
            return None

        if not isinstance(page, dict):
            print(
                f"Repository search page {page_number + 1} returned an unexpected "
                "response shape.",
                file=sys.stderr,
            )
            return None

        page_repositories = page.get("repos")
        next_cursor = page.get("cursor")
        if not isinstance(page_repositories, list) or not all(
            isinstance(repository, dict) for repository in page_repositories
        ):
            print(
                f"Repository search page {page_number + 1} returned an unexpected "
                "response shape.",
                file=sys.stderr,
            )
            return None
        if next_cursor is not None and not isinstance(next_cursor, str):
            print(
                f"Repository search page {page_number + 1} returned an invalid cursor.",
                file=sys.stderr,
            )
            return None

        repositories.extend(page_repositories)
        page_number += 1
        if not next_cursor:
            if len(page_repositories) >= REPOSITORY_PAGE_LIMIT:
                print(
                    "Repository search returned a full page without a next cursor; "
                    "cannot confirm that all repositories were fetched.",
                    file=sys.stderr,
                )
                return None
            break
        if next_cursor in seen_cursors or next_cursor == cursor:
            print(
                "Repository search returned a repeated cursor; stopping to avoid "
                "reprocessing the same page.",
                file=sys.stderr,
            )
            return None

        seen_cursors.add(next_cursor)
        cursor = next_cursor

    print(f"Fetched {len(repositories)} repositories across {page_number} page(s).")
    return repositories


def delete_repository(deployment_id, project_id, token):
    url = f"{API_BASE_URL}/{deployment_id}/repos/{project_id}"
    try:
        response = requests.delete(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        print(
            f"DELETE for project {project_id} failed ({type(exc).__name__}). "
            "Check project status before retrying.",
            file=sys.stderr,
        )
        return False

    if not 200 <= response.status_code < 300:
        print(
            f"DELETE for project {project_id} failed: HTTP {response.status_code}.",
            file=sys.stderr,
        )
        return False

    print(f"DELETE for project {project_id} returned HTTP {response.status_code}.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Find disconnected Semgrep repositories named DevExSandbox* "
            "and optionally delete them."
        )
    )
    parser.add_argument("deployment_id", type=int)
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete matching repositories (default: preview only).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt; requires --delete.",
    )
    args = parser.parse_args()

    if args.yes and not args.delete:
        parser.error("--yes can only be used with --delete.")
    if args.delete and not args.yes and not sys.stdin.isatty():
        parser.error("Use --yes with --delete when running non-interactively.")

    token = get_token(parser)
    repositories = fetch_repositories(args.deployment_id, token)
    if repositories is None:
        return 1

    projects_to_delete = []
    for repository in repositories:
        name = repository.get("name", "<unnamed>")
        starts_with_sandbox_prefix = (
            isinstance(name, str) and name.startswith("DevExSandbox")
        )
        if (
            repository.get("isDisconnected") is not True
            or not starts_with_sandbox_prefix
        ):
            continue
        project_id = repository.get("id")
        if (
            isinstance(project_id, bool)
            or not isinstance(project_id, (int, str))
            or not str(project_id).isdecimal()
        ):
            print(
                f"Matching repository has an invalid ID: {name}.",
                file=sys.stderr,
            )
            return 1
        projects_to_delete.append((str(project_id), name))

    print(f"Found {len(projects_to_delete)} repository/repositories to delete.")
    if not args.delete:
        for project_id, name in projects_to_delete:
            print(f"Would delete project {project_id} ({name}).")
        print("Preview only. Re-run with --delete to delete these repositories.")
        return 0

    if not projects_to_delete:
        return 0

    if not args.yes:
        try:
            confirmation = input(
                f"Delete all {len(projects_to_delete)} matching repositories? [y/N]: "
            )
        except EOFError:
            confirmation = ""
        if confirmation.strip().lower() not in ("y", "yes"):
            print("Deletion canceled.")
            return 0

    failures = 0
    for project_id, name in projects_to_delete:
        print(f"Deleting project {project_id} ({name}).")
        if not delete_repository(args.deployment_id, project_id, token):
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
