import subprocess
import re
import sys

if len(sys.argv) != 2:
    print("Usage: python transform2.py <path_to_maven_dep_tree.txt file>")
    sys.exit(1)
    
file_path = sys.argv[1]

# Run the sbt dependencyTree command and capture the output
result = subprocess.run(["cat", file_path], capture_output=True, text=True)

# Assign the output to actual_lines
actual_lines = result.stdout
# Function to extract and transform only the relevant lines
def extract_and_transform_lines(actual):
    # Split the actual input into lines
    lines = actual.strip().split("\n")
    # Find the index where the relevant lines start
    start_index = next((i for i, line in enumerate(lines) if "set current project to" in line), 0)
    if start_index != 0:
        start_index += 1
    # Extract the relevant lines
    relevant_lines = lines[start_index:]
    # Filter out empty [info] lines and the [success] line
    relevant_lines = [line for line in relevant_lines if line.strip() and not line.startswith("[success]")]
    # Transform the lines using the previously defined function
    transformed_lines = transform_lines_with_space("\n".join(relevant_lines))
    
    return transformed_lines

# Function to transform lines with correct spacing
def transform_lines_with_space(original):
    lines = original.strip().split("\n")
    transformed_lines = []

    for line in lines:
        line = line.replace("[info]", "").replace("[S]", "").strip()
        # Skip lines that contain only pipes and spaces or empty lines
        if re.match('^[ |]+$', line) or line == "":
            continue
        # Skip "evicted" dependencies as they are superseded by a different version
        # This regex is short and simple because "evicted" is sometimes truncated
        # When revising, recommended to check behavior and performance with a regex tester
        if re.search(r'\(evi.+', line):
            continue
        parts = line.split(':')
        if len(parts) > 2:
            parts.insert(2, 'jar')
            parts.append('compile')
            line = ':'.join(parts)
        # These ensure that the spacing of the pipes and +- notations are correct/consistent
        line = line.replace("+-", "+- ")
        line = re.sub(r'\|\s+', "|  ", line)
        # Add the line to the list if it's not empty
        if line:
            transformed_lines.append(line)
    
    return "\n".join(transformed_lines)

# Print the transformed output with correct spacing
final_transformed_output = extract_and_transform_lines(actual_lines)
print(final_transformed_output)
