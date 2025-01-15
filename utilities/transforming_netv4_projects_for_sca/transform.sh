#!/bin/bash

# Function to process csproj files
process_csproj_files() {
    current_dir=$(pwd)
    find_out=$(find . -type f -name '*.csproj')
    filtered_out=$(echo "$find_out" | grep -v '^./*.csproj$' || true)
    if [ -z "$filtered_out" ]; then
        echo "No submodule *.csproj files found after filtering. Skipping submodule processing."
    else
        sed_out=$(echo "$filtered_out" | sed 's|^\./||')
        csproj=$(echo "$sed_out" | xargs -I {} dirname {} | sort | uniq)
    fi
    if [ -z "$csproj" ]; then
        echo "No *.csproj files found. Skipping submodule processing."
    else
        for dir in $csproj; do
            cd $dir && dotnet restore -p:RestorePackagesWithLockFile=True > /dev/null 2>&1 || true && cd $current_dir
            if [ -f "$dir/packages.lock.json" ]; then
                echo "Successfully generated $dir/packages.lock.json"
                lockfile=true
            else
                echo "Failed to generate $dir/packages.lock.json"
            fi
        done
    fi
}

# Function to transform csproj files
transform_csproj_files() {
    find_out=$(find . -type f -name '*.csproj')
    for file in $find_out; do
        python3 $root_dir/transform.py $file
    done
}

root_dir=$(pwd)
lockfile=false
# Call the function to process csproj files
process_csproj_files

if [ "$lockfile" = false ]; then
    echo "No lock file has been generated for the project: ${repo_name}"
    transform_csproj_files
     process_csproj_files
fi
