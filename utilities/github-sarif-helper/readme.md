# Findings > Sarif
This is a utility for taking a semgrep findings json and converting it to a sarif file for the Github security dashboard.

While you'd be right in thinking you don't need one because semgrep supports `--sarif` - that doesn't give you control of which findings you actual want in your sarif nor does it fill in all of the Github specific fields.

In the stock configuration, the utility will respect your [semgrep policy](https://semgrep.dev/docs/semgrep-code/policies) and only upload results that are configured to comment or block (from Semgrep Code or Secrets) or considered Reachable by Semgrep Supply Chain.

The `./src/semgrep-json-to-sarif.py` script does the heavy lifting while the included dockerfile shows an example of how to combine this with a Semgrep scan.

The script takes 2 optional args: `--json` to specify a source json file and `--sarif` to specify the sarif to be created.

Example:
```semgrep-json-to-sarif.py --json ./semgrep-findings.json --sarif ./semgrep-sarif.json```

The resulting sarif file can then be [uploaded to Github](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github).
