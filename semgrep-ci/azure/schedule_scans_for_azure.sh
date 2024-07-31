#!/bin/bash

# This scripts needs to setup the next environment variables:
## SEMGREP_APP_TOKEN
## AZURE_TOKEN
## AZURE_ORGANIZATION
## AZURE_PROJECT

# Define the list of repository names
repo_name_list=$(curl -H "Authorization: Basic $(echo -n ":${AZURE_TOKEN}" | base64)" --request GET --url 'https://dev.azure.com/'${AZURE_ORGANIZATION}'/'${AZURE_PROJECT}'/_apis/git/repositories' | jq -r '.value[].name')
lockfile=false
root_dir=$(pwd)

# Read the CSV file into a list
inactive_repos=$(awk -F";" '{print $1}' InactiveProjects.csv)

# Convert the list to a space-separated string
inactive_repos_list=$(echo ${inactive_repos} | tr '\n' ' ')

# Function to process csproj files
process_csproj_files() {
    current_dir=$(pwd)
    find_out=$(find . -type f -name '*.csproj')
    filtered_out=$(echo "$find_out" | grep -v '^./*.csproj$' || true)
    if [ -n "$filtered_out" ]; then
        sed_out=$(echo "$filtered_out" | sed 's|^\./||')
        csproj=$(echo "$sed_out" | xargs -I {} dirname {} | sort | uniq)
    fi
    if [ -n "$csproj" ]; then
        for dir in $csproj; do
            cd $dir && dotnet restore -p:RestorePackagesWithLockFile=True && cd $current_dir
            if [ -f "$dir/packages.lock.json" ]; then
                echo "Successfully generated $dir/packages.lock.json"
                lockfile=true
            else
                echo "Failed to generate $dir/packages.lock.json"
            fi
        done
        #restoring the variable
        csproj=""
    fi
}

# Function to transform csproj files
transform_csproj_files() {
    find_out=$(find . -type f -name '*.csproj')
    for file in $find_out; do
        python3 $root_dir/transform.py $file
    done
}

# Iterate through the list and perform actions
for repo_name in ${repo_name_list}; do

    # Check if repo_name is in the inactive list
    if echo ${inactive_repos_list} | grep -w -q ${repo_name}; then
        echo "Skipping inactive repo: ${repo_name}"
        continue
    fi
    echo "Scanning repo: ${repo_name}"
    rm -rf ${repo_name}
    git clone https://${AZURE_TOKEN}@dev.azure.com/${AZURE_ORGANIZATION}/${AZURE_PROJECT}/_git/${repo_name} > /dev/null 2>&1 || true
    cd ${repo_name}
    lockfile=false
    # Call the function to process csproj files
    process_csproj_files

    if [ "$lockfile" = false ]; then
        transform_csproj_files
        process_csproj_files
    fi
    
    ## Javascript lock files
    if [ -f "./package.json" ]; then
        echo "NPM. Generating lock file"
        npm i --package-lock-only > /dev/null 2>&1 || true
    fi

    ## Java Maven lockfile
    # Check if pom.xml exists in the current directory
    if [ -f "./pom.xml" ]; then
        echo "Maven. Generating dependency tree for the root project"
        mvn dependency:tree -DoutputFile=maven_dep_tree.txt > /dev/null 2>&1 || true
    fi

    ## Java Gradle lockfile
    # Check if pom.xml exists in the current directory
    if [ -f "./build.gradle" ]; then
        echo "Gradle. Generating dependency tree for the root project"
        gradle dependencies --write-locks > /dev/null 2>&1 || true
    fi

    ## Scala lockfile
    if [ -f "./build.sbt" ]; then
        sbt "set asciiGraphWidth := 9999" "dependencyTree::toFile maven_dep_tree.txt -f" > /dev/null 2>&1 || true
        curl -O https://raw.githubusercontent.com/r2c-CSE/semgrep-utilities/main/maven/transform2.py > /dev/null 2>&1
        echo "Scala. Generating dependency tree for the root project"
        python3 transform2.py maven_dep_tree.txt > maven_dep_tree_copy.txt
        mv maven_dep_tree_copy.txt maven_dep_tree.txt
        if [ -f "maven_dep_tree.txt" ]; then
            echo "Successfully generated maven_dep_tree.txt for Scala"
        else
            echo "Failed to generate maven_dep_tree.txt for Scala"
        fi
    fi

    export SEMGREP_REPO_DISPLAY_NAME=${repo_name}
    semgrep ci || true 
    cd ..
    echo "deleting ${repo_name}"
    rm -rf ${repo_name}
done




