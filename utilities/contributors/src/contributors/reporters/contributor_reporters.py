from collections import defaultdict
from datetime import UTC, datetime, timedelta, timezone
from contributors.clients.api_client import (
    AzureDevOpsClient,
    BitbucketClient,
    GitHubClient,
    GitLabClient,
)
from contributors.models.reports import (
    AdoReport,
    BbReport,
    GhReport,
    GlReport,
    RepositoryStats,
)
from contributors.models.gitlab_models import GlGroup
import logging

logger = logging.getLogger(__name__)


class GhContributorReporter:
    def __init__(self, api_key: str):
        self.__github_client = GitHubClient(api_key)

    def get_report(
        self,
        org_name: str,
        number_of_days: int,
        repo_filter: list[str] | None = None,
    ):
        members = set(self.__github_client.get_member_logins(org_name))
        until_date = datetime.now(UTC).isoformat()
        since_date = (datetime.now(UTC) - timedelta(days=number_of_days)).isoformat()

        unique_contributors = set()
        unique_authors = set()

        repo_stats: list[RepositoryStats] = []
        for repository in self.__github_client.get_repositories(org_name):
            if is_repository_filtered(repo_filter, repository.name):
                logger.debug(f"Skipping repository: {repository.name}")
                continue

            logger.debug(f"Processing repository: {repository.name}")
            for commit in self.__github_client.get_commits(
                repository, since_date, until_date
            ):
                unique_contributors.add(commit.commit.author.name)
                if commit.author:
                    unique_authors.add(commit.author.login)

            repo_stats.append(
                RepositoryStats(
                    name=repository.name,
                    contributor_count=len(unique_authors & members),
                    contributors=list(unique_authors & members),
                )
            )

            logger.debug(
                f"Repository: {repository.name} - Contributors: {len(unique_authors)}"
            )
            logger.debug(
                f"Contributors for {repository.name}: {', '.join(unique_authors)}"
            )

        return GhReport(
            organization=org_name,
            date=datetime.today().date().strftime("%Y-%m-%d"),
            number_of_days_history=number_of_days,
            total_contributor_count=len(unique_authors),
            total_repository_count=len(repo_stats),
            repository_stats=repo_stats,
            org_members=sorted(list(members)),
            org_contributors=sorted(list(unique_authors & members)),
            org_contributors_count=len(unique_authors & members),
        )


class GlContributorReporter:
    def __init__(self, api_key: str, hostname: str):
        self.__gitlab_client = GitLabClient(api_key, hostname)

    def get_report(
        self,
        number_of_days: int,
        group: str | None = None,
        repo_filter: list[str] | None = None,
    ):
        all_contributors = set()
        repo_contributors = defaultdict(set)
        since_date = (datetime.now(UTC) - timedelta(days=number_of_days)).isoformat()

        self.__process_groups(
            group, since_date, all_contributors, repo_contributors, repo_filter
        )

        return GlReport(
            date=datetime.today().date().strftime("%Y-%m-%d"),
            number_of_days_history=number_of_days,
            total_contributor_count=len(all_contributors),
            total_repository_count=len(repo_contributors),
            repository_stats=[
                RepositoryStats(
                    name=repo,
                    contributor_count=len(contributors),
                    contributors=list(contributors),
                )
                for repo, contributors in repo_contributors.items()
            ],
            all_contributors=sorted(list(all_contributors)),
        )

    def __process_groups(
        self,
        group_name: str | None,
        since_date: str,
        all_contributors: set,
        repo_contributors: dict,
        repo_filter: list[str] | None = None,
    ):
        if group_name:
            group = self.__gitlab_client.get_group(group_name)
            if not group:
                logger.warning(f"Group {group_name} not found.")
                return
            self.__process_single_group(
                group, since_date, all_contributors, repo_contributors, repo_filter
            )
        else:
            for group in self.__gitlab_client.get_groups():
                self.__process_single_group(
                    group, since_date, all_contributors, repo_contributors, repo_filter
                )

    def __process_single_group(
        self,
        group: GlGroup,
        since_date: str,
        all_contributors: set,
        repo_contributors: dict,
        repo_filter: list[str] | None = None,
    ):
        for project in self.__gitlab_client.get_projects(group):
            if is_repository_filtered(repo_filter, project.path_with_namespace):
                logger.debug(f"Skipping repository: {project.path_with_namespace}")
                continue

            for commit in self.__gitlab_client.get_commits(project, since_date):
                all_contributors.add(commit.author_name)
                repo_contributors[project.path_with_namespace].add(commit.author_name)

            logger.debug(
                f"Repository: {project.path_with_namespace} - Contributors: {len(repo_contributors[project.path_with_namespace])}"
            )
            logger.debug(
                f"Contributors for {project.path_with_namespace}: {', '.join(repo_contributors[project.path_with_namespace])}"
            )


class BitbucketContributorReporter:
    def __init__(self, api_key: str, workspace: str):
        self.__bitbucket_client = BitbucketClient(api_key, workspace)
        self.__workspace = workspace

    def get_report(
        self,
        number_of_days: int,
        repo_filter: list[str] | None = None,
    ):
        since_date = (datetime.now() - timedelta(days=number_of_days)).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )

        all_contributors = set()
        repo_stats: list[RepositoryStats] = []

        for repository in self.__bitbucket_client.get_repositories():
            if is_repository_filtered(repo_filter, repository.name):
                logger.debug(f"Skipping repository: {repository.name}")
                continue

            commit_count = 0
            authors = set()
            for commit in self.__bitbucket_client.get_commits(repository, since_date):
                commit_count += 1
                author = (
                    commit.author.user.display_name
                    if commit.author.user
                    else commit.author.raw
                )
                authors.add(author)

            logger.debug(
                f"Found {commit_count} total commits from {len(authors)} unique authors in {repository.name}."
            )

            all_contributors.update(authors)
            repo_stats.append(
                RepositoryStats(
                    name=repository.name,
                    contributor_count=len(authors),
                    contributors=list(authors),
                )
            )

        return BbReport(
            workspace=self.__workspace,
            date=datetime.today().date().strftime("%Y-%m-%d"),
            number_of_days_history=number_of_days,
            total_contributor_count=len(all_contributors),
            total_repository_count=len(repo_stats),
            repository_stats=repo_stats,
            all_contributors=sorted(list(all_contributors)),
        )


class AzureDevOpsContributorReporter:
    def __init__(self, api_key: str, organization: str):
        self.__azure_devops_client = AzureDevOpsClient(api_key, organization)
        self.__organization = organization

    def get_report(
        self,
        number_of_days: int,
        repo_filter: list[str] | None = None,
    ):
        since_date = (
            datetime.now(timezone.utc) - timedelta(days=number_of_days)
        ).isoformat()

        all_contributors = set()
        repo_stats: list[RepositoryStats] = []

        for project in self.__azure_devops_client.get_projects():
            for repository in self.__azure_devops_client.get_repositories(project):
                if is_repository_filtered(repo_filter, repository.name):
                    logger.debug(f"Skipping repository: {repository.name}")
                    continue

                commit_count = 0
                authors = set()

                for commit in self.__azure_devops_client.get_commits(
                    repository, project, since_date
                ):
                    commit_count += 1
                    if commit.author.email:
                        authors.add(commit.author.email.lower())

                logger.debug(
                    f"Found {commit_count} total commits from {len(authors)} unique authors in {repository.name}."
                )

                all_contributors.update(authors)
                repo_stats.append(
                    RepositoryStats(
                        name=repository.name,
                        contributor_count=len(authors),
                        contributors=list(authors),
                    )
                )

        return AdoReport(
            organization=self.__organization,
            date=datetime.today().date().strftime("%Y-%m-%d"),
            number_of_days_history=number_of_days,
            total_contributor_count=len(all_contributors),
            total_repository_count=len(repo_stats),
            repository_stats=repo_stats,
            all_contributor_emails=sorted(list(all_contributors)),
        )


def is_repository_filtered(repo_filter: list[str] | None, repository: str) -> bool:
    return repo_filter and repository not in repo_filter
