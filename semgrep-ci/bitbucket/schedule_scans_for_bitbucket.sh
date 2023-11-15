#!/bin/bash

# This scripts needs to setup the next environment variables:
## SEMGREP_APP_TOKEN
## BITBUCKET_TOKEN
## BITBUCKET_USER
## BITBUCKET_WORKSPACE

repo_name_list=$(curl --request GET --url 'https://api.bitbucket.org/2.0/repositories/'${BITBUCKET_WORKSPACE} --header 'Authorization: Bearer '${BITBUCKET_TOKEN} --header 'Accept: application/json' | jq -r '.values[].name')
for repo_name in ${repo_name_list}; do
    echo "Scanning repo: ${repo_name}"
    rm -rf ${repo_name}
    git clone https://${BITBUCKET_USER}:${BITBUCKET_TOKEN}@bitbucket.org/${BITBUCKET_WORKSPACE}/${repo_name}.git
    cd ${repo_name}
    docker run -e SEMGREP_APP_TOKEN=$SEMGREP_APP_TOKEN  -e SEMGREP_REPO_NAME=${repo_name} -v "$(pwd):$(pwd)" --workdir $(pwd) returntocorp/semgrep semgrep ci || true
    cd ..
done
