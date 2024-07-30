Sometimes customers want to work with projects in Semgrep based on their visibility in their SCM (public, private, or internal). Semgrep does not read this metadata from the repository. To add it, the customer would have to manually create tags on each project in Semgrep.

This python script reads the metadata of all the repositories in their GitHub or GitHub Enterprise organization and tags the corresponding project in their Semgrep org with the repository's visibility. 

You'll need to paste the following values in the variables at the top of the script:
* A GitHub Personal Access Token with permission to read the metadata for all the repos.
* The name of your GitHub org.
* Your Semgrep Organization Slug (Can see this value by going to the settings and scrolling to the bottom of the page).
* A Semgrep API token. Can generate from the Settings -> Tokens page.