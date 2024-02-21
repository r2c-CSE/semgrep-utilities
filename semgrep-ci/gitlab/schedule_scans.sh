#!/bin/bash

# This scripts needs to setup the next environment variables:
## SEMGREP_APP_TOKEN
## GITLAB_ACCESS_TOKEN
## GITLAB_USER_ID

# GitLab API URL to fetch repositories
API_URL="https://gitlab.com/api/v4/users/${GITLAB_USER_ID}/projects?private_token=${GITLAB_ACCESS_TOKEN}&simple=true&per_page=100"

# Cloning directory
CLONE_DIR="./gitlab_repos"
mkdir -p "${CLONE_DIR}"
cd "${CLONE_DIR}"

# Fetch and clone repositories
curl --header "PRIVATE-TOKEN: ${GITLAB_ACCESS_TOKEN}" "${API_URL}" | jq -r '.[] | .http_url_to_repo' | while read gitlab_repo_url; do
  repo_name=$(basename -s .git "${gitlab_repo_url}")
  rm -rf ${repo_name}
  echo "cloning ${gitlab_repo_url}"
  repo_url="${gitlab_repo_url/https:\/\//}"
  git clone https://oauth2:${GITLAB_ACCESS_TOKEN}@${repo_url}
  echo "Scanning repository name: $repo_name"
  cd ${repo_name}
  docker run -e SEMGREP_APP_TOKEN=$SEMGREP_APP_TOKEN -v "$(pwd):$(pwd)" --workdir $(pwd) returntocorp/semgrep semgrep ci || true
  cd ..
done
