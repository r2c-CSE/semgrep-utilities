import re
import json
import sys
import os
from collections import OrderedDict

def parse_license_info(text_block):
    # Take the Semgrep CLI text output and split into lines
    lines = text_block.strip().splitlines()
    
    # Find the line where the license findings begin and get the index
    for i, line in enumerate(lines):
        if "Semgrep Supply Chain found the following packages with blocked licenses:" in line:
            # Start parsing from the next line onwards
            parsing_lines = lines[i + 1:]
            break
    else:
        # Let the user know no license violations were found and exit the script
        print("No license violations detected.")
        sys.exit(0)
    
    # Join the relevant lines for regex parsing
    relevant_text = "\n".join(parsing_lines)
    
    # Regular expression pattern to capture package, version, license, and file/line
    pattern = r'(.+?)\s(.+?)\swith\slicense\s(.+?)\sat\s(.+:\d+)'
    
    # Find all matches in the relevant text
    matches = re.findall(pattern, relevant_text)
    
    # Create a list to hold parsed information
    parsed_info = []
    
    # Loop through matches and store in a more structured format
    for match in matches:
        package_name = match[0]
        version = match[1]
        license_type = match[2]
        file_line = match[3]
        
        # Append to parsed_info list with lowercase keys and underscores
        parsed_info.append({
            'package': package_name,
            'version': version,
            'license': license_type,
            'file_and_line': file_line
        })
    
    return parsed_info

def append_to_json_file(data, file_path):
    # Check if the file exists
    if os.path.exists(file_path):
        # Read existing data from the JSON file
        with open(file_path, 'r') as json_file:
            try:
                existing_data = json.load(json_file, object_pairs_hook=OrderedDict)
            except json.JSONDecodeError:
                print("Error: Invalid JSON file format.")
                sys.exit(1)
    else:
        print("Error: File does not exist.")
        sys.exit(1)

    # Check if the 'results' key exists
    if "results" not in existing_data or not isinstance(existing_data["results"], list):
        print("Error: Invalid JSON file format. The 'results' key must be a list.")
        sys.exit(1)

    # Always overwrite the 'license_violations' key
    existing_data["license_violations"] = data

    # Create a new ordered dictionary to maintain the order
    new_data = OrderedDict()

    # Insert keys while preserving the order
    for key, value in existing_data.items():
        new_data[key] = value
        if key == "results":
            # Immediately after 'results', add 'license_violations'
            new_data["license_violations"] = data

    # Write updated data back to the JSON file, overwriting existing contents
    with open(file_path, 'w') as json_file:
        json.dump(new_data, json_file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_existing_json_file>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    
    # Read the text block from standard input
    text_block = sys.stdin.read()
    
    try:
        # Parse the text block if the preceding line is correct
        parsed_data = parse_license_info(text_block)

        # Append the parsed data to the specified JSON file
        append_to_json_file(parsed_data, json_file_path)

        print(f"License violations written to '{json_file_path}'")

    except ValueError as e:
        print(f"Error: {e}")
