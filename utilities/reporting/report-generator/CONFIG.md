# Configuration Guide

This document explains all configuration options for the Semgrep Reporter POC tool.

## Quick Start

1. Copy `config/sample-config.json` to create your organization's config
2. Update `organizationSettings` with your Semgrep org name and API token
3. Update `customer` information for report branding
4. Add your project IDs to the `projects` array
5. Configure `repositoryReferenceMapping` for dashboard links (optional but recommended)

## Configuration File Structure

### Customer Information
```json
{
  "customer": {
    "name": "Your Organization Name",           // Appears on report cover
    "industry": "Technology / Financial",       // Industry classification
    "reportingContact": "security@company.com"  // Contact for security questions
  }
}
```

### Project Selection
```json
{
  "projects": [
    {
      "semgrepProjectId": "1234567",  // Project ID from Semgrep dashboard
      "include": true                 // Set false to exclude from reports
    }
  ]
}
```

**Finding Project IDs:**
1. Go to your Semgrep dashboard
2. Navigate to Projects section
3. Copy the numerical ID from the URL or project details

### Application Settings
```json
{
  "applicationSettings": {
    "businessCriticality": "High",                           // Critical|High|Medium|Low
    "complianceRequirements": ["SOC 2", "GDPR", "PCI-DSS"], // Compliance frameworks
    "riskTolerance": "Low"                                   // Low|Medium|High
  }
}
```

**Business Criticality Impact:**
- **Critical/High**: Stricter security requirements, more detailed remediation
- **Medium/Low**: Standard security requirements, balanced approach

**Common Compliance Requirements:**
- `SOC 2` - Service Organization Control 2
- `GDPR` - General Data Protection Regulation  
- `PCI-DSS` - Payment Card Industry Data Security Standard
- `OWASP Top 10` - OWASP Top 10 security risks
- `HIPAA` - Health Insurance Portability and Accountability Act
- `ISO 27001` - Information Security Management

### Report Configuration

#### Section Controls
```json
{
  "reportConfiguration": {
    "includeSections": {
      "executiveSummary": true,      // High-level overview for leadership
      "securityScorecard": true,     // Numerical security scoring
      "owaspMapping": true,          // Map findings to OWASP Top 10
      "findingsDetails": true,       // Detailed vulnerability listings
      "remediationRoadmap": true,    // Prioritized remediation plan
      "complianceMatrix": false,     // Compliance framework mapping (optional)
      "appendixMethodology": false   // Technical methodology (optional)
    }
  }
}
```

#### Severity and Detail Controls
```json
{
  "reportConfiguration": {
    "severityThresholds": {
      "blockingFindings": ["Critical"],                    // Block deployments
      "expeditedFindings": ["Critical", "High"],          // Urgent fixes (days)
      "scheduledFindings": ["Medium", "Low"]              // Regular sprint work
    },
    
    "detailFilterMinSeverity": "Medium",  // Only show Medium+ in detailed sections
    "findingsDetailLevel": "standard"     // "brief" or "standard"
  }
}
```

**Detail Filter Severity:**
- `"Critical"` - Only show Critical findings in detailed sections
- `"High"` - Show Critical and High findings  
- `"Medium"` - Show Critical, High, and Medium findings (recommended)
- `"Low"` - Show all findings

**Findings Detail Level:**
- `"brief"` - Findings summaries on project pages only
- `"standard"` - Separate detailed findings pages with full descriptions, rule links, and remediation guidance

#### Dashboard Links
```json
{
  "reportConfiguration": {
    "includeDashboardLinks": true,
    "repositoryReferenceMapping": {
      "method": "static",
      "staticMappings": {
        "1234567": "98765432"  // semgrepProjectId: repositoryReferenceId
      }
    }
  }
}
```

**Getting Repository Reference IDs:**

Option 1 - Use the Repository Discovery Tool:
```bash
dotnet run -- discovery --org your-org-name --projects 1234567,1234568
```

Option 2 - Manual Network Inspection:
1. Open browser developer tools (Network tab)
2. Go to Semgrep dashboard findings page
3. Apply a repository filter
4. Look for POST requests to `/api/agent/deployments/`
5. Find `repositoryRefIds` in the request payload

#### Visual Branding
```json
{
  "reportConfiguration": {
    "branding": {
      "companyLogo": "./assets/Semgrep_logo.png",  // Path to logo image
      "primaryColor": "#2dcda7",                   // Primary brand color (hex)
      "accentColor": "#deede8"                     // Accent color for highlights
    }
  }
}
```

### Semgrep Configuration
```json
{
  "semgrepConfiguration": {
    "requiredScans": {
      "sast": true,         // Static Application Security Testing
      "supplyChain": true,  // Dependency/supply chain scanning
      "secrets": true       // Secrets detection
    },
    "rulesets": [
      "r2c-security-audit",  // Semgrep's comprehensive security rules
      "owasp-top-10",        // OWASP Top 10 specific rules
      "cwe-top-25"           // CWE Top 25 most dangerous weaknesses
    ],
    "minimumSemgrepLevel": "SL3"  // SL1|SL2|SL3 (SL3 most secure)
  }
}
```

**Common Rulesets:**
- `r2c-security-audit` - Comprehensive security rules (recommended)
- `owasp-top-10` - OWASP Top 10 security risks
- `cwe-top-25` - CWE Top 25 most dangerous software weaknesses
- `r2c-best-practices` - General best practices
- `security` - Basic security rules

### Organization Settings
```json
{
  "organizationSettings": {
    "organizationName": "your-org-name",    // From dashboard URL
    "apiToken": "your-api-token"            // From Settings > Tokens
  }
}
```

**Getting Your Organization Name:**
- Look at your Semgrep dashboard URL: `https://semgrep.dev/orgs/YOUR-ORG-NAME/`
- The organization name is the part after `/orgs/`

**Getting Your API Token:**
1. Go to Semgrep dashboard
2. Navigate to Settings > Tokens  
3. Create a new token with "Read" permissions for findings and projects
4. Copy the token value

**Alternative - Environment Variable:**
Set `SEMGREP_APP_TOKEN` environment variable instead of including in config file.

## Report Types

### Brief Reports
- Findings summaries on project cover pages
- Faster to generate and review
- Good for executive summaries and regular check-ins
- Set: `"findingsDetailLevel": "brief"`

### Standard Reports  
- Separate detailed findings pages for each project
- Full vulnerability descriptions and remediation guidance
- Hyperlinked rule IDs to Semgrep Registry
- Dashboard links to specific findings
- File-level details with line numbers
- Recommended for thorough security analysis
- Set: `"findingsDetailLevel": "standard"`

## Configuration Examples

### Small Organization (< 10 projects)
```json
{
  "detailFilterMinSeverity": "Medium",
  "findingsDetailLevel": "standard",
  "includeDashboardLinks": true
}
```

### Large Organization (> 50 projects)
```json
{
  "detailFilterMinSeverity": "High", 
  "findingsDetailLevel": "brief",
  "includeDashboardLinks": false
}
```

### Compliance-Focused
```json
{
  "complianceRequirements": ["SOC 2", "PCI-DSS"],
  "detailFilterMinSeverity": "Medium",
  "includeSections": {
    "complianceMatrix": true,
    "appendixMethodology": true
  }
}
```

## Troubleshooting

### Common Issues

**"No findings found for project"**
- Verify project ID is correct
- Check that project has recent scans
- Ensure API token has proper permissions

**"Repository reference mapping failed"**
- Dashboard links require repository reference IDs
- Use the discovery tool or manual inspection to get IDs
- Set `"includeDashboardLinks": false` to disable

**"Report generation timeout"**
- Large organizations may need extended timeouts
- Consider using `"brief"` format for faster generation
- Filter to fewer projects or higher severity only

**"API rate limiting"**
- Tool respects Semgrep API rate limits
- Large organizations may take longer to process
- Consider running during off-peak hours

### Getting Help

1. Check the logs for specific error messages
2. Verify your configuration against `sample-config.json`
3. Test with a smaller subset of projects first
4. Ensure your API token has the required permissions

## Advanced Configuration

### Custom Styling
Modify the `branding` section to match your organization's visual identity. Supported image formats for logos: PNG, JPG, SVG.

### Repository Discovery Tool
Use the built-in discovery tool to automatically find repository reference IDs:

```bash
# Dry run (recommended first)
dotnet run -- discovery --org your-org --dry-run

# Live discovery
dotnet run -- discovery --org your-org --live
```

### Environment Variables
- `SEMGREP_APP_TOKEN` - API token (alternative to config file)
- Additional environment variables may be supported in future versions