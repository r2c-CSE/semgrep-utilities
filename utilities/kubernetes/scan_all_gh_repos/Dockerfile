# Use a base image with Python installed
FROM semgrep/semgrep

# Set the working directory in the container
WORKDIR /app

# Copy the Python file into the container at /app
COPY scan.py .

# Set the entry point to execute the Python script
ENTRYPOINT ["python", "scan.py"]
