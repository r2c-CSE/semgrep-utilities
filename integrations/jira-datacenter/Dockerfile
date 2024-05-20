FROM semgrep/semgrep:latest

COPY ./src /semgrep-sync-jira-server
COPY ./requirements.txt /semgrep-sync-jira-server/requirements.txt

WORKDIR /semgrep-sync-jira-server
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /src

CMD [ "sh", "-c", "semgrep ci --json -o semgrep-findings.json; semgrep_exit_code=$?; python /semgrep-sync-jira-server/sync.py -f ./semgrep-findings.json; exit $semgrep_exit_code" ]