"""
GitHub Recent Contributors Script - Enhanced for Licensing Reporting
---------------------------------------------------------------------
This script provides detailed contributor analysis for GitHub organizations,
specifically designed for licensing audits and usage reporting.

Features:
- Detailed per-repository contributor breakdowns
- Per-contributor activity metrics (commit counts, date ranges, repositories)
- Distinction between org members and external contributors
- Comprehensive JSON output for licensing compliance
- Support for analyzing all repos or specific subsets

Output includes:
- Which contributors worked on which repositories
- How many commits each contributor made
- First and last commit dates for each contributor per repository
- Clear identification of org members requiring licenses
- Summary statistics for quick overview

Directions:
1. Install the required Python library: `pip3 install requests`
2. Export your GitHub Personal Access Token:
   export GITHUB_PERSONAL_ACCESS_TOKEN='your_token_here'
3. Run the script:

   # Analyze all repos for 90 days
   python3 github_recent_contributors.py MyOrg 90 report.json

   # Analyze specific repos only
   python3 github_recent_contributors.py MyOrg 90 report.json --repos repo1 repo2 repo3

Requirements:
- Python 3.x
- A GitHub Personal Access Token

GitHub Permissions Needed:
- repo (or public_repo for public repositories)
- read:org
- read:user
- user:email (optional, but recommended)

JSON Output Structure:
- report_metadata: Report date, organization, analysis period
- summary: Aggregate counts and totals
- licensing_counts: List of org members requiring licenses
- contributors_by_type: Detailed breakdown of org members vs external contributors
- repository_details: Per-repository contributor lists with commit counts
- detailed_contributor_list: Per-contributor summary across all repositories

Note:
- Keep your tokens secure and never expose them in client-side code or public repositories.
"""
import requests
import os
from datetime import datetime, timedelta, timezone, UTC
import argparse
import json


def get_repos(org_name, headers):
    """Fetch all repositories for the given organization."""
    repos = []
    page = 1  # Start from page 1

    while True:
        response = requests.get(
            f'https://api.github.com/orgs/{org_name}/repos',
            headers=headers,
            params={'per_page': 100, 'page': page}  # Fetch 100 repos per page
        )

        if response.status_code != 200:
            error_msg = f"Error fetching repositories for organization {org_name}. Status code: {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f"\nGitHub API response: {error_details.get('message', 'No message')}"
                if 'documentation_url' in error_details:
                    error_msg += f"\nDocs: {error_details['documentation_url']}"
            except:
                error_msg += f"\nResponse: {response.text}"
            raise ValueError(error_msg)

        data = response.json()
        
        if not data:  # If no more repositories, break the loop
            break
        repos.extend(data)  # Add fetched repos to the list
        page += 1  # Move to the next page

    return repos


def get_organization_members(org_name, headers):
    """Fetch all members of the organization."""
    members = []
    page = 1
    while True:
        response = requests.get(
            f'https://api.github.com/orgs/{org_name}/members?page={page}',
            headers=headers
        )
        if response.status_code != 200:
            break
        members_page = response.json()
        if not members_page:
            break
        members.extend(members_page)
        page += 1
    return {member['login'] for member in members}

def get_contributors(org_name, number_of_days, headers):
    # init contributor set
    unique_contributors = set()
    unique_authors = set()

    # Enhanced tracking structures
    repo_details = {}  # Per-repository contributor details
    contributor_details = {}  # Per-contributor details across repos

    if not repo_list:
        print("No repo names provided. Will count contributors to all repos in the org [" + org_name + "]")

    # Fetch all repositories in the organization
    repos = get_repos(org_name, headers)
    print(f"Number of repos = {len(repos)}")

    # Date range calculation
    since_date = (datetime.now(timezone.utc) - timedelta(days=number_of_days)).isoformat()
    until_date = datetime.now(UTC).isoformat()

    # Loop through each repository in the organization
    for repo in repos:
        owner = repo['owner']['login']
        repo_name = repo['name']

        if repo_list:
            if repo_name in repo_list:
                print(f"Processing repo: {repo_name}")
            else:
                #print(f"skipping: {repo_name}")
                continue

        # Fetch commits for each repository in the given date range
        response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo_name}/commits',
            params={'since': since_date, 'until': until_date},
            headers=headers
        )

        commits = response.json()

        if isinstance(commits, list):
            # Initialize repo tracking
            repo_contributors = {}

            for commit in commits:
                author_name = commit['commit']['author']['name']
                author_login = commit['author']['login'] if commit['author'] else None
                commit_date = commit['commit']['author']['date']

                unique_contributors.add(author_name)

                if author_login:
                    unique_authors.add(author_login)

                    # Track per-repository contributors
                    if author_login not in repo_contributors:
                        repo_contributors[author_login] = {
                            'login': author_login,
                            'name': author_name,
                            'commit_count': 0,
                            'first_commit_date': commit_date,
                            'last_commit_date': commit_date
                        }
                    repo_contributors[author_login]['commit_count'] += 1

                    # Update date range
                    if commit_date < repo_contributors[author_login]['first_commit_date']:
                        repo_contributors[author_login]['first_commit_date'] = commit_date
                    if commit_date > repo_contributors[author_login]['last_commit_date']:
                        repo_contributors[author_login]['last_commit_date'] = commit_date

                    # Track per-contributor activity across repos
                    if author_login not in contributor_details:
                        contributor_details[author_login] = {
                            'login': author_login,
                            'name': author_name,
                            'total_commits': 0,
                            'repositories': []
                        }
                    contributor_details[author_login]['total_commits'] += 1

            # Store repo details if there were commits
            if repo_contributors:
                repo_details[repo_name] = {
                    'repository': repo_name,
                    'contributor_count': len(repo_contributors),
                    'total_commits': sum(c['commit_count'] for c in repo_contributors.values()),
                    'contributors': list(repo_contributors.values())
                }

                # Update contributor details with repo information
                for login, details in repo_contributors.items():
                    contributor_details[login]['repositories'].append({
                        'repository': repo_name,
                        'commit_count': details['commit_count'],
                        'first_commit_date': details['first_commit_date'],
                        'last_commit_date': details['last_commit_date']
                    })
        else:
            print(f"Repo: {repo_name} is empty.")

    return unique_contributors, unique_authors, repo_details, contributor_details

def report_contributors(org_name, number_of_days, output_file):
    # init github auth
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        raise ValueError("Please set your GITHUB_PERSONAL_ACCESS_TOKEN as an environment variable.")
    headers = {'Authorization': f'token {token}'}

    org_members = get_organization_members(org_name, headers)
    unique_contributors, unique_authors, repo_details, contributor_details = get_contributors(org_name, number_of_days, headers)

    # Calculate member status for each contributor
    committing_members = unique_authors & org_members
    external_contributors = unique_authors - org_members

    # Enhance contributor details with org membership info
    for login, details in contributor_details.items():
        details['is_org_member'] = login in org_members
        details['contributor_type'] = 'org_member' if login in org_members else 'external'
        # Sort repositories by commit count (descending)
        details['repositories'].sort(key=lambda x: x['commit_count'], reverse=True)

    if output_file:
        output_data = {
            "report_metadata": {
                "organization": org_name,
                "report_date": datetime.today().date().strftime('%Y-%m-%d'),
                "analysis_period_days": number_of_days,
                "date_range": {
                    "from": (datetime.now(timezone.utc) - timedelta(days=number_of_days)).strftime('%Y-%m-%d'),
                    "to": datetime.now(timezone.utc).strftime('%Y-%m-%d')
                }
            },
            "summary": {
                "total_repositories_analyzed": len(repo_details),
                "total_commit_authors": len(unique_authors),
                "total_org_members": len(org_members),
                "committing_org_members": len(committing_members),
                "external_contributors": len(external_contributors),
                "total_commits": sum(r['total_commits'] for r in repo_details.values())
            },
            "licensing_counts": {
                "org_members_requiring_licenses": list(committing_members),
                "count": len(committing_members)
            },
            "contributors_by_type": {
                "org_members": [
                    contributor_details[login] for login in committing_members
                ],
                "external_contributors": [
                    contributor_details[login] for login in external_contributors
                ]
            },
            "repository_details": list(repo_details.values()),
            "detailed_contributor_list": sorted(
                contributor_details.values(),
                key=lambda x: x['total_commits'],
                reverse=True
            )
        }

        with open(output_file, 'w') as file:
            json.dump(output_data, file, indent=2)

        print(f"\n✓ Detailed report saved to: {output_file}")

    # Print summary statistics
    print(f"\n{'='*60}")
    print(f"LICENSING REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"Organization: {org_name}")
    print(f"Period: Last {number_of_days} days")
    print(f"Repositories analyzed: {len(repo_details)}")
    print(f"\n{'='*60}")
    print(f"CONTRIBUTOR COUNTS")
    print(f"{'='*60}")
    print(f"Total commit authors: {len(unique_authors)}")
    print(f"  ├─ Org members who committed: {len(committing_members)}")
    print(f"  └─ External contributors: {len(external_contributors)}")
    print(f"\nTotal org members: {len(org_members)}")
    print(f"  └─ Requiring licenses (committed): {len(committing_members)}")

    # Show top contributors
    print(f"\n{'='*60}")
    print(f"TOP 10 CONTRIBUTORS (by commit count)")
    print(f"{'='*60}")
    sorted_contributors = sorted(
        contributor_details.values(),
        key=lambda x: x['total_commits'],
        reverse=True
    )
    for i, contrib in enumerate(sorted_contributors[:10], 1):
        member_badge = "✓ ORG" if contrib['is_org_member'] else "  EXT"
        print(f"{i:2}. [{member_badge}] {contrib['login']:20} - {contrib['total_commits']:4} commits across {len(contrib['repositories'])} repos")

    print(f"\n{'='*60}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Get unique contributors from a GitHub organization.",
        usage="%(prog)s ORG_NAME NUMBER_OF_DAYS OUTPUT_FILENAME [--repos REPO1 REPO2 ...]"
    )
    parser.add_argument("org_name", help="The name of the GitHub organization.")
    parser.add_argument("number_of_days", type=int, help="Number of days to look over.")
    parser.add_argument("output_filename", help="A file to log output.")
    parser.add_argument("--repos", nargs="+", help="List of repo names (optional). If omitted, all repos will be considered.")
    args = parser.parse_args()

    repo_list = args.repos if args.repos else []
    if repo_list:
        print(f"repo_list: {repo_list}")
    report_contributors(args.org_name, args.number_of_days, args.output_filename)
