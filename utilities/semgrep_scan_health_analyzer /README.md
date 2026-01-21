# Semgrep Full Scan Health Analysis Tool

This tool analyzes Semgrep scan data across all repositories in your organization, providing insights into full scan success rates metrics.

## Features

- Fetches scan data for all repositories in your Semgrep organization
- Generates detailed scan reports in both CSV and Excel formats
- Calculates repository health metrics including scan failure rates
- Provides color-coded health summary in Excel
- Supports pagination for large datasets
- Properly formatted Excel output with correct data types
- Organized report storage in a dedicated reports directory

## Output Files

The script generates three files (with timestamps) in a `reports` directory:

1. `semgrep_scans_<timestamp>.csv`: Detailed list of all scans
2. `repo_scan_health_summary_<timestamp>.csv`: Repository health metrics
3. `semgrep_scans_<timestamp>.xlsx`: Excel workbook containing:
   - Sheet 1: "Semgrep Scans" - Detailed scan data
   - Sheet 2: "Repo Health Summary" - Color-coded health metrics

## Prerequisites

- Python 3.6 or higher
- Semgrep API access
- Required environment variables (see Configuration section)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:

```bash
export SEMGREP_API_TOKEN="your-api-token"
export SEMGREP_ORG_ID="your-org-id"
export SEMGREP_DEPLOYMENT_SLUG="your-deployment-slug"
```

Or create a `.env` file:

```plaintext
SEMGREP_API_TOKEN=your-api-token
SEMGREP_ORG_ID=your-org-id
SEMGREP_DEPLOYMENT_SLUG=your-deployment-slug
```

## Usage

Run the script:
```bash
python semgrep_scan_health_analyzer.py
```

The script will:
1. Create a `reports` directory if it doesn't exist
2. Fetch all projects from your Semgrep organization
3. Collect scan data for each project
4. Generate health metrics
5. Save all reports to the `reports` directory

## Health Metrics

The repository health summary includes:
- Total number of scans per repository
- Number of failed scans
- Failure percentage
- Success rate

Excel Formatting:
- Numbers are stored as proper numeric types (not text)
- Percentages are formatted with 2 decimal places
- Color coding in Excel:
  - 🔴 Red: Failure rate ≥ 20%
  - 🟡 Yellow: Failure rate between 10% and 20%
  - 🟢 Green: Failure rate < 10%

## Sample Output

### Scan Details (semgrep_scans_*.csv):
```csv
scan_id,repository_id,project_name,is_full_scan,status,branch,completed_at
12345,67890,my-repo,True,SCAN_STATUS_COMPLETED,main,2024-01-01T12:00:00Z
```

### Health Summary (repo_scan_health_summary_*.csv):
```csv
repository_id,project_name,total_scans,failed_scans,failure_percentage,success_rate
67890,my-repo,100,5,5.0,95.0
```

### Excel Workbook Features
- Proper numeric data types for IDs and metrics
- Formatted percentage columns
- Color-coded health indicators
- Optimized column widths
- Bold headers with gray background
- Two organized sheets for different views of the data

## File Organization

```
.
├── reports/
│   ├── semgrep_scans_20240415_123456.csv
│   ├── semgrep_scans_20240415_123456.xlsx
│   └── repo_scan_health_summary_20240415_123456.csv
├── semgrep_scan_analyzer.py
├── requirements.txt
└── README.md
```

## Error Handling

The script includes error handling for:
- Missing environment variables
- API authentication failures
- Network connectivity issues
- Invalid response data
- Directory creation issues
- Data type conversion errors

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
