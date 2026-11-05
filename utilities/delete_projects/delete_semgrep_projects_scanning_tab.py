"""Delete Semgrep projects whose full name starts with DevExSandbox.

Requires requests. Set SEMGREP_APP_TOKEN or enter it at the hidden prompt.
Example preview: python3 delete_semgrep_project.py my-deployment --dry-run
Example deletion: python3 delete_semgrep_project.py my-deployment
"""

import argparse
import os
import sys
from getpass import getpass
from urllib.parse import quote, urljoin, urlsplit

import requests

PREFIX = "DevExSandbox"
PAGE_SIZE = 100


def collect_projects(session, url):
    """Collect every page before deleting so pagination cannot shift."""
    names = set()
    page = 0
    while True:
        response = session.get(
            url, params={"page_size": PAGE_SIZE, "page": page},
            timeout=30, allow_redirects=False,
        )
        if response.status_code != 200:
            raise ValueError(f"Project listing failed: HTTP {response.status_code} (page {page}).")
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
            raise ValueError("Expected a JSON object containing a projects list.")
        projects = data["projects"]
        if not projects:
            return sorted(names)
        page_names = set()
        for project in projects:
            if not isinstance(project, dict) or not isinstance(project.get("name"), str) or not project["name"]:
                raise ValueError("A project has a missing or invalid name.")
            page_names.add(project["name"])
        if not page_names - names:
            raise ValueError("Pagination returned no new projects. Aborting before deletion.")
        names.update(page_names)
        page += 1


def delete_project(session, url):
    """Follow at most five method-preserving redirects on the same HTTPS origin."""
    for redirect_count in range(6):
        response = session.delete(url, timeout=30, allow_redirects=False)
        if response.status_code not in (307, 308):
            return response
        location = response.headers.get("Location")
        if not location:
            raise ValueError("DELETE redirect has no Location header.")
        target = urljoin(url, location)
        parsed = urlsplit(target)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "semgrep.dev"
            or parsed.port not in (None, 443)
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("DELETE redirect points outside https://semgrep.dev. Inspect its Location header.")
        if redirect_count == 5:
            raise ValueError("DELETE exceeded five redirects. Inspect its Location header.")
        url = target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deployment_slug")
    parser.add_argument("--dry-run", action="store_true", help="List matches without deleting.")
    args = parser.parse_args()
    token = os.environ.get("SEMGREP_APP_TOKEN", "").strip()
    if not token and sys.stdin.isatty():
        token = getpass("Semgrep App token (without Bearer): ").strip()
    if not token or any(char.isspace() for char in token):
        parser.error("Provide the raw token via SEMGREP_APP_TOKEN or the interactive prompt.")

    url = f"https://semgrep.dev/api/v1/deployments/{quote(args.deployment_slug, safe='')}/projects"
    with requests.Session() as session:
        session.headers.update({"Authorization": f"Bearer {token}"})
        try:
            projects = collect_projects(session, url)
        except (requests.RequestException, ValueError) as exc:
            # Request exceptions can contain request details; omit those.
            detail = type(exc).__name__ if isinstance(exc, requests.RequestException) else str(exc)
            print(f"Collection failed: {detail}", file=sys.stderr)
            return 1

        matches = [name for name in projects if name.startswith(PREFIX)]
        print(f"Collected {len(projects)} projects; {len(matches)} match {PREFIX!r}.")
        deleted = 0
        for name in matches:
            if args.dry_run:
                print(f"Would delete: {name}")
                continue
            try:
                response = delete_project(session, f"{url}/{quote(name, safe='')}")
            except (requests.RequestException, ValueError) as exc:
                detail = type(exc).__name__ if isinstance(exc, requests.RequestException) else str(exc)
                print(
                    f"DELETE failed for {name!r}: {detail}. "
                    f"Check its status before retrying. {deleted} deletions confirmed.",
                    file=sys.stderr,
                )
                return 1
            if not 200 <= response.status_code < 300:
                print(
                    f"DELETE failed for {name!r}: HTTP {response.status_code}. "
                    f"{deleted} deletions confirmed.",
                    file=sys.stderr,
                )
                return 1
            deleted += 1
            print(f"Deleted: {name} (HTTP {response.status_code})")
        logging.info(f"Dry run complete: {len(matches)} matches." if args.dry_run else f"Deleted {deleted} projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
