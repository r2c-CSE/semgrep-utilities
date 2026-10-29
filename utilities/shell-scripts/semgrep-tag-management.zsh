#!/usr/bin/env zsh

# Strict execution flags:
# -e : Exit immediately if a command exits with a non-zero status
# -u : Treat unset variables as an error
# -o pipefail : Return status of the last command in a pipeline that failed
set -euo pipefail

# Print help message
usage() {
  cat <<EOF >&2
Usage: $0 <METHOD> <DEPLOYMENT_NAME> <PROJECT_NAME> [TAG1 TAG2 ...]

Description:
  Performs an API request against a Semgrep project's tags endpoint.

Arguments:
  METHOD           HTTP verb to use (PUT | DELETE | GET)
  DEPLOYMENT_NAME  Name of the Semgrep deployment
  PROJECT_NAME     Name of the project (e.g. Org/Repo)
  TAG1 TAG2 ...    Tags to apply (Required for PUT/DELETE, ignored for GET)

Environment Variables:
  SEMGREP_APP_TOKEN  (Required) Bearer token for Semgrep API authorization.

Examples:
  $0 PUT csmonkee CSMonkee-Org/WebGoat-LocalBuild ALB-Java API-Applied-Tag
  $0 GET csmonkee CSMonkee-Org/WebGoat-LocalBuild
  $0 DELETE csmonkee CSMonkee-Org/WebGoat-LocalBuild ALB-Java
EOF
  exit 1
}

# 1. Validate environment prerequisites
if [[ -z "${SEMGREP_APP_TOKEN:-}" ]]; then
  echo "Error: SEMGREP_APP_TOKEN environment variable is not set." >&2
  exit 1
fi

# 2. Validate argument count
if (($# < 3)); then
  echo "Error: Invalid number of arguments." >&2
  usage
fi

# Convert HTTP method to uppercase
HTTP_METHOD="${1:u}"
DEPLOYMENT_NAME="$2"
PROJECT_NAME="$3"
shift 3  # Remove METHOD, DEPLOYMENT_NAME, and PROJECT_NAME from argument list

# Validate HTTP verb
case "$HTTP_METHOD" in
  GET|PUT|DELETE) ;;
  *)
    echo "Error: Invalid HTTP verb '$HTTP_METHOD'. Allowed values: PUT, DELETE, GET." >&2
    exit 1
    ;;
esac

# 3. Determine correct URL endpoint based on HTTP method
URL_ENDPOINT="https://semgrep.dev/api/v1/deployments/${DEPLOYMENT_NAME}/projects/${PROJECT_NAME}"
if [[ "$HTTP_METHOD" != "GET" ]]; then
  URL_ENDPOINT+="/tags"
fi

# Construct curl command arguments as an array
CURL_ARGS=(
  --silent
  --show-error
  --write-out "\nHTTP_STATUS:%{http_code}"
  --request "$HTTP_METHOD"
  --url "$URL_ENDPOINT"
  --header "Authorization: Bearer ${SEMGREP_APP_TOKEN}"
  --header "Content-Type: application/json"
)

# 4. Handle payload for methods that accept body data (PUT, DELETE)
if [[ "$HTTP_METHOD" != "GET" ]]; then
  TAGS_ARRAY=()
  for tag in "$@"; do
    [[ -z "$tag" ]] && continue
    # Escape quotes and backslashes for valid JSON string encoding
    escaped_tag=$(printf '%s' "$tag" | sed 's/\\/\\\\/g; s/"/\\"/g')
    TAGS_ARRAY+=("\"${escaped_tag}\"")
  done

  if ((${#TAGS_ARRAY} == 0)); then
    echo "Error: At least one non-empty tag must be provided for $HTTP_METHOD request." >&2
    exit 1
  fi

  # Join array elements with commas
  TAGS_JSON=$(printf ',%s' "${TAGS_ARRAY[@]}")
  TAGS_JSON="[${TAGS_JSON:1}]"

  PAYLOAD="{\"tags\": ${TAGS_JSON}}"
  
  # Append --data flag to curl arguments
  CURL_ARGS+=(--data "$PAYLOAD")
fi

# 5. Perform API Request
echo "Sending ${HTTP_METHOD} request to ${URL_ENDPOINT}..." >&2

RESPONSE=$(curl "${CURL_ARGS[@]}")

# Extract HTTP status code and response body
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | awk -F':' '{print $2}')
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

# 6. Check API status code
if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 300 ]]; then
  echo "Success (HTTP $HTTP_STATUS): ${HTTP_METHOD} request completed." >&2
  if [[ -n "$BODY" ]]; then
    echo "$BODY"
  fi
else
  echo "Error (HTTP $HTTP_STATUS): API request failed." >&2
  if [[ -n "$BODY" ]]; then
    echo "Response: $BODY" >&2
  fi
  exit 1
fi
