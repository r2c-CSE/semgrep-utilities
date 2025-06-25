# Semgrep Contributors Tool

A unified command-line tool for counting and analyzing contributors across multiple Git platforms including GitHub, GitLab, Bitbucket, and Azure DevOps.

## Overview

This tool helps estimate the number of active contributors within organizations across different Git platforms over a specified time period. It provides a consistent interface for all supported platforms and generates detailed reports with contributor statistics.

## Features

- **Multi-platform support**: GitHub, GitLab, Bitbucket, and Azure DevOps
- **Unified CLI interface**: Single command with platform-specific subcommands
- **Flexible filtering**: Filter by specific repositories or groups
- **Detailed reporting**: JSON output with comprehensive contributor statistics
- **Rate limiting handling**: Built-in retry mechanisms for API rate limits
- **Environment variable support**: Secure API key management

## Installation

### Prerequisites

- Python 3.12.8 or higher
- API access tokens for the platforms you want to analyze

### Setup

1. Clone this repository and navigate to the `utilities/contributors` directory
2. Install the package using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Docker

You can also run the tool using Docker, which eliminates the need to install Python dependencies locally:

```bash
# Build the Docker image
docker build -t semgrep-contributors .

# Run with Docker (example for GitHub)
docker run --rm \
  -e GITHUB_API_KEY=your_token_here \
  -v $(pwd):/workspace \
  semgrep-contributors github \
  --org-name your-org \
  --number-of-days 30 \
  --output-filename /workspace/contributors.json
```

**Docker Options:**
- `--rm`: Automatically remove the container when it exits
- `-e`: Set environment variables for API keys
- `-v $(pwd):/workspace`: Mount current directory to share files between host and container
- `-w /workspace`: Set working directory (optional, for convenience)

**Example for all platforms:**
```bash
# GitHub
docker run --rm -e GITHUB_API_KEY=your_token semgrep-contributors github --org-name my-org

# GitLab
docker run --rm -e GITLAB_API_KEY=your_token semgrep-contributors gitlab --hostname gitlab.company.com

# Bitbucket
docker run --rm -e BITBUCKET_API_KEY=your_token -e BITBUCKET_WORKSPACE=my-workspace semgrep-contributors bitbucket

# Azure DevOps
docker run --rm -e AZURE_DEVOPS_API_KEY=your_token -e AZURE_DEVOPS_ORGANIZATION=my-org semgrep-contributors azure-devops
```

## Usage

The tool provides a unified CLI interface with platform-specific subcommands:

```bash
semgrep-contributors [OPTIONS] COMMAND [ARGS]...
```

### Common Options

- `--debug`: Enable debug logging
- `--help`, `-h`: Show help information

### Platform Commands

#### GitHub

```bash
semgrep-contributors github [OPTIONS]
```

**Options:**
- `--api-key TEXT`: GitHub API key (or set `GITHUB_API_KEY` environment variable)
- `--org-name TEXT`: Name of the GitHub organization (required)
- `--number-of-days INTEGER`: Number of days to analyze (default: 30)
- `--output-filename TEXT`: Output JSON file path (optional)
- `--repo-file PATH`: File containing repository names to filter (optional)
- `--repositories TEXT`: Comma-separated list of repositories to analyze (optional)

**Example:**
```bash
export GITHUB_API_KEY=ghp_your_token_here
semgrep-contributors github --org-name r2c-cse --number-of-days 90 --output-filename github_contributors.json
```

#### GitLab

```bash
semgrep-contributors gitlab [OPTIONS]
```

**Options:**
- `--api-key TEXT`: GitLab API key (or set `GITLAB_API_KEY` environment variable)
- `--number-of-days INTEGER`: Number of days to analyze (default: 30)
- `--output-filename TEXT`: Output JSON file path (optional)
- `--repo-file PATH`: File containing repository names to filter (optional)
- `--hostname TEXT`: GitLab instance hostname (default: gitlab.com)
- `--group TEXT`: GitLab group to analyze (optional)
- `--repositories TEXT`: Comma-separated list of repositories to analyze (optional)

**Example:**
```bash
export GITLAB_API_KEY=glpat_your_token_here
semgrep-contributors gitlab --hostname gitlab.company.com --group my-group --number-of-days 60
```

#### Bitbucket

```bash
semgrep-contributors bitbucket [OPTIONS]
```

**Options:**
- `--api-key TEXT`: Bitbucket API key (or set `BITBUCKET_API_KEY` environment variable)
- `--workspace TEXT`: Bitbucket workspace (or set `BITBUCKET_WORKSPACE` environment variable)
- `--number-of-days INTEGER`: Number of days to analyze (default: 30)
- `--output-filename TEXT`: Output JSON file path (optional)
- `--repo-file PATH`: File containing repository names to filter (optional)
- `--repositories TEXT`: Comma-separated list of repositories to analyze (optional)

**Example:**
```bash
export BITBUCKET_API_KEY=your_token_here
export BITBUCKET_WORKSPACE=my-workspace
semgrep-contributors bitbucket --number-of-days 45 --output-filename bitbucket_contributors.json
```

#### Azure DevOps

```bash
semgrep-contributors azure-devops [OPTIONS]
```

**Options:**
- `--api-key TEXT`: Azure DevOps API key (or set `AZURE_DEVOPS_API_KEY` environment variable)
- `--organization TEXT`: Azure DevOps organization (or set `AZURE_DEVOPS_ORGANIZATION` environment variable)
- `--number-of-days INTEGER`: Number of days to analyze (default: 30)
- `--output-filename TEXT`: Output JSON file path (optional)
- `--repo-file PATH`: File containing repository names to filter (optional)
- `--repositories TEXT`: Comma-separated list of repositories to analyze (optional)

**Example:**
```bash
export AZURE_DEVOPS_API_KEY=your_pat_token_here
export AZURE_DEVOPS_ORGANIZATION=my-org
semgrep-contributors azure-devops --number-of-days 30 --output-filename azure_contributors.json
```

## API Key Requirements

### GitHub
- **Token Type**: Personal Access Token (PAT)
- **Required Scopes**: `repo`, `read:org`, `read:user`, `user:email`

### GitLab
- **Token Type**: Personal Access Token
- **Required Scopes**: `read_api`, `read_user`, `read_repository`

### Bitbucket
- **Token Type**: App Password or Personal Access Token
- **Required Scopes**: `Repositories: Read`, `Pull requests: Read`

### Azure DevOps
- **Token Type**: Personal Access Token (PAT)
- **Required Scopes**: `Code (Read)`, `Graph (Read)`, `Git (Read)`, `Project and Team (Read)`

## Output Format

The tool generates JSON reports with the following structure:

### Base Report Structure
```json
{
  "date": "2024-01-15",
  "number_of_days_history": 30,
  "repository_stats": [
    {
      "name": "repo-name",
      "contributor_count": 5,
      "contributors": ["user1@example.com", "user2@example.com"]
    }
  ],
  "total_contributor_count": 15,
  "total_repository_count": 10
}
```

### Platform-Specific Extensions

**GitHub:**
```json
{
  "organization": "org-name",
  "org_members": ["member1@example.com", "member2@example.com"],
  "org_contributors": ["contributor1@example.com"],
  "org_contributors_count": 1
}
```

**GitLab:**
```json
{
  "all_contributors": ["contributor1@example.com", "contributor2@example.com"]
}
```

**Bitbucket:**
```json
{
  "workspace": "workspace-name",
  "all_contributors": ["contributor1@example.com", "contributor2@example.com"]
}
```

**Azure DevOps:**
```json
{
  "organization": "org-name",
  "all_contributor_emails": ["contributor1@example.com", "contributor2@example.com"]
}
```

## Repository Filtering

You can filter repositories using either:

1. **Repository file**: Create a text file with one repository name per line
2. **Command line**: Provide a comma-separated list of repository names

Example repository file (`repos.txt`):
```
my-repo-1
my-repo-2
my-repo-3
```

Usage:
```bash
semgrep-contributors github --org-name my-org --repo-file repos.txt
# or
semgrep-contributors github --org-name my-org --repositories "repo1,repo2,repo3"
```

## Development

### Project Structure
```
src/contributors/
├── cli.py              # Main CLI interface
├── main.py             # Entry point
├── commands/           # Command implementations
│   └── get_contributors.py
├── models/             # Pydantic data models
│   ├── reports.py
│   ├── github_models.py
│   ├── gitlab_models.py
│   ├── bitbucket_models.py
│   └── azure_devops_models.py
├── clients/            # API clients
└── reporters/          # Platform-specific reporters
```

### Running Tests
```bash
# Install test dependencies
uv sync --group dev

# Run tests
pytest
```

### Building
```bash
# Build the package
uv build

# Install in development mode
uv pip install -e .
```

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: The tool includes automatic retry mechanisms, but you may need to wait if you hit rate limits frequently.

2. **Authentication Errors**: Ensure your API tokens have the correct permissions and are not expired.

3. **Repository Access**: Verify that your API token has access to the repositories you're trying to analyze.

4. **Debug Mode**: Use the `--debug` flag to get detailed logging information:
   ```bash
   semgrep-contributors --debug github --org-name my-org
   ```

### Logging

The tool provides different logging levels:
- **INFO** (default): Basic progress and summary information
- **DEBUG**: Detailed API request/response information and pagination details

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests to improve the tool.

## License

This project is part of the Semgrep utilities and follows the same licensing terms.
