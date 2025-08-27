# Semgrep Repository Tag Creation Script

A Python script to create and manage tags for Semgrep repositories using the Semgrep API. Supports both simple tags (like `Python-3.7`) and key-value tags (like `environment:production`).

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Semgrep API token:
```bash
export SEMGREP_APP_TOKEN="your_semgrep_api_token_here"
```

## Usage

### Create a simple tag
```bash
python create_semgrep_tag.py <org_slug> <repo_name> <tag_name>
```

### Create a key-value tag
```bash
python create_semgrep_tag.py <org_slug> <repo_name> <tag_name> <tag_value>
```

### List tags for a specific repository
```bash
python create_semgrep_tag.py <org_slug> <repo_name> --list
```

### List all repositories in organization
```bash
python create_semgrep_tag.py <org_slug> --list-all
```

## Examples

```bash
# Create a simple tag (like managed-scan, Python-3.7)
python create_semgrep_tag.py semgrep_kyle_sms kyle-semgrep/js-app Python-3.7

# Create a key-value tag (like environment:production)
python create_semgrep_tag.py semgrep_kyle_sms kyle-semgrep/js-app environment production

# Create more tags
python create_semgrep_tag.py semgrep_kyle_sms kyle-semgrep/js-app language JavaScript
python create_semgrep_tag.py semgrep_kyle_sms kyle-semgrep/js-app team security

# List tags for a specific repository
python create_semgrep_tag.py semgrep_kyle_sms kyle-semgrep/js-app --list

# List all repositories in the organization
python create_semgrep_tag.py semgrep_kyle_sms --list-all
```

## Key Features

- ✅ **Simple Tags**: Create tags like `Python-3.7`, `managed-scan` (no value needed)
- ✅ **Key-Value Tags**: Create tags like `environment:production`, `language:JavaScript`
- ✅ **Tag Management**: Updates existing tags or adds new ones
- ✅ **Preserves System Tags**: Keeps reserved tags like `managed-scan`
- ✅ **Repository Discovery**: List all repositories in an organization
- ✅ **Tag Listing**: View current tags for any repository

## Finding Your Repository Name

Use the `--list-all` flag to find the exact repository name format:

```bash
python create_semgrep_tag.py your_org_slug --list-all
```

This will show all repositories like:
```
- kyle-semgrep/js-app (tags: ['managed-scan', 'Python-3.7'])
- kyle-semgrep/java-app (tags: [])
```

## Notes

- **Organization Slug**: Use underscores, not dashes (e.g., `semgrep_kyle_sms`)
- **Repository Name**: Use the full `owner/repo` format (e.g., `kyle-semgrep/js-app`)
- **API Token**: Set the `SEMGREP_APP_TOKEN` environment variable
- **Tag Updates**: Existing key-value tags get updated, simple tags are skipped if they exist
- **Reserved Tags**: System tags like `managed-scan` are preserved automatically