#!/bin/zsh
# set -x

# Ensure script fails on unhandled errors and undefined variables
set -euo pipefail

# Verify we are inside a Git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Current directory is not a Git repository." >&2
    exit 1
fi

# Export environment variables from Git metadata
export SEMGREP_REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' || echo "")
export SEMGREP_COMMIT=$(git rev-parse HEAD)
export SEMGREP_BRANCH=$(git branch --show-current)
export SEMGREP_REPO_NAME=$(git remote get-url origin 2>/dev/null | sed -E -e 's#\.git$##' -e 's#^.*[:/]([^/:]+/[^/:]+)$#\1#' || echo "")
export SEMGREP_REPO_DISPLAY_NAME="${SEMGREP_REPO_NAME}"-LocalBuild


# Now run the local build
semgrep ci --allow-local-builds $@
