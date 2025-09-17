## Sample output:
```
total number of pull request events in the past 1 year: XXX
average number of pull request events per month in the past 1 year: XX.XX
total number of pull requests in the past 1 year: XXX
average number of pull requests per month in the past 1 year: XX.XX
```

## Required inputs (configured as environment variables):
* GITHUB_ORG: Name of your GitHub Org
* GITHUB_TOKEN- requires the following permissions:
  * Read access to administration, code, metadata, and pull requests
  * Read access to members
  * <img width="996" alt="image" src="https://github.com/r2c-CSE/semgrep-utilities/assets/119853191/339b3440-3151-4f5f-9d04-67936aea5804">


## How does it work:
* Get list of repos in the customer ORG
* Get list of PRs in the repo
* Get list of commits in the PR (this is for the case when  multiple commits into the same PR) and check if commit date was < 365 days from todays date


## Sample output- details per repo and per pull request:
```
total number of commits in repo: semgrep-utilities, pr-#21, pr-title: add new config, head: PR1 into base: main  - 2
total number of commits in repo: semgrep-utilities, pr-#20, pr-title: Branch 1, head: BRANCH_1 into base: main  - 7
total number of commits in repo: semgrep-utilities, pr-#19, pr-title: Patch 3, head: patch-3 into base: main  - 4
total number of commits in repo: semgrep-utilities, pr-#18, pr-title: Sebastianrevuelta patch 2, head: sebastianrevuelt into base: main  - 5
total number of commits in repo: semgrep-utilities, pr-#17, pr-title: Prg1, head: PRG1 into base: main  - 5
```
