#!/bin/bash

# Check for org and branch names and repo limit
while getopts o:b:l:m flag
do
  case $flag in
    o) GH_ORG_NAME=${OPTARG};;
    b) BRANCH_NAME=${OPTARG};;
    l) REPO_LIMIT=${OPTARG};;
    m) MERGE=true;;
  esac
done

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

echo "This script uses the Github CLI (gh) client to approve existing PRs
      on $BRANCH_NAME to add semgrep to repos in $GH_ORG_NAME."

if [[ -n $MERGE ]]
then
  echo "The PRs will also be merged."
fi


# Grab only the repo name of unarchived repos with limit $REPO_LIMIT
gh repo list $GH_ORG_NAME --no-archived -L $REPO_LIMIT --json name > repos.json
echo "Collecting repo names..."
GITHUB_REPOS=($(jq -r '.[].name' repos.json))

# Iterate over repo PRs, approving (and potentially merging) each one
for i in ${!GITHUB_REPOS[@]}; do
  GH_REPO_NAME=${GITHUB_REPOS[$i]}
  gh pr review -R "$GH_ORG_NAME/$GH_REPO_NAME" $BRANCH_NAME --approve
  if [[ $MERGE == true ]]
  then
    gh pr merge -R "$GH_ORG_NAME/$GH_REPO_NAME" $BRANCH_NAME -m
  fi
done

# Cleanup
rm -f repos.json
