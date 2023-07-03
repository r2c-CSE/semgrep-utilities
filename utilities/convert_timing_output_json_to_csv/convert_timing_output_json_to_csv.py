import json
import csv
import os



def convert_timing_output_json_to_csv():


    current_path = os.getcwd()
    relative_path = "/utilities/convert_timing_output_json_to_csv"

    new_file_path = current_path + relative_path + "/output/" + "output-paths.csv" 

    # Open the file in write mode using 'w'
    output_file_paths = open(new_file_path, "w")
    writer_paths = csv.writer(output_file_paths)
    writer_paths.writerow(["path", "run_time"])

    new_file_rules = current_path + relative_path + "/output/" + "output-rules-list.csv" 
    output_file_rules = open(new_file_rules, 'w', newline='')
    writer_rules = csv.writer(output_file_rules)
    writer_rules.writerow(["rule", "rule_time"])

    input_file = open(current_path + relative_path  + "/input/" + "timing.json", "r")
    content = json.loads(input_file.read())
    for file in content['time']['targets']:
        writer_paths.writerow([file['path'],file['run_time']])

    rule_counter = 0
    for rule in content['time']['rules']:
        rule_time = 0
        for file in content['time']['targets']:
            rule_time = rule_time + file['match_times'][rule_counter] + file['parse_times'][rule_counter]
        writer_rules.writerow([rule.get('id'),rule_time])   
        rule_counter = rule_counter + 1
    
    print("config_time: " + str(content['time']['profiling_times']['config_time']))
    print("core_time: " + str(content['time']['profiling_times']['core_time']))
    print("ignores_time: " + str(content['time']['profiling_times']['ignores_time']))
    print("total_time: " + str(content['time']['profiling_times']['total_time']))

    output_file_paths.close()
    output_file_rules.close()


if __name__ == '__main__':
    convert_timing_output_json_to_csv()