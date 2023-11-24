#!/bin/bash

# A local semgrep.yml is required
if ! [[ -f semgrep.yml ]]
then
  echo "Please create a semgrep.yml in the current directory to add to every repo."
  exit 1
fi

# Check for org and branch names and repo limit
while getopts o:b:l: flag
do
  case $flag in
    o) GH_ORG_NAME=${OPTARG};;
    b) BRANCH_NAME=${OPTARG};;
    l) REPO_LIMIT=${OPTARG};;
  esac
done

# Org name is required - we can't know it in advance
if [[ -z $GH_ORG_NAME ]]
then
  echo "Usage: $0 -o github_org_name [-b branch_name] [-l repo_limit]"
  exit 1
fi

# If optional variables are not set, fall back to default
if [[ -z $BRANCH_NAME ]]
then
  BRANCH_NAME="add-semgrep"
fi

if [[ -z $REPO_LIMIT ]]
then
  REPO_LIMIT=10
fi

# These values can be safely modified, but are not configurable by default
PR_TITLE="Add semgrep.yml to .github/workflows to run Semgrep scans"
PR_BODY="Adding Semgrep GitHub action to scan code for security issues"

echo "This script uses the Github CLI (gh) client to add semgrep to repos in $GH_ORG_NAME
by creating PRs on branch $BRANCH_NAME."

# Grab only the repo name and default branch of unarchived repos with limit $REPO_LIMIT
gh repo list $GH_ORG_NAME --no-archived -L $REPO_LIMIT --json name,defaultBranchRef > repos.json
echo "Collecting repo names and default branches..."
GITHUB_REPOS=($(jq -r '.[].name' repos.json))
GITHUB_BRANCHES=($(jq -r '.[].defaultBranchRef.name' repos.json))

# iterate over repos, creating PRs for each one
for i in ${!GITHUB_REPOS[@]}; do
  GH_REPO_NAME=${GITHUB_REPOS[$i]}
  GH_DEFAULT_BRANCH=${GITHUB_BRANCHES[$i]}
  # Check if the file exists on the default branch
  SEMGREP_ONBOARDED=`gh api repos/$GH_ORG_NAME/$GH_REPO_NAME/contents/.github/workflows/semgrep.yml\?branch=$GH_DEFAULT_BRANCH --jq '.name'`
  if [[ $SEMGREP_ONBOARDED == 'semgrep.yml' ]]
  then
    echo "Semgrep already onboarded for $GH_REPO_NAME. Moving to next repo."
    continue
  fi
  echo "Creating $BRANCH_NAME on $GH_REPO_NAME based on $GH_DEFAULT_BRANCH"
  # Get the SHA of the default branch
  DEFAULT_BRANCH_SHA=$(gh api repos/$GH_ORG_NAME/$GH_REPO_NAME/git/ref/heads/$GH_DEFAULT_BRANCH --jq ".object.sha")
  # Create the new branch off the default branch sha
  BRANCH_CREATION_RESULT=`gh api repos/$GH_ORG_NAME/$GH_REPO_NAME/git/refs -X POST -F ref=refs/heads/$BRANCH_NAME -F sha=$DEFAULT_BRANCH_SHA`
  BC_STATUS=$?
  if [[ $BRANCH_CREATION_RESULT =~ "Reference already exists" ]]
  then
    echo "A branch with the name $BRANCH_NAME already exists on $GH_REPO_NAME, no need to create one."
  elif [[ $BC_STATUS -ne 0 ]]
  then
    echo "Something else went wrong for $GH_REPO_NAME: $BRANCH_CREATION_RESULT"
    continue
  fi

  # Generate a new random cron expression to run schedule scans
  random_value_minutes=$((RANDOM % 59))
  random_value_hours=$((RANDOM % 24))
  minutes=$(printf "%02d" "$random_value_minutes")
  hours=$(printf "%02d" "$random_value_hours")
  new_content="    - cron: '$minutes $hours * * *'"

  # Use sed to replace the specified line in the file
  line_number=$(grep -n "cron:" "semgrep.yml" | cut -d ':' -f 1)
  sed "${line_number}s/.*/${new_content}/" semgrep.yml > semgrep_$GH_REPO_NAME.yml

  SEMGREP_YML_BASE64=$(cat semgrep_$GH_REPO_NAME.yml | base64)

  # Add the file to the branch (creates a commit also)
  echo "Creating semgrep.yml on $BRANCH_NAME in $GH_REPO_NAME"
  FILE_CREATION_RESULT=`gh api repos/$GH_ORG_NAME/$GH_REPO_NAME/contents/.github/workflows/semgrep.yml \
    -X PUT \
    -H "Accept: application/vnd.github.v3+json" \
    -F message="Add semgrep.yml" \
    -F content=$SEMGREP_YML_BASE64 \
    -F branch=$BRANCH_NAME`
  FC_STATUS=$?
  # If the file exists, GitHub expects a sha to update it from, so "sha wasn't supplied" means the file exists (weird but true)
  if [[ $FILE_CREATION_RESULT =~ "\\\"sha\\\" wasn't supplied" ]]
  then
    echo "A semgrep.yml file already exists on $BRANCH_NAME in $GH_REPO_NAME, no need to create one."
  elif [[ $FC_STATUS -ne 0 ]]
  then
    echo "Something else went wrong for $GH_REPO_NAME: $FILE_CREATION_RESULT"
    continue
  fi
  # Create a PR with the branch and added file
  echo "Creating PR for $BRANCH_NAME in $GH_REPO_NAME to $GH_DEFAULT_BRANCH"
  gh pr create -b "$PR_BODY" -R "$GH_ORG_NAME/$GH_REPO_NAME" -t "$PR_TITLE" --base $GH_DEFAULT_BRANCH -H $BRANCH_NAME
done

# Cleanup
rm -f repos.json
