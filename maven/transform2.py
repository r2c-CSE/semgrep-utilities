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
raw_output = result.stdout

# Function to determine if a line should be skipped
# Skips lines that are evicted (sometimes truncated) or end with ... (not a valid dependency)
def should_be_skipped(line):
    # This regex is short and simple because "evicted" is sometimes truncated
    # When revising, recommended to check behavior and performance with a regex tester
    return re.search(r'\(evi.+', line) or line.strip().endswith('...')

# Function to clean a line by removing [info] and [S] tags and trailing whitespace
def clean_line(line):
    return line.replace("[info]", "").replace("[S]", "").rstrip()

# Function to normalize the dependency text to the canonical Maven format
# Ensures that the dependency string has the form group:artifact:jar:version:scope
def normalize_dependency_text(dep_text):
    parts = dep_text.split(":")
    if len(parts) < 3:
        return dep_text  # Skip malformed line
    # Check if parts[2] matches the pattern: whitespace + bracket + (e|ev|.)
    # Example: com.fasterxml.jackson.core:jackson-databind:2.12.7.1 (..
    # will be discarded
    if re.search(r'\s[\(](e|ev|\.)', parts[2]):
        return None  # Evicted/truncated
    # Insert 'jar' and 'compile' if needed to match canonical format
    if len(parts) == 3:
        parts.insert(2, "jar")
        parts.append("compile")
    elif len(parts) == 4:
        parts.append("compile")
    return ":".join(parts)

# Main function to extract and transform only the relevant lines
def extract_and_transform_lines(raw_output):
    lines = raw_output.splitlines()

    # Locate start of dependency block
    # Find the index where the relevant lines start (after 'set current project to')
    start_index = next((i for i, line in enumerate(lines) if "set current project to" in line), 0)
    if start_index != 0:
        start_index += 1
    lines = lines[start_index:]

    transformed_lines = []

    for line in lines:
        line = line.strip("\n")
        # Filter out empty lines and the [success] line
        if not line or line.strip().startswith("[success]"):
            continue

        cleaned = clean_line(line)

        if should_be_skipped(cleaned):
            continue

        # Capture tree prefix (e.g., '    |  +-')
        prefix_match = re.match(r'^(\s*[| +\\-]+)', line)
        prefix = prefix_match.group(1) if prefix_match else ""

        # Remove prefix from dependency part
        dep_part = cleaned[len(prefix):].strip() if prefix else cleaned.strip()

        normalized = normalize_dependency_text(dep_part)
        if normalized:
            # These ensure that the spacing of the pipes and +- notations are correct/consistent
            # (from transform2.py)
            norm_line = f"{prefix}{normalized}"
            norm_line = norm_line.replace("+-", "+- ")
            norm_line = re.sub(r'\|\s+', "|  ", norm_line)
            if norm_line:
                transformed_lines.append(norm_line)

    return "\n".join(transformed_lines)

# Transform and print output
final_output = extract_and_transform_lines(raw_output)
print(final_output)
