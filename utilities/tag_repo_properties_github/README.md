Sometimes customers want to work with projects in Semgrep based on metadata from their SCM, such as visibility (public, private, or internal), topics, or source code languages. Semgrep does not read this metadata from the repository. To add it, the customer would have to manually create tags on each project in Semgrep.

This python script reads the metadata of all the repositories in a GitHub or GitHub Enterprise organization and tags the corresponding project in their Semgrep org with:
- the repo's visibility (e.g. `public`)
- a tag per GitHub topic (e.g. `topic:tier1`)
- a tag per source code language reported by GitHub (e.g. `language:Java`)

Note: each run replaces the full set of tags Semgrep has for a project with the set computed above, so any tags added on a project outside of this script will be lost the next time it runs.

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
