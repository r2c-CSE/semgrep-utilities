# github_recent_contributors.py
This script is meant to help estimate the number of contributors that are active within a Github organization over a period of time.

The script does not use exactly the same logic as Semgrep in determining active contributors but should be helpful in determining a rough estimate.

## Usage
You'll need to first export a [Github PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) into your environment for the script to use.

Export your PAT as the variable `GITHUB_PERSONAL_ACCESS_TOKEN`.  

Example: `export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_BunchOfSecretStuffGoesHere`

The Token will need the following scopes:
- repo
- read:org
- read:user
- user:email

The script takes the following arguements:
- The name of the github organization
- The number of days to look over (we recommend 90 as a safe default)
- An output filename to store the details from the execution

After you have the PAT in your environment, run this script like this:
```python3 github_recent_contributors.py r2c-cse 90 output.json```

## Output
Example console output:
```
Total commit authors in the last 90 days: 33
Total members in r2c-cse: 16
Total unique contributors from r2c-cse in the last 90 days: 5
```

Example output file:
```
{
    "organization": "r2c-cse",
    "date": "2023-09-26",
    "number_of_days_history": 90,
    "org_members": [
        ...
    ],
    "commit_authors": [
        ...
    ],
    "commiting_members": [
        ...
    ]
}
```