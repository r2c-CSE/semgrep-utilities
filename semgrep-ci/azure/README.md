## Work Item creation script from an Azure Pipeline

This script must be placed in the azure-pipelines.yml logic.
It will create [Azure Work Items](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/about-work-items?view=azure-devops&tabs=agile-process).

The logic is that it starts the Azure pipeline and calls Semgrep to scan the diff. If there are some new findings related to rules in the comment or blocking mode then
a new work item is created.
The work item title will be the rule name.
In addition to that, the work item has the following information:
* Link to the code
* Link to the Semgrep finding
* Severity

To fill out the [Area Path](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/set-area-paths?view=azure-devops&tabs=browser) the script will read
a csv file from a specific repository that will match email and AreaPath. The email is the email author of the pull request.

