usage: Semgrep Rule CWE Extractor [-h] [-c CSV] dirs [dirs ...]

Searches dirs recursively for Semgrep Rule files with .yaml or .yml extension.
Extracts all CWEs from each rule's metadata and removes duplicates. Prints
list of CWE IDs to standard out or to CSV file

positional arguments:
  dirs               One or more directories that will be recursively searched
                     for Semgrep Rules

options:
  -h, --help         show this help message and exit
  -c CSV, --csv CSV  Filename to output list of CWEs in single row CSV format
