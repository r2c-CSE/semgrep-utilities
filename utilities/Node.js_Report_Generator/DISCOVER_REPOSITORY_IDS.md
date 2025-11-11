# Quick Repository ID Discovery Process

## Step-by-Step Guide

### 1. Prepare Your Environment
- Open Chrome/Firefox with Developer Tools
- Navigate to Semgrep Dashboard: `https://semgrep.dev/orgs/YOUR_ORG/findings`

### 2. Capture Network Traffic
```bash
# In browser Developer Tools (F12):
1. Go to Network tab
2. Clear existing requests (🚫 icon)
3. Filter: XHR/Fetch only
4. Keep Dev Tools open
```

### 3. Discover Each Repository Mapping

For **each repository** you want dashboard links for:

#### A. Apply Repository Filter
1. Click the repository filter dropdown
2. Select **ONE specific repository** 
3. Apply the filter

#### B. Capture the repo_ref
1. In Network tab, look for `/api/agent/deployments/` requests
2. Click on a POST request
3. Go to **Request** tab
4. Look for JSON body containing: `"repositoryRefIds":[NUMBER]`
5. Record: `Project ID → repo_ref ID`

#### C. Clear and Repeat
1. Remove repository filter
2. Clear network log
3. Repeat for next repository

### 4. Update Code Mapping

Add discovered mappings to `/Services/EnhancedReportGenerator.cs`:

```csharp
var knownRepositoryMappings = new Dictionary<string, string>
{
    ["3740958"] = "70046396", // kyle-semgrep/java-app-lockfileless
    ["3739270"] = "70044708", // kyle-semgrep/javaspringvulny (example)
    ["3739274"] = "70044712", // kyle-semgrep/lodash (example)
    // Add your discovered mappings here...
};
```

### 5. Verification

Test each mapping by:
1. Generating a report with dashboard links enabled
2. Clicking the dashboard links 
3. Verifying they filter to the correct repository

## Automation Tools (Future)

### Option A: HAR File Processor
```bash
# Capture HAR file with ALL repository interactions
# Process automatically:
dotnet run Tools/HarProcessor.exe semgrep.dev.har
```

### Option B: Browser Automation
```bash
# Fully automated discovery:
dotnet run Tools/RepositoryDiscovery.exe --org your-org --username user@company.com
```

### Option C: Batch Discovery Script
```javascript
// Browser console script to cycle through all repositories
const repositories = ['repo1', 'repo2', 'repo3'];
const mappings = {};

for (const repo of repositories) {
    // Simulate clicks and capture network
    // Extract repositoryRefIds automatically
}
```

## Troubleshooting

### No repositoryRefIds Found
- Ensure you're filtering to **one specific repository**
- Check that `/api/agent/` requests are being made
- Try refreshing the page after applying filter

### Wrong Repository Reference
- Double-check the repository name matches
- Verify the project ID corresponds to correct repo
- Test the generated dashboard link

### Multiple Repository IDs
- Some requests may contain multiple IDs
- Use the ID that appears when filtering to **just your target repo**

## Repository Name → Project ID Mapping

If you need to find project IDs:
```bash
# From our existing code/reports, we know:
3740958 = kyle-semgrep/java-app-lockfileless
3739270 = kyle-semgrep/javaspringvulny  
3739274 = kyle-semgrep/lodash
3739268 = kyle-semgrep/bad-python-app-kyle-managed
3739271 = kyle-semgrep/js-app
3739269 = kyle-semgrep/BrokenAccessControl
3739273 = kyle-semgrep/semgrep-feature-matrix-generator
3739266 = kyle-semgrep/bad-python-app-kyle-ci-gh
3739272 = kyle-semgrep/semgrep-docs
3806482 = local_scan/src
```

Use this mapping to correlate repository names with project IDs when adding discovered repo_ref values.