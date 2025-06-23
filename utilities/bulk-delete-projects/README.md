# Bulk Delete Projects Script

## What is it
This script will delete projects in bulk from the deployment specified by ORGSLUG, by looping over a CSV of Project Names, and hitting the `DELETE - Delete project` endpoint. Once complete, it will generate a log of what was deleted, and if there were any errors (as well as providing the realtime responses in your CLI).

## How to run
To run the script, you first need to create and populate an `input.csv` file with all the project names of the projects you want to delete. See the included `input.csv.example` file as an example.

You can use the `GET - List all projects` endpoint on the API to get these, but this will only return **scanned** projects, if you want to delete unscanned projects in bulk, you'll need to contact Semgrep Support to do this for you.

Now you've got the data, you need to setup the config at the top of the script - just add your Organization Slug to `ORGSLUG`, and your token to `BEARER_TOKEN` (must be authorised for the API) for the deployment.

Then, once that's done you're good to go!

CD to the scripts directory (`bulk-delete-projects`) and run it with the below command:

`python3 index.py` (may vary depending on which Python version you have installed).