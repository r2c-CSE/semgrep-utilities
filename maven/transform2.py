import subprocess
import re
import sys

# Check for correct usage and print usage instructions if needed
if len(sys.argv) != 2:
    print("Usage: python transform2.py <path_to_maven_dep_tree.txt file>")
    sys.exit(1)
    
file_path = sys.argv[1]

# Read file contents using subprocess (to allow for future flexibility, e.g., piping)
result = subprocess.run(["cat", file_path], capture_output=True, text=True)

# Assign the output to actual_lines
actual_lines = result.stdout

# Function to determine if a line should be skipped
# Skips lines that are evicted (sometimes truncated) or end with ... (not a valid dependency)
def should_be_skipped(line):
    # This regex is short and simple because "evicted" is sometimes truncated
    # When revising, recommended to check behavior and performance with a regex tester
    return re.search(r'\(e.*', line) or re.search(r'\.\.+$', line)

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

def transform_lines_with_space(original):
    lines = original.strip().split("\n")
    transformed_lines = []
    root_seen = False

    for line in lines:
        original_line = line  # for calculating indent
        clean_line = line.replace("[info]", "").replace("[S]", "").strip()
        if re.match(r'^[\|\+\-\s]+$', clean_line) or clean_line == "" or should_be_skipped(clean_line):
            continue

        # Calculate indentation depth (each 2 spaces == 1 level)
        indent_match = re.match(r'^([ |]+)\+-', line)
        if indent_match:
            indent_str = indent_match.group(1)
            depth = indent_str.count('|') + indent_str.count('  ')
        else:
            depth = 0

        # Clean the line from old tree characters
        line_content = re.sub(r'^[\|\+\-\s]+', '', clean_line)

        parts = line_content.split(':')
        if len(parts) >= 3:
            if re.search(r'\s[\(](e|ev|\.)', parts[2]):
                continue
            parts.insert(2, 'jar')
            parts.append('compile')
            formatted_line = ':'.join(parts)

            if not root_seen:
                transformed_lines.append(formatted_line)
                root_seen = True
            else:
                prefix = "|  " * (depth - 1) + "+- " if depth > 0 else "+- "
                transformed_lines.append(prefix + formatted_line)

    return "\n".join(transformed_lines)


# Print the transformed output with correct spacing
final_transformed_output = extract_and_transform_lines(actual_lines)
print(final_transformed_output)
