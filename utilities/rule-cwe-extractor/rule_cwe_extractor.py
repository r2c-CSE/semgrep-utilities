import os
import yaml
import re
import argparse
import csv

def main():
    parser = argparse.ArgumentParser(prog='Semgrep Rule CWE Extractor',
                    description="Searches dirs recursively for Semgrep rule files with .yaml or .yml extension. Extracts all CWEs from each rule's metadata and removes duplicates. Prints list of CWE IDs to standard out or to CSV file");

    parser.add_argument("dirs", nargs='+', help="One or more directories that will be recursively searched for Semgrep Rules")
    parser.add_argument("-c", "--csv", type=str, help="Filename to output list of CWEs in single row CSV format")

    args = parser.parse_args()
    search_dirs = args.dirs
    cwe_list = []

    for dir in search_dirs:
        if not os.path.isdir(dir):
            raise ValueError("The path provided " + dir + " is not a valid directory path.")

        yaml_files = find_yaml_files(dir)

        cwe_list = []

        for yaml_file in yaml_files:
            yaml_data = parse_yaml_file(yaml_file)
            if yaml_data is not None:
                cwe_list += get_cwe_list_from_semgrep_yaml(yaml_data)
    
    cwe_list = sorted(unique(cwe_list), key= lambda x: int(x))

    if (args.csv):
        with open(args.csv, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["CWE"])
            for cwe in cwe_list:
                csv_writer.writerow([f"{cwe}"])

        print(f"CSV file '{args.csv}' was created.")
        return

    print(cwe_list)

def find_yaml_files(directory):
    yaml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def parse_yaml_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)
            return yaml_data
    except Exception as e:
        print(f"Error parsing '{file_path}': {e}")
        return None

def get_cwe_list_from_semgrep_yaml(yaml_data):
    raw_cwes = []

    if not "rules" in yaml_data:
        return raw_cwes
    
    for rule in yaml_data['rules']:
        if 'metadata' in rule and 'cwe' in rule['metadata']:
            cwe_value = rule['metadata']['cwe']

            if isinstance(cwe_value, list):
                raw_cwes = raw_cwes + cwe_value
            else:
                raw_cwes = raw_cwes + [cwe_value]

    return list(map(get_cwe_number, raw_cwes))


def get_cwe_number(raw_cwe):
    # Define a regular expression pattern to match CWE numbers
    cwe_pattern = r'CWE-(\d+)'

    # Use re.search to find the first match of the pattern in the string
    match = re.search(cwe_pattern, raw_cwe)
    match = re.search(r'\d+', match.group())
    if not match:
       return
       
    return match.group()


def unique(value_list):
    return list(set(value_list))

if __name__ == "__main__":
    main()