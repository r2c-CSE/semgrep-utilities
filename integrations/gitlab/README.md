🧩 Semgrep → GitLab Security Reports Integration

This repository defines a GitLab CI/CD pipeline that retrieves findings from Semgrep Managed Scans (SMS) via API, transforms them into GitLab-compatible Security Report formats, and imports them into your GitLab project as native SAST and Dependency Scanning reports.

📋 Overview

The pipeline automates the following workflow:

Retrieve findings from Semgrep’s API using your deployment token.

Transform the Semgrep JSON reports into GitLab-compliant security report formats (gl-sast-report.json, gl-dependency-scanning-report.json).

Import those reports so that GitLab can display vulnerabilities in the Security tab of your project.

🏗️ Pipeline Stages
Stage	Purpose	Key Output

* retrieve	Fetch raw Semgrep findings from the API	sast-api-report.json, sca-api-report.json
* transform	Convert Semgrep API reports into GitLab-compatible formats	gl-sast-report.json, report-ssc.json
* import	Upload final reports to GitLab Security Dashboard
