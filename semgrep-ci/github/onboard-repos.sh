#!/opt/homebrew/bin/bash

# TODO: Work out a way to change the cron per-repo (probably not critical but wd be better)
# Works best if semgrep.yml file uses org secret or reusable workflow (avoids needing to add secret everywhere)

if [[ -z $1 ]]
then
  echo "You must set an org name"
  exit 1
fi

if ! [[ -f semgrep.yml ]]
then
  echo "Please create a semgrep.yml in the current directory to add to every repo."
  exit 1
fi

# Set up variables
GH_ORG_NAME=$1
PR_TITLE="Add semgrep.yml to .github/workflows to run Semgrep scans"
PR_BODY="Adding Semgrep GitHub action to scan code for security issues"
REPO_LIMIT=200
BRANCH_NAME="add-semgrep"
SEMGREP_YML_BASE64=$(cat semgrep.yml | base64)

echo "This script uses the Github CLI (gh) client to add semgrep to repos in $GH_ORG_NAME 
by creating PRs on branch $BRANCH_NAME."

# Grab only the repo name and default branch of unarchived repos with limit $REPO_LIMIT
gh repo list $GH_ORG_NAME --no-archived -L $REPO_LIMIT --json nameWithOwner,defaultBranchRef > repos.json
echo "Collecting repo names and default branches..."
GITHUB_REPOS=($(jq -r '.[].nameWithOwner' repos.json))
GITHUB_BRANCHES=($(jq -r '.[].defaultBranchRef.name' repos.json))

# iterate over repos, creating PRs for each one
for i in ${!GITHUB_REPOS[@]}; do
  GH_REPO=${GITHUB_REPOS[$i]}
  GH_DEFAULT_BRANCH=${GITHUB_BRANCHES[$i]}
  echo "Creating $BRANCH_NAME on $GH_REPO based on $GH_DEFAULT_BRANCH"
  # Get the SHA of the default branch
  DEFAULT_BRANCH_SHA=$(gh api repos/{owner}/{repo}/git/ref/heads/$GH_DEFAULT_BRANCH --jq ".object.sha")
  # Create the new branch off the default branch sha
  gh api repos/{owner}/{repo}/git/refs -X POST -F ref=refs/heads/$BRANCH_NAME -F sha=$DEFAULT_BRANCH_SHA
  # TODO: Check return and flag if ref already exists (probably OK) or some other issue (probably not OK)
  # Add the file to the branch (creates a commit also)
  echo "Creating semgrep.yml on $BRANCH_NAME in $GH_REPO"
  gh api repos/{owner}/{repo}/contents/.github/workflows/semgrep.yml \
    -X PUT \
    -H "Accept: application/vnd.github.v3+json" \
    -F message="Add semgrep.yml" \
    -F content=$SEMGREP_YML_BASE64 \
    -F branch=$BRANCH_NAME
  # TODO: Check return and flag if "sha wasn't supplied" (file is already present, probably OK) or something else (probably not OK)
  # Create a PR with the branch and added file
  echo "Creating PR for $BRANCH_NAME in $GH_REPO to $GH_DEFAULT_BRANCH"
  gh pr create -b "$PR_BODY" -R $GH_REPO -t "$PR_TITLE" --base $GH_DEFAULT_BRANCH -H $BRANCH_NAME
done
