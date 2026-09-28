# github_recent_contributors.py

A comprehensive GitHub contributor analysis tool designed for licensing audits and usage reporting. This script provides detailed insights into contributor activity across GitHub organizations, helping you understand who has committed code, when, and where.

## Features

### Detailed Contributor Analysis
- **Per-repository contributor breakdowns** - See who contributed to each repo
- **Per-contributor activity metrics** - Track commits, date ranges, and repositories per contributor
- **Org member vs external contributor distinction** - Identify who requires licenses
- **Comprehensive JSON output** - Full data export for compliance and reporting
- **Flexible repository filtering** - Analyze all repos or specific subsets

### Output Includes
- Which contributors worked on which repositories
- Commit counts per contributor per repository
- First and last commit dates for each contributor in each repository
- Clear identification of org members requiring licenses
- Summary statistics for quick overview
- Top contributors ranked by commit count

## Requirements

- Python 3.x
- `requests` library: `pip3 install requests`
- GitHub Personal Access Token with appropriate permissions

### GitHub Token Permissions

Your Personal Access Token needs the following scopes:
- `repo` (or `public_repo` for public repositories only)
- `read:org`
- `read:user`
- `user:email` (optional, but recommended)

## Installation

1. Install the required Python library:
   ```bash
   pip3 install requests
   ```

2. Create a GitHub Personal Access Token at https://github.com/settings/tokens

3. Export your token as an environment variable:
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN='your_token_here'
   ```

## Usage

### Analyze All Repositories

```bash
python3 github_recent_contributors.py MyOrg 90 report.json
```

This analyzes all repositories in the organization for the last 90 days.

### Analyze Specific Repositories

```bash
python3 github_recent_contributors.py MyOrg 90 report.json --repos repo1 repo2 repo3
```

This analyzes only the specified repositories.

### Command-Line Arguments

- `org_name` - The name of the GitHub organization (required)
- `number_of_days` - Number of days to look back for commits (required)
- `output_filename` - Path to save the JSON report (required)
- `--repos` - Space-separated list of repository names to analyze (optional)

## Output Format

### Console Output

The script prints a detailed summary to the console:

```
============================================================
LICENSING REPORT SUMMARY
============================================================
Organization: MyOrg
Period: Last 90 days
Repositories analyzed: 45

============================================================
CONTRIBUTOR COUNTS
============================================================
Total commit authors: 23
  ├─ Org members who committed: 18
  └─ External contributors: 5

Total org members: 25
  └─ Requiring licenses (committed): 18

============================================================
TOP 10 CONTRIBUTORS (by commit count)
============================================================
 1. [✓ ORG] alice              - 245 commits across 12 repos
 2. [✓ ORG] bob                - 198 commits across 8 repos
 3. [  EXT] contractor1        - 156 commits across 3 repos
 ...
```

### JSON Output Structure

The JSON file contains comprehensive data with the following structure:

```json
{
  "report_metadata": {
    "organization": "MyOrg",
    "report_date": "2026-04-10",
    "analysis_period_days": 90,
    "date_range": {
      "from": "2026-01-10",
      "to": "2026-04-10"
    }
  },
  "summary": {
    "total_repositories_analyzed": 45,
    "total_commit_authors": 23,
    "total_org_members": 25,
    "committing_org_members": 18,
    "external_contributors": 5,
    "total_commits": 1234
  },
  "licensing_counts": {
    "org_members_requiring_licenses": ["alice", "bob", "charlie", ...],
    "count": 18
  },
  "contributors_by_type": {
    "org_members": [
      {
        "login": "alice",
        "name": "Alice Smith",
        "total_commits": 245,
        "is_org_member": true,
        "contributor_type": "org_member",
        "repositories": [
          {
            "repository": "api-service",
            "commit_count": 89,
            "first_commit_date": "2026-01-15T10:23:45Z",
            "last_commit_date": "2026-04-08T16:42:12Z"
          }
        ]
      }
    ],
    "external_contributors": [...]
  },
  "repository_details": [
    {
      "repository": "api-service",
      "contributor_count": 8,
      "total_commits": 342,
      "contributors": [
        {
          "login": "alice",
          "name": "Alice Smith",
          "commit_count": 89,
          "first_commit_date": "2026-01-15T10:23:45Z",
          "last_commit_date": "2026-04-08T16:42:12Z"
        }
      ]
    }
  ],
  "detailed_contributor_list": [
    {
      "login": "alice",
      "name": "Alice Smith",
      "total_commits": 245,
      "is_org_member": true,
      "contributor_type": "org_member",
      "repositories": [...]
    }
  ]
}
```

#### Key Sections

**report_metadata**: Report generation details
- Organization name
- Report generation date
- Analysis period
- Exact date range analyzed

**summary**: Aggregate statistics
- Total repositories analyzed
- Total unique commit authors
- Org member counts
- External contributor counts
- Total commits in period

**licensing_counts**: License requirement data
- List of org members who committed code
- Count requiring licenses

**contributors_by_type**: Detailed breakdowns
- Org members with their activity
- External contributors with their activity

**repository_details**: Per-repository information
- Repository name
- Contributor count per repo
- Total commits per repo
- List of contributors with commit counts and date ranges

**detailed_contributor_list**: Per-contributor summary
- Login and name
- Total commits across all repos
- List of repositories they contributed to
- Commit counts per repository
- First and last commit dates per repository
- Organization membership status

## Use Cases

### Licensing Audits
Identify exactly which organization members have committed code and require licenses for tools like Semgrep.

### Activity Tracking
Understand contributor patterns, identify most active contributors, and track repository engagement.

### External Contributor Management
Identify and track external contributors (contractors, open-source contributors, etc.) separately from organization members.

### Compliance Reporting
Generate comprehensive reports for compliance, security, or management review with full commit history and date ranges.

### Budget Planning
Use contributor counts and activity levels to plan tool licensing budgets and resource allocation.

## Security Notes

- Keep your GitHub Personal Access Token secure
- Never commit tokens to version control
- Never expose tokens in client-side code or public repositories
- Use environment variables for token storage
- Rotate tokens regularly
- Use the minimum required token permissions

## Example Workflow

```bash
# Set up environment
export GITHUB_PERSONAL_ACCESS_TOKEN='ghp_xxxxxxxxxxxx'

# Run analysis for last quarter (90 days) on all repos
python3 github_recent_contributors.py acme-corp 90 quarterly-report.json

# Run analysis on specific security-critical repos
python3 github_recent_contributors.py acme-corp 30 security-audit.json \
  --repos auth-service payment-api user-management

# View the JSON report
cat quarterly-report.json | jq '.summary'
```

## Troubleshooting

### "Error fetching repositories for organization"
- Verify your token has `read:org` permission
- Ensure the organization name is correct
- Check that your token hasn't expired

### "Please set your GITHUB_PERSONAL_ACCESS_TOKEN"
- Make sure you've exported the environment variable
- Verify the variable name is exactly `GITHUB_PERSONAL_ACCESS_TOKEN`

### Empty or missing data
- Check your token has `repo` or `public_repo` permission
- Verify repositories have commits in the specified date range
- Ensure the repository names are spelled correctly (when using --repos)

# gitlab_contributor_count.py

## Description

This Python script counts the number of unique contributors across all repositories in all groups of a GitLab Self-Managed instance. It uses the GitLab API to fetch repository and commit data for a specified time period.

## Features

- Retrieves all groups and their projects from a GitLab instance
- Fetches commits for each project within a specified time frame
- Counts unique contributors across all repositories
- Handles API rate limiting with an exponential backoff retry mechanism
- Provides detailed logging of the process
- Generates a CSV file with a summary of contributors per repository and overall unique contributors

## Requirements

- Python 
- `requests` library

## Installation

1. Clone this repository or download the script.
2. Install the required Python package:

```
pip install requests
```

## Configuration

Before running the script, you need to set up the following:

1. GitLab instance URL
2. Private token for API authentication
3. Number of days to look back for contributions

Edit the following lines at the bottom of the script:

```python
base_url = "https://your-gitlab-instance.com"  # Replace with your GitLab instance URL
private_token = "your_private_token_here"  # Replace with your actual private token
days = 3000  # Number of days to look back
```

## Usage

Run the script using Python:

```
python gitlab_contributor_count.py
```

## Output

The script generates two types of output:
- A log file named gitlab_contributor_count.log with detailed information about the process.
- A CSV file named contributor_summary.csv containing:
    - A list of repositories with their contributor counts and names
    - The total number of unique contributors across all repositories
 

## Logging
The script provides detailed logging at different levels:
- DEBUG: Detailed information about groups, projects, and commits retrieved
- INFO: Summary information about the process and results
- WARNING: Any issues encountered during execution (e.g., rate limiting)
- ERROR: Any errors that occur during the process

Logs are written to both the console and the gitlab_contributor_count.log file.

## Troubleshooting
If you encounter any issues:
- Check the gitlab_contributor_count.log file for error messages.
- Ensure your GitLab instance URL and private token are correct.
- Verify that your GitLab account has the necessary permissions to access the groups and projects.
- If you're hitting rate limits frequently, try increasing the backoff time in the make_request method.


# Bitbucket Contributor Counter

This script counts unique contributors across all repositories in a Bitbucket workspace for a specified time period.

## Features

- Counts unique contributors across all repositories in a workspace
- Configurable time period for analysis
- Handles rate limiting with exponential backoff
- Outputs results to both console and JSON file
- Uses environment variables for secure token management
- Automatic pagination handling for both repositories and commits
- Detailed logging of API requests and responses

## Prerequisites

- Python 3.x
- `requests` library
- Bitbucket access token with appropriate permissions

## Setup

1. Install the required Python package:
```bash
pip install requests
```

2. Set up your Bitbucket access token as an environment variable:
```bash
export BITBUCKET_ACCESS_TOKEN="your_token_here"
```

## Configuration

The script has the following configurable constants at the top of the file:

- `WORKSPACE`: Your Bitbucket workspace name
- `COMMITS_FROM_DAYS`: Number of days to look back for commits (default: 1000)

## Usage

Run the script:
```bash
python bitbucket_contributor_count_retry.py
```

The script will:
1. Fetch all repositories in the specified workspace (with pagination)
2. For each repository, fetch commits within the specified time period (with pagination)
3. Extract unique contributors from the commits
4. Output the results to the console
5. Save the results to a JSON file with timestamp

## Pagination

The script automatically handles pagination for:
- Repository listing: Fetches all repositories across multiple pages
- Commit history: Fetches all commits within the specified time period across multiple pages

Debug logging will show:
- Number of repositories found per page
- Total number of repositories and pages
- Number of commits found per page for each repository
- Total number of commits and pages per repository

## Output

The script generates two types of output:

1. Console output with logging information about:
   - Repository processing progress
   - Number of commits and pages per repository
   - Number of unique contributors per repository
   - Total unique contributors across all repositories
   - API request/response details (in DEBUG mode)

2. JSON file (`contributors_YYYYMMDD_HHMMSS.json`) containing:
   - Workspace name
   - Analysis period in days
   - Total number of contributors
   - Sorted list of all contributors

## Logging

The script uses Python's logging module with the following levels:
- DEBUG (default): Detailed API request/response information, pagination details
- INFO: Repository progress, counts, and results
- WARNING: Rate limit notifications

To change the logging level, modify the `level` parameter in `logging.basicConfig()`:
```python
logging.basicConfig(
    level=logging.INFO,  # Change to INFO to see less detail
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

## Error Handling

The script includes error handling for:
- Missing access token
- API rate limiting (with automatic retry)
- Failed API requests
- Pagination issues

## Security

- Access token is stored in environment variables, not in the code
- API requests use secure HTTPS
- Token is passed securely in request headers 

## Contributing
Contributions to improve the script are welcome. Please feel free to submit a Pull Request.


# Azure DevOps Contributors Counter

A Python script to fetch and analyze unique contributors across all repositories in an Azure DevOps organization and project.

## Description

This script connects to Azure DevOps and generates a report of all unique contributors who have made commits across repositories within a specified time period. It provides both a summary view and detailed breakdown by repository.

## Features

- Fetches contributors from all repositories in a project
- Supports custom time period analysis
- Generates detailed JSON output
- Provides both summary and detailed contributor information
- Handles pagination for large repositories
- Includes error handling and connection testing

## Prerequisites

- Python 3.x
- `requests` library
- Azure DevOps Personal Access Token (PAT)

### Required Azure DevOps Permissions

Your PAT token needs the following permissions:
- Code (Read)
- Graph (Read)
- Git (Read)
- Project and Team (Read)

## Installation

1. Clone this repository or download the script
2. Install the required dependencies:
   ```bash
   pip install requests
   ```

## Usage

1. Set your Azure DevOps Personal Access Token as an environment variable:
   ```bash
   export AZURE_PERSONAL_ACCESS_TOKEN='your_pat_token_here'
   ```

2. Run the script with the required parameters:
   ```bash
   python ado_contributor_count.py <organization_name> <project_name> <number_of_days> <output_filename>
   ```

### Parameters

- `organization_name`: Your Azure DevOps organization name
- `project_name`: The project name within the organization
- `number_of_days`: Number of days to look back for contributors
- `output_filename`: JSON file to store the output

### Example

```bash
python ado_contributor_count.py my-org my-project 30 contributors.json
```

## Output

The script generates a JSON file with the following structure:

```json
{
  "organization": "organization_name",
  "project": "project_name",
  "date": "YYYY-MM-DD",
  "number_of_days_history": number_of_days,
  "total_contributors": total_count,
  "total_repositories": repo_count,
  "repositories": [
    {
      "name": "repo_name",
      "contributors": contributor_count,
      "contributor_emails": ["email1@example.com", "email2@example.com"]
    }
  ],
  "all_contributor_emails": ["email1@example.com", "email2@example.com"]
}
```

## Troubleshooting

If you encounter issues:

1. Verify your PAT token is correct and not expired
2. Confirm the organization and project names are correct
3. Ensure your PAT token has all required permissions
4. Check if you can access the project in your browser
5. Review the error messages and debug output provided by the script

## Contributing
Contributions to improve the script are welcome. Please feel free to submit a Pull Request.
