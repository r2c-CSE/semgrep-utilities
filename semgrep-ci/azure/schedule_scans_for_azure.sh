#!/bin/bash

# This scripts needs to setup the next environment variables:
## SEMGREP_APP_TOKEN
## AZURE_TOKEN
## AZURE_ORGANIZATION
## AZURE_PROJECT


echo 'https://dev.azure.com/'${AZURE_ORGANIZATION}'/'${AZURE_PROJECT}'/_apis/git/repositories'
repo_name_list=$(curl --request GET --url 'https://dev.azure.com/'${AZURE_ORGANIZATION}'/'${AZURE_PROJECT}'/_apis/git/repositories' --header 'Authorization: Bearer '${AZURE_TOKEN} --header 'Accept: application/json' | jq -r '.value[].name')
for repo_name in ${repo_name_list}; do
    echo "Scanning repo: ${repo_name}"
    rm -rf ${repo_name}
    git clone https://dev.azure.com/${AZURE_ORGANIZATION}/${AZURE_PROJECT}/_git/${repo_name}
    cd ${repo_name}
    docker run -e SEMGREP_APP_TOKEN=$SEMGREP_APP_TOKEN  -e SEMGREP_REPO_NAME=${repo_name} -v "$(pwd):$(pwd)" --workdir $(pwd) returntocorp/semgrep semgrep ci || true
    cd ..
done
