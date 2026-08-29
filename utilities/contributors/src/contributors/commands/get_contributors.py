from datetime import datetime
import logging
import os
import click

from contributors.reporters.contributor_reporters import (
    AzureDevOpsContributorReporter,
    BitbucketContributorReporter,
    GhContributorReporter,
    GlContributorReporter,
)

logger = logging.getLogger(__name__)


@click.group()
def get_contributors():
    pass


@get_contributors.command(name="github")
@click.option(
    "--api-key", help="GitHub API key.", envvar="GITHUB_API_KEY", required=True
)
@click.option(
    "--org-name",
    help="Name of the organization to get contributors for.",
    envvar="GITHUB_ORG_NAME",
    required=True,
)
@click.option(
    "--number-of-days",
    help="Number of days to get contributors for.",
    type=click.INT,
    default=30,
)
@click.option(
    "--output-dir",
    help="Directory to write the contributors to.",
    required=False,
    type=click.Path(exists=True, dir_okay=True),
)
@click.option(
    "--repo-file",
    help="Path to a file containing repository names to filter by, one per line (optional).",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--repositories",
    help="A comma separated list of repositories to get contributors for.",
    required=False,
    type=click.STRING,
)
def github(api_key, org_name, number_of_days, output_dir, repo_file, repositories):
    logger.info(f"Creating contributors report for GitHub organization {org_name}.")
    github_reporter = GhContributorReporter(api_key)
    report = github_reporter.get_report(
        org_name,
        number_of_days,
        __get_repository_filter(repo_file, repositories),
    )
    if output_dir:
        __write_json(report.model_dump_json(indent=2), output_dir, "github")
    logger.info(
        f"Total unique contributors: {report.total_contributor_count} in the last {number_of_days} days."
    )
    logger.info(f"Total unique organization members: {len(report.org_members)}.")
    logger.info(
        f"Total unique organization contributors: {report.org_contributors_count} in the last {number_of_days} days."
    )


@get_contributors.command(name="gitlab")
@click.option(
    "--api-key", help="GitLab API key.", envvar="GITLAB_API_KEY", required=True
)
@click.option(
    "--number-of-days",
    help="Number of days to get contributors for.",
    type=click.INT,
    default=30,
)
@click.option(
    "--output-dir",
    help="Directory to write the contributors to.",
    required=False,
    type=click.Path(exists=True, dir_okay=True),
)
@click.option(
    "--repo-file",
    help="Path to a file containing repository names to filter by, one per line (optional).",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--hostname",
    help="Hostname of the GitLab instance.",
    required=False,
    default="gitlab.com",
)
@click.option(
    "--group",
    help="GitLab group to get contributors for.",
    type=click.STRING,
    envvar="GITLAB_GROUP",
    required=False,
)
@click.option(
    "--repositories",
    help="A comma separated list of repositories to get contributors for.",
    required=False,
    type=click.STRING,
)
def gitlab(
    api_key,
    number_of_days,
    output_dir,
    repo_file,
    hostname,
    group,
    repositories,
):
    logger.info(f"Creating contributors report for GitLab.")
    gitlab_reporter = GlContributorReporter(api_key, hostname)
    report = gitlab_reporter.get_report(
        number_of_days,
        group,
        __get_repository_filter(repo_file, repositories),
    )
    if output_dir:
        __write_json(report.model_dump_json(indent=2), output_dir, "gitlab")
    logger.info(
        f"Total unique contributors: {report.total_contributor_count} in the last {number_of_days} days."
    )


@get_contributors.command(name="bitbucket")
@click.option(
    "--api-key", help="Bitbucket API key.", envvar="BITBUCKET_API_KEY", required=True
)
@click.option(
    "--workspace",
    help="Bitbucket workspace.",
    envvar="BITBUCKET_WORKSPACE",
    required=True,
)
@click.option(
    "--number-of-days",
    help="Number of days to get contributors for.",
    type=click.INT,
    default=30,
)
@click.option(
    "--output-dir",
    help="Directory to write the contributors to.",
    required=False,
    type=click.Path(exists=True, dir_okay=True),
)
@click.option(
    "--repo-file",
    help="Path to a file containing repository names to filter by, one per line (optional).",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--repositories",
    help="A comma separated list of repositories to get contributors for.",
    required=False,
    type=click.STRING,
)
def bitbucket(api_key, workspace, number_of_days, output_dir, repo_file, repositories):
    logger.info(f"Creating contributors report for Bitbucket workspace {workspace}.")
    bitbucket_reporter = BitbucketContributorReporter(api_key, workspace)
    report = bitbucket_reporter.get_report(
        number_of_days, __get_repository_filter(repo_file, repositories)
    )
    if output_dir:
        __write_json(report.model_dump_json(indent=2), output_dir, "bitbucket")
    logger.info(
        f"Total unique contributors: {report.total_contributor_count} in the last {number_of_days} days."
    )


@get_contributors.command(name="azure-devops")
@click.option(
    "--api-key",
    help="Azure DevOps API key.",
    envvar="AZURE_DEVOPS_API_KEY",
    required=True,
)
@click.option(
    "--organization",
    help="Azure DevOps organization.",
    envvar="AZURE_DEVOPS_ORGANIZATION",
    required=True,
)
@click.option(
    "--number-of-days",
    help="Number of days to get contributors for.",
    type=click.INT,
    default=30,
)
@click.option(
    "--output-dir",
    help="Directory to write the contributors to.",
    required=False,
    type=click.Path(exists=True, dir_okay=True),
)
@click.option(
    "--repo-file",
    help="Path to a file containing repository names to filter by, one per line (optional).",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--repositories",
    help="A comma separated list of repositories to get contributors for.",
    required=False,
    type=click.STRING,
)
def azure_devops(
    api_key, organization, number_of_days, output_dir, repo_file, repositories
):
    logger.info(
        f"Creating contributors report for Azure DevOps organization {organization}."
    )
    azure_devops_reporter = AzureDevOpsContributorReporter(api_key, organization)
    report = azure_devops_reporter.get_report(
        number_of_days, __get_repository_filter(repo_file, repositories)
    )
    if output_dir:
        __write_json(report.model_dump_json(indent=2), output_dir, "azure-devops")

    logger.info(
        f"Total unique contributors: {report.total_contributor_count} in the last {number_of_days} days."
    )


def __get_repository_filter(
    repo_file: str | None, repositories: list[str] | None
) -> list[str]:
    repo_names: set[str] = set()
    if repositories:
        repo_names.update([repo.strip() for repo in repositories.split(",")])
    if repo_file:
        try:
            with open(repo_file, "r") as f:
                repo_names.update([line.strip() for line in f.readlines()])
        except FileNotFoundError:
            logger.error(f"Repository file {repo_file} not found.")
            raise click.ClickException(f"Repository file {repo_file} not found.")
    return list(repo_names)


def __write_json(report: str, output_dir: str, filename: str):
    with open(
        os.path.join(
            output_dir,
            f"{filename}-contributors-{datetime.now().strftime('%Y-%m-%d')}.json",
        ),
        "w",
    ) as f:
        f.write(report)
