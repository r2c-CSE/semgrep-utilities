Sometimes customers want to work with projects in Semgrep based on their visibility in their SCM (public, private, or internal). Semgrep does not read this metadata from the repository. To add it, the customer would have to manually create tags on each project in Semgrep.

This python script reads the metadata of all the repositories in their GitHub or GitHub Enterprise organization and tags the corresponding project in their Semgrep org with the repository's visibility. 

Before running the script, you will need to add a .env file to the same folder. The .env file should contain the following values:
```
# GitHub personal access token with permission to read the metadata for all the repos.
GITHUB_TOKEN = 'your_github_token'
# GitHub organization
GITHUB_ORG = 'your_org'
# GitHub API base URL. No need to alter this value.
GITHUB_API_URL = 'https://api.github.com'
# Semgrep Organization Slug (Found by going to the Semgrep settings and scrolling to the bottom).
SEMGREP_ORG_SLUG = 'your_semgrep_org_slug'
# Semgrep API token. Acquired from the Semgrep 'Settings -> Tokens' page.
SEMGREP_API_TOKEN='your_semgrep_api_token'
```