import subprocess
import re
import sys

if len(sys.argv) != 2:
    print("Usage: python transform2.py <path_to_maven_dep_tree.txt file>")
    sys.exit(1)

file_path = sys.argv[1]

# Read file contents
result = subprocess.run(["cat", file_path], capture_output=True, text=True)
raw_output = result.stdout

def should_be_skipped(line):
    return re.search(r'\(evi.+', line) or line.strip().endswith('...')

def clean_line(line):
    return line.replace("[info]", "").replace("[S]", "").rstrip()

def normalize_dependency_text(dep_text):
    parts = dep_text.split(":")
    if len(parts) < 3:
        return dep_text  # Skip malformed line
    if re.search(r'\s[\(](e|ev|\.)', parts[2]):
        return None  # Evicted/truncated
    # Insert jar and compile if needed
    if len(parts) == 3:
        parts.insert(2, "jar")
        parts.append("compile")
    elif len(parts) == 4:
        parts.append("compile")
    return ":".join(parts)

def extract_and_transform_lines(raw_output):
    lines = raw_output.splitlines()

    # Locate start of dependency block
    start_index = next((i for i, line in enumerate(lines) if "set current project to" in line), 0)
    if start_index != 0:
        start_index += 1
    lines = lines[start_index:]

    transformed_lines = []

    for line in lines:
        line = line.strip("\n")
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
            transformed_lines.append(f"{prefix}{normalized}")

    return "\n".join(transformed_lines)

# Transform and print output
final_output = extract_and_transform_lines(raw_output)
print(final_output)
