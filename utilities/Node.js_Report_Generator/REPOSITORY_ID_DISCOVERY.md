# Repository Reference ID Discovery Guide

## Problem
Semgrep Dashboard links require internal repository reference IDs (`repo_ref`) that are not exposed through the public API. These IDs are different from project IDs and are only available through internal Semgrep systems (Metabase).

## Current Status
- ✅ **java-app-lockfileless**: Project ID `3740958` → repo_ref `70046396` (verified working)
- ❌ **Other repositories**: Mathematical calculation approach failed

## How to Discover Repository Reference IDs

### Method 1: Browser Network Traffic Analysis (Manual)

1. **Open Semgrep Dashboard** in your browser
2. **Navigate to Findings** page for your organization
3. **Apply Repository Filter**:
   - Click on repository filter dropdown
   - Select the specific repository you need the ID for
4. **Open Browser Developer Tools** (F12)
5. **Monitor Network Traffic**:
   - Go to Network tab
   - Look for requests to `/api/agent/deployments/` endpoints
6. **Examine Request Bodies**:
   - Find POST requests with `repositoryRefIds` arrays
   - The numeric value in this array is your repo_ref ID

**Example HAR Analysis Result:**
```json
{
  "filter": {
    "repositoryRefIds": [70046396]  // ← This is your repo_ref
  }
}
```

### Method 2: Configuration Discovery Tool (Automated - Future)

We could create a browser automation tool that:
1. Logs into Semgrep Dashboard
2. Iterates through each repository
3. Applies filters and captures network traffic
4. Extracts repo_ref IDs automatically
5. Generates configuration mappings

### Method 3: Contact Semgrep Support

For enterprise customers, Semgrep support may be able to provide these mappings or expose them through future API updates.

## Adding New Repository Mappings

Once you discover a repository reference ID, add it to the code:

**File:** `/Services/EnhancedReportGenerator.cs`

```csharp
var knownRepositoryMappings = new Dictionary<string, string>
{
    ["3740958"] = "70046396", // kyle-semgrep/java-app-lockfileless
    ["YOUR_PROJECT_ID"] = "YOUR_REPO_REF", // your-org/your-repo
};
```

## Alternative Approaches

### Option 1: Selective Dashboard Links
Only enable dashboard links for repositories with known repo_ref mappings:

```csharp
// Skip dashboard links for unmapped repositories
if (!knownRepositoryMappings.ContainsKey(projectId))
{
    // Don't render dashboard column for this repository
    return null;
}
```

### Option 2: Warning Messages
Add warnings to reports when dashboard links may not work:

```
⚠️ Dashboard links for some repositories may not work correctly due to internal ID requirements.
Contact your Semgrep administrator for assistance with repository reference mappings.
```

### Option 3: Configuration-Based Toggle
Allow users to disable dashboard links entirely if they can't maintain the mappings:

```json
{
  "includeDashboardLinks": false  // Disable if mappings unavailable
}
```

## Future Improvements

1. **Browser Automation Tool**: Create automated discovery script
2. **API Enhancement Request**: Ask Semgrep to expose repo_ref IDs in public API
3. **Configuration UI**: Build web interface for mapping management
4. **Fallback URLs**: Use alternative URL patterns that might work without repo_ref