import sys
import re

def parse_csproj(filename):
    references = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith('<Reference Include='):
                references.append(line)
    return references

def extract_package_info(reference_line):
    match = re.match(r'<Reference Include="([^,]+)(?:, Version=([^,]+))?.*"', reference_line)
    if match:
        package_name = match.group(1)
        version = match.group(2)
        if version:
            return f'<PackageReference Include="{package_name}" Version="{version}" />'
        else:
            return f'<PackageReference Include="{package_name}" />'
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python transform.py <csproj-file>")
        return
    
    filename = sys.argv[1]
    references = parse_csproj(filename)
    
    package_references = []
    for reference in references:
        package_info = extract_package_info(reference)
        if package_info:
            package_references.append(package_info)
        else:
            print(f'Pattern did not match: {reference}')

    if not package_references:
        print("No valid package references found.")
        return

    with open(filename, 'r') as file:
        content = file.read()

    itemgroup_index = content.find('<ItemGroup>')
    if itemgroup_index == -1:
        print("No <ItemGroup> tag found in the file.")
        return

    itemgroup_end_index = content.find('>', itemgroup_index) + 1

    new_content = content[:itemgroup_end_index] + '\n    ' + '\n    '.join(package_references) + content[itemgroup_end_index:]

    with open(filename, 'w') as file:
        file.write(new_content)

    print("Package references added successfully.")

if __name__ == "__main__":
    main()
