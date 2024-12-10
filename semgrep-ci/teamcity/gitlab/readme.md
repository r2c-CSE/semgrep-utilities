## Configuring TeamCity for Semgrep Scans and GitLab MR Comments

The `settings.kts` file in this folder provides the necessary configuration to enable Semgrep scans with GitLab MR comments in TeamCity. If using Kotlin DSL files in your source control, much of this file can be copy and pasted over. If not, then follow the TeamCity UI specifying the necessary values based on what's in the `settings.kts` file.

The build configuration consists of two steps: 1. a diff scan step; and 2. a full scan step. We use a condition (`exists("teamcity.pullRequest.number")`) to determine whether to run a diff scan or a full scan. There may be other ways to accomplish this as well.

Both diff scan and full scan steps rely on a few shared variables, some of which should be stored as secrets within the TeamCity platform. The shared variables are the following:
* `env.SEMGREP_APP_TOKEN` -- Secret used to authenticate with `semgrep.dev`.
* `env.SEMGREP_REPO_URL` -- The URL of the repository to be scanned and can be set dynamically. One such value is `%vcsroot.url%`
* `env.SEMGREP_REPO_NAME` -- The name of the repository to scan. This name should align with the name of the repository in GitLab in the form of `orgName/repoName`
* `env.GITLAB_TOKEN` -- Secret used to authenticate with the GitLab API for creating comments on MRs.

For diff scans, we need to set a few additional variables as well. These values are specified in the VCS trigger section, which confines them to just the diff scan step.
* `env.SEMGREP_BASELINE_REF` -- The ref to enable diff aware scanning. See our documentation [here.](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables#semgrep_baseline_ref) This can be set to `origin/%teamcity.pullRequest.target.branch%`
* `env.SEMGREP_BRANCH` -- The name of the branch we're scanning. See our documentation [here.](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables#semgrep_branch) This can be set dynamically to `%teamcity.pullRequest.source.branch%`.
* `env.SEMGREP_PR_ID` -- Used to enable MR comments. See our documentation [here.](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables#semgrep_pr_id) This value can be set dynamically to `%teamcity.pullRequest.number%`
* `teamcity.git.fetchAllHeads` -- Set to `true` which allows Semgrep to calculate the diff between the baseline ref and current branch.

**_NOTE:_** This configuration provides daily scans to ensure regular full repository analysis for vulnerabilities and issues.
**_NOTE:_** This configuration provides performance monitoring to track and log performance metrics for the build process.
