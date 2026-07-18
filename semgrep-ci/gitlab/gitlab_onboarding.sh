#!/bin/bash

# This scripts needs to setup the next environment variables:
## SEMGREP_APP_TOKEN
## GITLAB_ACCESS_TOKEN (API permissions)
## GITLAB_USER_ID

## and also it needs:
## jq utility
## git client

# GitLab API URL to fetch repositories
API_URL="https://gitlab.com/api/v4/users/${GITLAB_USER_ID}/projects?private_token=${GITLAB_ACCESS_TOKEN}&simple=true&per_page=100"
# Directory where repositories will be cloned
WORKDIR="./gitlab_repos"

# Semgrep CI configuration to add to .gitlab-ci.yml
SEMGREP_CI_CONFIG="
semgrep:
  image: semgrep/semgrep
  script: semgrep ci
  rules:
  - if: \$CI_MERGE_REQUEST_IID
  - if: \$CI_COMMIT_BRANCH == \$CI_DEFAULT_BRANCH
  variables:
    SEMGREP_APP_TOKEN: \$SEMGREP_APP_TOKEN
"

# Function to fetch repository SSH URLs
fetch_repos() {
    curl --header "Private-Token: $GITLAB_ACCESS_TOKEN" "$API_URL" | jq -r '.[] | .http_url_to_repo'
}

# Main script
mkdir -p "$WORKDIR"
cd "$WORKDIR"


fetch_repos | while read gitlab_repo_url; do

    repo_name=$(basename -s .git "${gitlab_repo_url}")
    rm -rf ${repo_name}
    echo "cloning ${gitlab_repo_url}"
    repo_url="${gitlab_repo_url/https:\/\//}"
    git clone https://oauth2:${GITLAB_ACCESS_TOKEN}@${repo_url}
    cd ${repo_name}

    # Check if .gitlab-ci.yml exists and add or modify it
    if [ -f ".gitlab-ci.yml" ]; then
        ## detect if Semgrep is already added to the .gitlab-ci.yml
        grep -qi "semgrep" .gitlab-ci.yml
        found=$?
        if [ $found -eq 0 ]; then
            echo "**** Skipping the repo $repo_name because it has already installed Semgrep ****"
            continue
        else
            echo "---- Modifying existing .gitlab-ci.yml for $repo_name ----"
            git checkout -b ADD_SEMGREP
            echo "$SEMGREP_CI_CONFIG" >> .gitlab-ci.yml
        fi
    else
        echo "++++ Creating new .gitlab-ci.yml for $repo_name ++++"
        git checkout -b ADD_SEMGREP
        echo "$SEMGREP_CI_CONFIG" > .gitlab-ci.yml
    fi
    git add .gitlab-ci.yml
    git commit -m "Add Semgrep to .gitlab-ci.yml"
    git push --set-upstream origin ADD_SEMGREP
    cd ..
done
