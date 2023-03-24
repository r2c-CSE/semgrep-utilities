import json
import csv

def convert():

    output_file = open('output-paths.csv', 'w', newline='')
    writer_paths = csv.writer(output_file)
    writer_paths.writerow(["path", "run_time"])

    output_file_rules = open('output-rules-list.csv', 'w', newline='')
    writer_rules = csv.writer(output_file_rules)
    writer_rules.writerow(["rule", "rule_time"])

    f = open('error.json')
    content = json.loads(f.read())
    for file in content['time']['targets']:
        writer_paths.writerow([file['path'],file['run_time']])

    for file in content['time']['rules']:
        writer_rules.writerow([file['id']])

if __name__ == '__main__':
    convert()