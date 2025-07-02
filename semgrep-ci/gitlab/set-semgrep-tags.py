"""
This is an example script demonstrating how to automatically set tags on a Semgrep project
from a GitLab pipeline. It's intended to be modified for your specific use case rather than
run as-is. The script itself is a sample and not a supported Semgrep product.

Example minimal pipeline configuration:

  semgrep-tags:
  image: python
  script:
      - pip install requests
      - python set-semgrep-tags.py

It also requires an API-scoped SEMGREP_API_TOKEN in CI/CD variables, which you can create here:

  https://semgrep.dev/orgs/-/settings/tokens

Note that this is different from the CI-scoped token you need to run Semgrep itself.

As written, this script tries to use the repository name or URL to find a matching Semgrep project.
If it succeeds, it adds tags to that project for each group in the GitLab project path between
the top-level namespace and the project name itself. For example, if the GitLab project is:

  my-org/appsec-team/infrastructure/test-environments

Then this script would apply the tags `appsec-team` and `infrastructure` to a Semgrep project
named `my-org/appsec-team/infrastructure/test-environments`.

See the docstrings below for details about how to customize this behavior, including using a
different source for tags, removing disallowed tags, or searching more robustly for the
matching Semgrep project.
"""

import json
import os
import requests

# Set this API-scoped Semgrep token as an environment secret in CI
SEMGREP_API_TOKEN = os.environ['SEMGREP_API_TOKEN']
# Leave this as-is unless you know you need to change it
SEMGREP_API_BASE_URL = "https://semgrep.dev/api/v1"


def semgrep_api(endpoint, method=requests.get, payload=None):
    """
    Call a Semgrep API endpoint with the given method and payload.

    API reference: https://semgrep.dev/api/v1/docs
    """
    response = method(
        SEMGREP_API_BASE_URL + endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SEMGREP_API_TOKEN}"
        },
        data = json.dumps(payload) if payload else None
    )
    response.raise_for_status()
    return response.json()

def get_project_endpoint(deployment):
    """
    Try to match a Semgrep API endpoint to the current GitLab project.

    First checks whether the GitLab path is the name of a Semgrep project we can see.
    If not, iterates through the first page of results from the list projects API
    looking for a match by remote URL. Failing that, gives up and raises Exception.
    """
    all_projects_endpoint = f"/deployments/{deployment['slug']}/projects"
    project_name = os.environ.get("CI_PROJECT_PATH", "")
    try:
        semgrep_api(f"{all_projects_endpoint}/{project_name}")
    except requests.exceptions.HTTPError:
        # If you have more than 100 projects, you'd need to iterate through pages of
        # results here, or get the project name a different way entirely.
        all_projects = semgrep_api(all_projects_endpoint)["projects"]
        try:
            project_name = next(p["name"] for p in all_projects if p["url"] == os.environ["CI_PROJECT_URL"])
        except (KeyError, StopIteration):
            raise Exception("Couldn't find project by path or URL. Does it exist in Semgrep yet?")
    return f"{all_projects_endpoint}/{project_name}"

def update_project_tags(project_endpoint, tags_to_add, tags_to_remove):
    """
    Adds and removes the specified tags from a Semgrep project.

    Returns the project object from the last API response, after both updates.
    """
    endpoint = project_endpoint + "/tags"
    for method, tags in [(requests.put, tags_to_add), (requests.delete, tags_to_remove)]:
        result = semgrep_api(
            endpoint,
            method = method,
            payload = { "tags": tags }
        )
    return result["project"]

def get_tags_to_add():
    """
    Determine what tags this project should have and return them as a list.

    This example splits the GitLab project path into groups and returns everything
    between the top-level namespace and the current project name. You could use any
    other metadata from GitLab instead, or call an external API, or reference a
    static file.
    """
    project_path = os.environ.get("CI_PROJECT_PATH")
    if project_path is None:
        return []
    return project_path.split("/")[1:-1]

def get_tags_to_remove(current_tags):
    """
    Determine what tags this project should NOT have and return them as a list.

    This placeholder always returns an empty list, so that running the example
    script won't destroy any live data. Here's a real use case though:

    allowlist = ["dev", "stage", "prod", "managed-scan"]
    ok_tags = get_tags_to_add() + allowlist
    return [t for t in current_tags if t not in ok_tags]
    """
    return []

def main():
    """
    Update this project's tags in Semgrep.
    """
    deployment = semgrep_api("/deployments")["deployments"][0]
    project_endpoint = get_project_endpoint(deployment)
    current_tags = semgrep_api(project_endpoint)["project"]["tags"]
    print(f"Current tags: {current_tags}")
    updated_tags = update_project_tags(
        project_endpoint,
        get_tags_to_add(),
        get_tags_to_remove(current_tags)
    )["tags"]
    print(f"Tags after update: {updated_tags}")

if __name__ == "__main__":
    main()
