# Semgrep Sync Jira Server (aka Data Center!)

This project automates the process of syncing findings from Semgrep to Jira, creating Jira issues for actionable findings. It filters findings based on custom criteria, queries Jira to avoid duplicate issues, and batches queries for handling large jobs.

## Usage

These scripts are meant to used within your CI scan process with Semgrep.  It assumes that it's being run within a git repo - and can subsequently run `git` commands to figure out some details of the repo.  

This is designed to be supported by a service account on the Jira Server. Authentication is based on using an auth token, presented to the script via the env var `JIRA_TOKEN`.  

`src/config.py` is hopefully the only file you need to touch for simpler integrations.  Configure the variables at the top of the file along with the functions `finding_to_issue` and `filter_findings`.  

- `finding_to_issue`      This function configures the fields and values of the Jira issues to be created.
- `filter_findings`       This function is a filter for excluding findings you don't want to create issues for.

## Configuring `src/config.py`:
- `JIRA_SERVER`: Your Jira's HTTPS URL.
- `JIRA_PROJECT`: The Jira project key for where issues will be created.
- `JIRA_LABELS`: Any labels you want on all issues.
- `JIRA_ISSUE_TYPE`: Use a standard type like "Bug" or a custom types like "Security Issue".
- `JIRA_FINGERPRINT_FIELD`: Select a custom text field to store the finding fingerprint.  This value will look something like `customfield_10200`. 
- `finding_to_issue`: Modify this to format issues and map data fields - populate labels, custom fields, etc.
- `filter_findings`: Customize to filter the findings list to limit which findings create issues.

### Environment variables:
- `JIRA_TOKEN`: [PAT](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html) used query the Jira API.  Preferrably use a service account outside of testing.
- `SEMGREP_APP_TOKEN`: [API token](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables/#semgrep_app_token) for authenticating Semgrep scans.
- Optional: [any other environment variables](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables/#environment-variables-for-configuring-scan-behavior) for controlling the Semgrep scan.  Recommended `SEMGREP_REPO_DISPLAY_NAME` to set the project name in the Semgrep Cloud.

## Docker usage

The included `Dockerfile` will build on Semgrep's image to include these scripts and run them along with a Semgrep scan.  The docker command is designed to return the exit code from the Semgrep scan, regardless of whether the script errors.  

`sync.py` should always exit code 0 to be easy to use in CI pipelines.  

After customizing `config.py`, you can build a custom image with your settings by running:  
```
docker build --tag=semgrep-sync-jira .
```

Assuming you have a `$JIRA_TOKEN` and `$SEMGREP_APP_TOKEN` in your env, from within a repo you can run a semgrep scan + sync with the command:  
```
docker run --rm -v "${PWD}:/src" -e SEMGREP_REPO_DISPLAY_NAME="org_name/repo_name" -e SEMGREP_APP_TOKEN=$SEMGREP_APP_TOKEN -e JIRA_TOKEN=$JIRA_TOKEN -it semgrep-sync-jira
```

Use this command if you already have json output (`./semgrep-findings.json` in this example) from a Semgrep scan that you want to sync to Jira:
> Note you'll still want to run this from within a repo so that the script can use git commands to fetch repo details. 
```
docker run --rm -v "${PWD}:/src" -e JIRA_TOKEN=$JIRA_TOKEN -it semgrep-sync-jira python /semgrep-sync-jira-server/sync.py -f ./semgrep-findings.json
```




