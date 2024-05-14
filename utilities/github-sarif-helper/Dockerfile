# This Dockerfile is used to show how to base on the official semgrep image
# And include the script to convert semgrep json output to SARIF format

FROM semgrep/semgrep:latest

COPY ./src /transform/
WORKDIR /src

CMD [ "sh", "-c", "semgrep ci --json -o semgrep-findings.json; semgrep_exit_code=$?; python /transform/semgrep-json-to-sarif.py --json ./semgrep-findings.json --sarif ./semgrep-sarif.json; exit $semgrep_exit_code" ]

