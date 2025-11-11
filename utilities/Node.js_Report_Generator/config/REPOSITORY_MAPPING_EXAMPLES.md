# Repository Reference Mapping Configuration

This document explains the different methods for configuring repository reference mappings to enable precise Semgrep dashboard links in customer environments where you only have API token access.

## Configuration Methods

### 1. Simplified Method (Default)
**Best for:** Token-only environments where you want working dashboard links without repo-specific filtering.

```json
{
  "repositoryReferenceMapping": {
    "method": "simplified"
  }
}
```

**Result:** Dashboard links filter by rule across the entire organization (no repo_ref parameter).

### 2. Static Mappings Method
**Best for:** When you have a known set of project ID → repo_ref mappings.

```json
{
  "repositoryReferenceMapping": {
    "method": "static",
    "staticMappings": {
      "1942269": "70123456",
      "1942270": "70123457",
      "3550199": "71234567"
    }
  }
}
```

**How to obtain mappings:**
- Use browser dev tools to capture network traffic on Semgrep dashboard
- Look for API calls containing `repo_ref` parameters
- Map project IDs to repo_ref values

### 3. External File Method
**Best for:** Large numbers of mappings or when mappings are managed separately.

```json
{
  "repositoryReferenceMapping": {
    "method": "external",
    "externalMappingFile": "./config/customer-repo-mappings.json"
  }
}
```

**External file format:**
```json
{
  "1942269": "70123456",
  "1942270": "70123457",
  "1942271": "70123458"
}
```

### 4. Playwright Automation Method (Future)
**Best for:** Automated discovery when you have login credentials.

```json
{
  "repositoryReferenceMapping": {
    "method": "playwright",
    "playwrightConfig": {
      "enabled": true,
      "username": "your-email@company.com",
      "password": "your-password",
      "organizationSlug": "your-org-name",
      "cacheResults": true,
      "cacheFile": "./cache/repo-mappings.json"
    }
  }
}
```

**Note:** This method is designed for future implementation and requires login credentials.

## Obtaining Repository Reference IDs

### Method 1: Browser Developer Tools
1. Navigate to Semgrep dashboard findings page
2. Open Browser Developer Tools (F12)
3. Go to Network tab
4. Filter for API calls
5. Look for calls to `/findings` endpoint with `repo_ref` parameter
6. Note the mapping between repository name and repo_ref value

### Method 2: HAR File Analysis
1. Record browser session navigating dashboard
2. Export HAR file
3. Search for `repo_ref` parameters in the HAR data
4. Extract project ID → repo_ref mappings

### Method 3: Manual Discovery Script (Token-based)
Create a discovery script that:
1. Uses API to get project list
2. For each project, attempts to find corresponding dashboard URLs
3. Captures working repo_ref values
4. Outputs mapping file

## Integration Examples

### Customer Environment Setup
```json
{
  "organizationSettings": {
    "organizationName": "customer-org",
    "apiToken": "customer_api_token_here"
  },
  "reportConfiguration": {
    "includeDashboardLinks": true,
    "repositoryReferenceMapping": {
      "method": "external",
      "externalMappingFile": "./customer-configs/repo-mappings.json"
    }
  }
}
```

### Hybrid Approach (Static + Fallback)
```json
{
  "repositoryReferenceMapping": {
    "method": "static",
    "staticMappings": {
      "1942269": "70123456",
      "1942270": "70123457"
    }
  }
}
```
*Unknown project IDs automatically fall back to simplified links*

## Fallback Behavior

All methods fall back gracefully:
1. **Static/External:** Unknown projects → simplified links
2. **Playwright:** Discovery failure → simplified links  
3. **Simplified:** Always works (no repo-specific filtering)
4. **Error states:** Always fall back to simplified links

This ensures reports always generate successfully with working dashboard links, even if repo_ref mapping fails.