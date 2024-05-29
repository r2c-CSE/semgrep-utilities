# Semgrep Data Mapper

## Description
This repository is a tool for formatting Semgrep data to make reporting and analysis easier. It has utilities for normalizing and flattening Semgrep scan and rule data into CSV format for reporting purposes. It is designed to streamline the process of extracting actionable insights from Semgrep outputs.

## Prerequisites
Before you run this tool, ensure you have the following installed:
- Python 3.7 or higher
- [pipenv](https://pypi.org/project/pipenv/)

## Usage
Run either with pipenv or with Docker.

### Pipenv
You can run an export of your rules/findings data with `pipenv run python ./src/map_semgrep_data.py`.

The scripts look for Semgrep token in the `SEMGREP_APP_TOKEN` environment variable [just like Semgrep](https://semgrep.dev/docs/semgrep-ci/ci-environment-variables#semgrep_app_token)!  

They will fetch, normalize, cross-reference, and export data from the [Semgrep API's](https://semgrep.dev/api/v1/docs/#section/Introduction) and export them as csv's in the `data/` directory.  

### Docker
Build a docker image: `docker build -t semgrep-data-mapper .`
Run the container, write output into the current directory: `docker run -e SEMGREP_APP_TOKEN -v ./:/src/data semgrep-data-mapper`

## Errors
Errors logged to the console during runs indicate minor issues where some data wasn't able to be mapped.  

It may be from where a rule is missing a metadata field or a specific finding type is missing data available from the other finding types.