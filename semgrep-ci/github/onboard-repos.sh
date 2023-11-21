#!/bin/bash

# TODO: Work out a way to change the cron per-repo (probably not critical but wd be better)
# Where does the secret come from? Maybe we should do the reusable workflows?

if ! [[ -f semgrep.yml ]]
then
  echo "Please create a semgrep.yml in the current directory to add to every repo."
  exit 1
fi

while getopts ao: flag
do
  case $flag in
    o) GH_ORG_NAME=${OPTARG};;
    a) APPROVE=true;;
  esac
done

if [[ -z $GH_ORG_NAME ]]
then
  echo "You must set an org name"
  exit 1
fi

# Set up variables
PR_TITLE="Add semgrep.yml to .github/workflows to run Semgrep scans"
PR_BODY="Adding Semgrep GitHub action to scan code for security issues"
# Change this limit to match the number of repos you want to onboard
REPO_LIMIT=200
BRANCH_NAME="add-semgrep"
SEMGREP_YML_BASE64=$(cat semgrep.yml | base64)

echo "This script uses the Github CLI (gh) client to add semgrep to repos in $GH_ORG_NAME 
by creating PRs on branch $BRANCH_NAME."

if [[ -z $APPROVE ]]
then
  echo "PRs will only be created, not approved."
else
  echo "PRs will be approved as well as created"
fi

# Grab only the repo name and default branch of unarchived repos with limit $REPO_LIMIT
gh repo list $GH_ORG_NAME --no-archived -L $REPO_LIMIT --json nameWithOwner,defaultBranchRef > repos.json
echo "Collecting repo names and default branches..."
GITHUB_REPOS=($(jq -r '.[].nameWithOwner' repos.json))
GITHUB_BRANCHES=($(jq -r '.[].defaultBranchRef.name' repos.json))

# iterate over repos, creating PRs for each one
for i in ${!GITHUB_REPOS[@]}; do
  GH_REPO=${GITHUB_REPOS[$i]}
  GH_DEFAULT_BRANCH=${GITHUB_BRANCHES[$i]}
  # Check if the file exists on the default branch
  SEMGREP_ONBOARDED=`gh api repos/{owner}/{repo}/contents/.github/workflows/semgrep.yml\?branch=$GH_DEFAULT_BRANCH --jq '.name'`
  if [[ $SEMGREP_ONBOARDED == 'semgrep.yml' ]]
  then
    echo "Semgrep already onboarded for $GH_REPO. Moving to next repo."
    continue
  fi
  echo "Creating $BRANCH_NAME on $GH_REPO based on $GH_DEFAULT_BRANCH"
  # Get the SHA of the default branch
  DEFAULT_BRANCH_SHA=$(gh api repos/{owner}/{repo}/git/ref/heads/$GH_DEFAULT_BRANCH --jq ".object.sha")
  # Create the new branch off the default branch sha
  BRANCH_CREATION_RESULT=`gh api repos/{owner}/{repo}/git/refs -X POST -F ref=refs/heads/$BRANCH_NAME -F sha=$DEFAULT_BRANCH_SHA`
  BC_STATUS=$?
  if [[ $BRANCH_CREATION_RESULT =~ "Reference already exists" ]]
  then
    echo "A branch with the name $BRANCH_NAME already exists on $GH_REPO, no need to create one."
  elif [[ $BC_STATUS -ne 0 ]]
  then
    echo "Something else went wrong for $GH_REPO: $BRANCH_CREATION_RESULT"
    continue    
  fi
  # Add the file to the branch (creates a commit also)
  echo "Creating semgrep.yml on $BRANCH_NAME in $GH_REPO"
  FILE_CREATION_RESULT=`gh api repos/{owner}/{repo}/contents/.github/workflows/semgrep.yml \
    -X PUT \
    -H "Accept: application/vnd.github.v3+json" \
    -F message="Add semgrep.yml" \
    -F content=$SEMGREP_YML_BASE64 \
    -F branch=$BRANCH_NAME`
  FC_STATUS=$?
  # If the file exists, GitHub expects a sha to update it from, so "sha wasn't supplied" means the file exists (weird but true)
  if [[ $FILE_CREATION_RESULT =~ "\\\"sha\\\" wasn't supplied" ]]
  then
    echo "A semgrep.yml file already exists on $BRANCH_NAME in $GH_REPO, no need to create one."
  elif [[ $FC_STATUS -ne 0 ]]
  then
    echo "Something else went wrong for $GH_REPO: $FILE_CREATION_RESULT"
    continue    
  fi
  # Create a PR with the branch and added file
  echo "Creating PR for $BRANCH_NAME in $GH_REPO to $GH_DEFAULT_BRANCH"
  gh pr create -b "$PR_BODY" -R $GH_REPO -t "$PR_TITLE" --base $GH_DEFAULT_BRANCH -H $BRANCH_NAME
  
  # Cleanup
  rm -f repos.json
done
