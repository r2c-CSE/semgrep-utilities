import json
import argparse

def modify_schema(string_to_add, new_type_value, description):
    schema = {
         "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://gitlab.com/gitlab-org/security-products/security-report-schemas/-/raw/master/dist/dependency-scanning-report-format.json",
        "title": "Report format for GitLab Dependency Scanning",
        "description": "This schema provides the the report format for Dependency Scanning analyzers (https://docs.gitlab.com/ee/user/application_security/dependency_scanning).",
        "allOf": [
            { "$ref": "security-report-format.json" },
            {
                "properties": {
                    "scan": {
                        "properties": {
                            "type": {
                                "enum": ["dependency_scanning"]
                            }
                        }
                    }
                }
            },
            {
                "properties": {
                    "dependency_files": {
                        "type": "array",
                        "description": "List of dependency files identified in the project.",
                        "items": {
                            "$ref": "security-report-format.json#/definitions/dependency_file"
                        }
                    }
                },
                "required": [ "dependency_files" ]
            },
            {
                "properties": {
                    "vulnerabilities": {
                        "items": {
                            "properties": {
                                "location": { "$ref": "#/definitions/location" }
                            },
                            "required": [ "location" ]
                        }
                    }
                }
            }
        ],
        "definitions": {
            "location": {
                "type": "object",
                "description": "Identifies the vulnerability's location.",
                "properties": {
                    "file": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Path to the manifest or lock file where the dependency is declared (such as yarn.lock)."
                    },
                    "dependency": {
                        "$ref": "security-report-format.json#/definitions/dependency"
                    }
                },
                "required": [ "file", "dependency" ]
            }
        }
    }

    def add_value_to_required_key(schema_dict, string_to_add, new_type_value, description, indent=0):
        for key, value in schema_dict.items():
            if key == 'required' and 'dependency_files' in value:
                value.append(string_to_add)
            
            # Check for 'type' keys with a string value and set to new_type_value
            if key == 'type' and isinstance(value, str):
                schema_dict[key] = new_type_value
            
            #Check for 'type' key with a string value and set to description
            if key == 'description' and isinstance(value, str) and "Identifies the vulnerability's location." in value:
                schema_dict[key] = value.replace("Identifies the vulnerability's location.", description)
            
            #Check for 'type' key with a string value and set to reachable

            if isinstance(value, dict):
                add_value_to_required_key(value, string_to_add, new_type_value, description, indent+1)
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, dict):
                        add_value_to_required_key(item, string_to_add, new_type_value, description, indent+1)
    add_value_to_required_key(schema, string_to_add, new_type_value, description)

    # Save the modified schema to a file
    with open('gitlab.json.json', 'w') as f:
        json.dump(schema, f, indent=4)  # pretty print JSON

import argparse
import json

def parse_sarif_file(filename):
    # Read and parse the JSON from a file
    with open(filename, 'r') as file:
        data = json.load(file)

    # Accessing some elements in the parsed JSON
    for run in data['runs']:
        print('Tool name:', run['tool']['driver']['name'])
        print('Semantic Version:', run['tool']['driver']['semanticVersion'])
        print()

        for result in run['results']:
            print('Fingerprints:', result['fingerprints'])
            print('Location URI:', result['locations'][0]['physicalLocation']['artifactLocation']['uri'])
            print('Message:', result['message']['text'])
            print('Properties:', result['properties'])
            print('RuleId:', result['ruleId'])
            print()
            description = result['message']['text']
            new_type_value = result['locations'][0]['physicalLocation']['artifactLocation']['uri']
            modify_schema(result['locations'][0]['physicalLocation']['artifactLocation']['uri'], new_type_value, description)

# Create the parser and add argument
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="The name of the file to be parsed")

# Parse the arguments
args = parser.parse_args()

# Use the function with the filename as an argument
parse_sarif_file(args.filename)




