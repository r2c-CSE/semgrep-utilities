# Compare Semgrep Findings
This utility is designed to help compare the results of 2 distinct semgrep scans.  

It's a cli script that takes in 2 path arguments of Semgrep scan json output files and creates an html file comparing the results.

## Installation
- Have or install node.js
- Clone this repo
- Run npm install
```shell
npm install
```

## Usage
Run the script and review the generated html (it will look like `findings-compared-YYYY-MM-dd.hh.mm.ss.html`)
```shell
node ./compare-findings.js ./example-findings-oss.json ./example-findings-pro.json
```
