import logging
import requests
import time
import re
from urllib.parse import quote
from contributors.models.github_models import GhCommit, GhRepository
from contributors.models.bitbucket_models import BbRepository, BbCommit
from contributors.models.azure_devops_models import AdoProject, AdoRepository, AdoCommit
from contributors.models.gitlab_models import GlGroup, GlProject, GlCommit
from typing import Callable, Generator, Optional

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str, headers: dict | None = None):
        self.__base_url = base_url
        self.__session = requests.Session()
        if headers:
            self.__session.headers.update(headers)

    def make_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        retry_func: Callable[[dict], int | None] | None = None,
        json: dict | None = None,
    ):
        for i in range(9):
            try:
                request_url = (
                    url if url.startswith("http") else f"{self.__base_url}{url}"
                )
                response = self.__session.request(
                    method, request_url, params=params, json=json
                )
                response.raise_for_status()
                return response.json(), response.headers
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    return None, e.response.headers
                if not (e.response.status_code >= 500 or e.response.status_code == 429):
                    logger.error(f"Unrecoverable error making requests: {e}")
                    return None, e.response.headers
                logger.warning(f"Error making request: {e}")

                retry_time = None
                if retry_func:
                    retry_time = retry_func(e.response.headers)
                sleep_time = retry_time if retry_time is not None else 2**i
                logger.info(f"Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
        return None, None


class GitHubClient(ApiClient):
    def __init__(self, github_token: str):
        super().__init__(
            "https://api.github.com",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    def __get_next_url(self, link_header: str) -> str | None:
        if not link_header:
            return None
        next_pattern = r'(?<=<)([\S]*)(?=>; rel="next")'
        match = re.search(next_pattern, link_header)
        return match.group(1) if match else None

    def get_member_logins(self, org_name: str) -> Generator[str, None, None]:
        url = f"/orgs/{org_name}/members"
        params = {"per_page": 100}

        while url:
            members_page, headers = self.make_request("GET", url, params)
            if not members_page:
                break

            for member in members_page:
                login = member.get("login", "")
                if login:
                    yield login

            url = self.__get_next_url(headers.get("Link", ""))

    def get_repositories(self, org_name: str) -> Generator[GhRepository, None, None]:
        url = f"/orgs/{org_name}/repos"
        params = {"per_page": 100}

        while url:
            repositories_page, headers = self.make_request("GET", url, params)
            if not repositories_page:
                break

            for repo in repositories_page:
                try:
                    yield GhRepository.model_validate(repo)
                except Exception as e:
                    logger.warning(
                        f"Error validating repository {repo.get('name')}: {e}"
                    )

            url = self.__get_next_url(headers.get("Link", ""))

    def get_commits(
        self, repository: GhRepository, since_date: str, until_date: str
    ) -> Generator[GhCommit, None, None]:
        url = f"/repos/{repository.owner.login}/{repository.name}/commits"
        params = {
            "since": since_date,
            "until": until_date,
            "per_page": 100,
        }

        while url:
            commits_page, headers = self.make_request("GET", url, params)
            if not commits_page:
                break

            for commit in commits_page:
                try:
                    yield GhCommit.model_validate(commit)
                except Exception as e:
                    logger.warning(f"Error validating commit {commit.get('sha')}: {e}")

            url = self.__get_next_url(headers.get("Link", ""))


class GitLabClient(ApiClient):
    def __init__(self, gitlab_token: str, hostname: str):
        super().__init__(
            f"https://{hostname}/api/v4",
            headers={"PRIVATE-TOKEN": f"{gitlab_token}"},
        )

    def get_group(self, group_name: str) -> GlGroup | None:
        response, _ = self.make_request("GET", f"/groups/{quote(group_name)}")
        if not response:
            return None
        return GlGroup.model_validate(response)

    def get_groups(self) -> Generator[GlGroup, None, None]:
        page = 1
        while True:
            response, _ = self.make_request(
                "GET",
                "/groups",
                params={"page": page, "per_page": 100},
            )
            if not response:
                break

            for group in response:
                try:
                    yield GlGroup.model_validate(group)
                except Exception as e:
                    logger.warning(f"Error validating group {group.get('name')}: {e}")

            page += 1

    def get_projects(self, group: GlGroup) -> Generator[GlProject, None, None]:
        page = 1
        while True:
            response, _ = self.make_request(
                "GET",
                f"/groups/{group.id}/projects",
                params={"page": page, "per_page": 100},
            )
            if not response:
                break

            for project in response:
                try:
                    yield GlProject.model_validate(project)
                except Exception as e:
                    logger.warning(
                        f"Error validating project {project.get('name')}: {e}"
                    )

            page += 1

    def get_commits(
        self, project: GlProject, since_date: str
    ) -> Generator[GlCommit, None, None]:
        page = 1
        while True:
            response, _ = self.make_request(
                "GET",
                f"/projects/{project.id}/repository/commits",
                params={"since": since_date, "page": page, "per_page": 100},
            )
            if not response:
                break

            for commit in response:
                try:
                    yield GlCommit.model_validate(commit)
                except Exception as e:
                    logger.warning(f"Error validating commit {commit.get('id')}: {e}")

            page += 1


class BitbucketClient(ApiClient):
    def __init__(self, bitbucket_token: str, bitbucket_workspace: str):
        super().__init__(
            "https://api.bitbucket.org/2.0",
            headers={"Authorization": f"Bearer {bitbucket_token}"},
        )
        self.__workspace = bitbucket_workspace

    def get_repositories(self) -> Generator[BbRepository, None, None]:
        url = f"/repositories/{self.__workspace}"

        while url:
            response, _ = self.make_request(
                "GET", url, retry_func=lambda headers: headers.get("Retry-After", None)
            )
            if not response:
                break

            for repo in response.get("values", []):
                try:
                    yield BbRepository.model_validate(repo)
                except Exception as e:
                    logger.warning(
                        f"Error validating repository {repo.get('name')}: {e}"
                    )

            url = response.get("next", None)

    def get_commits(
        self, repository: BbRepository, since_date: str
    ) -> Generator[BbCommit, None, None]:
        url = f"/repositories/{self.__workspace}/{repository.name}/commits"

        while url:
            response, _ = self.make_request(
                "GET", url, retry_func=lambda headers: headers.get("Retry-After", None)
            )
            if not response:
                break

            for commit in response.get("values", []):
                try:
                    bbCommit = BbCommit.model_validate(commit)
                    if bbCommit.date < since_date:
                        return
                    yield bbCommit
                except Exception as e:
                    logger.warning(
                        f"Error validating commit {commit.get('hash', 'unknown')}: {e}"
                    )

            url = response.get("next", None)


class AzureDevOpsClient(ApiClient):
    def __init__(self, azure_devops_token: str, organization: str):
        super().__init__(
            f"https://dev.azure.com/{organization}",
            headers={"Authorization": f"Bearer {azure_devops_token}"},
        )

    def get_projects(self) -> Generator[AdoProject, None, None]:
        url = f"/_apis/projects"
        params = {"api-version": "7.1", "$top": 100, "stateFilter": "wellFormed"}

        while url:
            response, _ = self.make_request("GET", url, params)
            if not response:
                break

            for project in response.get("value", []):
                try:
                    yield AdoProject.model_validate(project)
                except Exception as e:
                    logger.warning(
                        f"Error validating project {project.get('name')}: {e}"
                    )

            continuation_token = response.get("continuationToken", None)
            if continuation_token:
                params["continuationToken"] = continuation_token
            else:
                break

    def get_repositories(
        self, project: AdoProject
    ) -> Generator[AdoRepository, None, None]:
        url = f"/{project.id}/_apis/git/repositories"
        response, _ = self.make_request("GET", url)

        if not response:
            return

        for repo in response.get("value", []):
            try:
                yield AdoRepository.model_validate(repo)
            except Exception as e:
                logger.warning(f"Error validating repository {repo.get('name')}: {e}")

    def get_commits(
        self,
        repository: AdoRepository,
        project: AdoProject,
        since_date: Optional[str] = None,
    ) -> Generator[AdoCommit, None, None]:
        url = f"/{project.id}/_apis/git/repositories/{repository.id}/commitsbatch"
        params = {"api-version": "7.1", "$top": 100}

        request_body = {}
        if since_date:
            request_body["fromDate"] = since_date

        while True:
            response, _ = self.make_request("POST", url, params, json=request_body)

            if not response:
                break

            for commit in response.get("value", []):
                try:
                    yield AdoCommit.model_validate(commit)
                except Exception as e:
                    logger.warning(
                        f"Error validating commit {commit.get('commitId')}: {e}"
                    )

            if len(response.get("value", [])) < 100:
                break

            params["$skip"] = params.get("$skip", 0) + 100
