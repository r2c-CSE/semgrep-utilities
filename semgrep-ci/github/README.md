# Index
* Creating (and approving) PRs to onboard Semgrep to GitHub repos

# Creating (and approving) PRs to onboard Semgrep to GitHub repos

If you use branch protection on your GitHub repos, onboarding Semgrep to many repos at the same time is not currently possible through the Semgrep Cloud Platform UI. The scripts in this directory provide an alternative. The script `onboard-repos.sh` creates PRs for all targeted repos in an organization, and the script `approve-semgrep-prs.sh` approves and merges those PRs.

The approval script is optional. PRs can also be reviewed manually. If you run the approval script, you can also choose whether or not to merge the approved PR.

To easily provide a secure `SEMGREP_APP_TOKEN` value to all repos, set the value as an [organization secret](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions#creating-secrets-for-an-organization). If you do not have access to organization secrets, consider setting up a [reusable workflow](https://semgrep.dev/docs/kb/semgrep-ci/github-reusable-workflows-semgrep/) and referencing that workflow in the `semgrep.yml` you will use to onboard other repositories.

## Prerequisities

The scripts make use of the [`gh`](https://cli.github.com/manual/gh) command line client to interact with the GitHub API. Install the client before attempting to use the script. For Mac, the client is available via `brew`.

After installing the client, determine which GitHub account to log in with.

* To create PRs, you need a GitHub user account that has permission to create PRs on any repos in the target organization that you want to onboard.
* To approve and merge PRs, you need a **different** user account that has permission to review and merge PRs on those same repos. The same user cannot both create and review a PR.

Use `gh auth login` to log in. To change users, use `gh auth logout` and then log in with the new user. Use `gh auth login --help` to see more options (e.g. for GitHub Enterprise Server, or to use a token).

## How the scripts work

* `onboard-repos.sh`: Requires a local `semgrep.yml` specifying the desired configuration. Checks repos for existing Semgrep workflow files. Repos with existing files are skipped. Other repos have PRs opened on a new branch with the content of the local `semgrep.yml`.
  * Onboards all repos in an organization up to a configurable limit.
  * Branch name for PRs is configurable.
  * PR title and content can be modified through the script body.
* `approve-semgrep-prs.sh`: Approves and merges PRs from the provided branch name. This branch name should match the one used in `onboard-repos.sh`.
  * Approves PRs for all repos in an organization up to a configurable limit.
  * Merges PRs if `-m` flag is set.

The onboarding script will catch errors during the branch and commit creation process, and print messages as to whether the error is concerning. Some errors are expected: for example, if you already have a branch of a particular name, and the script tries to create a branch with the same name, it records that the branch exists and proceeds. (Using a relatively unique branch name is recommended. The default is `add-semgrep`.)

If unexpected errors occur when creating the branch and adding the file, onboarding for that repo will be skipped and the script will proceed to the next repo.

If errors occur in creating, reviewing, or merging the PR, the script will print the error that occurred. Most errors for these commands provide helpful guidance to resolve the issue. For example, if the same user attempts to review the PR who created it, you see `failed to create review: GraphQL: Can not approve your own pull request (addPullRequestReview)`.

## Sample workflow

1. Download scripts to a local directory.
2. Create `semgrep.yml` in local directory, according to your needs. See [Sample GitHub Actions configuration file](https://semgrep.dev/docs/semgrep-ci/sample-ci-configs/#sample-github-actions-configuration-file) and [CI environment variables](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables/) in the Semgrep docs.
3. `brew install gh`
4. `gh auth login` and log in as the user who will create all the PRs.
5. Execute `onboard-repos.sh -o YOUR_GITHUB_ORG`. If you wish to test with a small number of repos first, set a low limit, such as `-l 5`.
6. If PR creation is generally successful, proceed with `gh auth logout` and then `gh auth login` as the user who will approve and merge the PRs.
7. Run `approve-semgrep-prs.sh` to approve the PRs. Run with `-m` to merge the PRs.

