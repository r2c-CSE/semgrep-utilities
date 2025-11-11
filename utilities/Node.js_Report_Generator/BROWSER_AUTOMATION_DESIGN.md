# Browser Automation Tool Design

## Overview
Automated tool to discover Semgrep Dashboard repository reference IDs by simulating user interactions and capturing network traffic.

## Option 1: Selenium WebDriver (.NET Integration)

### Architecture
```
SemgrepReporter.POC/
├── Services/
│   ├── SemgrepApiClient.cs (existing)
│   ├── BrowserAutomationService.cs (new)
│   └── RepositoryMappingService.cs (new)
├── Models/
│   └── RepositoryMapping.cs (new)
└── Tools/
    └── RepositoryIdDiscovery/ (new utility)
```

### Implementation Plan

#### 1. Dependencies
```xml
<PackageReference Include="Selenium.WebDriver" Version="4.15.0" />
<PackageReference Include="Selenium.WebDriver.ChromeDriver" Version="119.0.6045.10500" />
<PackageReference Include="Selenium.Support" Version="4.15.0" />
```

#### 2. Core Service Class
```csharp
public class BrowserAutomationService
{
    private readonly IWebDriver _driver;
    private readonly List<RepositoryMapping> _discoveredMappings;
    
    public async Task<Dictionary<string, string>> DiscoverRepositoryMappingsAsync(
        string orgName, 
        List<string> projectIds,
        string username, 
        string password)
    {
        // 1. Login to Semgrep Dashboard
        await LoginAsync(username, password);
        
        // 2. For each project, discover repo_ref
        foreach (var projectId in projectIds)
        {
            var repoRef = await DiscoverRepositoryRefAsync(orgName, projectId);
            if (repoRef != null)
            {
                _discoveredMappings.Add(new RepositoryMapping 
                { 
                    ProjectId = projectId, 
                    RepositoryRefId = repoRef 
                });
            }
        }
        
        return _discoveredMappings.ToDictionary(m => m.ProjectId, m => m.RepositoryRefId);
    }
    
    private async Task<string?> DiscoverRepositoryRefAsync(string orgName, string projectId)
    {
        // Enable network traffic capture
        var networkLogs = new List<LogEntry>();
        
        // Navigate to findings page
        var findingsUrl = $"https://semgrep.dev/orgs/{orgName}/findings?tab=open";
        _driver.Navigate().GoToUrl(findingsUrl);
        
        // Wait for page load
        await WaitForElementAsync(By.CssSelector("[data-testid='repository-filter']"));
        
        // Open repository filter dropdown
        var repoFilter = _driver.FindElement(By.CssSelector("[data-testid='repository-filter']"));
        repoFilter.Click();
        
        // Get repository name from project
        var repoName = await GetRepositoryNameAsync(projectId);
        
        // Select specific repository
        var repoOption = await WaitForElementAsync(By.XPath($"//div[contains(text(), '{repoName}')]"));
        
        // Start network monitoring
        StartNetworkCapture();
        
        // Click repository option (triggers API calls)
        repoOption.Click();
        
        // Wait for API calls to complete
        await Task.Delay(2000);
        
        // Extract repo_ref from captured network traffic
        var repoRef = ExtractRepositoryRefFromNetwork();
        
        return repoRef;
    }
    
    private string? ExtractRepositoryRefFromNetwork()
    {
        // Parse browser logs for /api/agent/ requests
        var logs = _driver.Manage().Logs.GetLog(LogType.Performance);
        
        foreach (var log in logs)
        {
            if (log.Message.Contains("/api/agent/deployments/") && 
                log.Message.Contains("repositoryRefIds"))
            {
                // Parse JSON to extract repositoryRefIds array
                var jsonMatch = Regex.Match(log.Message, @"repositoryRefIds"":\[(\d+)\]");
                if (jsonMatch.Success)
                {
                    return jsonMatch.Groups[1].Value;
                }
            }
        }
        
        return null;
    }
}
```

#### 3. Model Classes
```csharp
public class RepositoryMapping
{
    public string ProjectId { get; set; } = string.Empty;
    public string RepositoryRefId { get; set; } = string.Empty;
    public string RepositoryName { get; set; } = string.Empty;
    public DateTime DiscoveredAt { get; set; } = DateTime.UtcNow;
}

public class DiscoveryConfiguration
{
    public string SemgrepUsername { get; set; } = string.Empty;
    public string SemgrepPassword { get; set; } = string.Empty;
    public string OrganizationName { get; set; } = string.Empty;
    public List<string> ProjectIds { get; set; } = new();
    public bool HeadlessMode { get; set; } = true;
    public int TimeoutSeconds { get; set; } = 30;
}
```

#### 4. CLI Tool
```csharp
// Tools/RepositoryIdDiscovery/Program.cs
class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("Semgrep Repository ID Discovery Tool");
        
        var config = LoadDiscoveryConfig();
        var automationService = new BrowserAutomationService();
        
        try
        {
            var mappings = await automationService.DiscoverRepositoryMappingsAsync(
                config.OrganizationName,
                config.ProjectIds,
                config.SemgrepUsername,
                config.SemgrepPassword
            );
            
            // Output C# code for integration
            GenerateMappingCode(mappings);
            
            // Save to JSON file
            SaveMappingsToFile(mappings);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Discovery failed: {ex.Message}");
        }
    }
    
    static void GenerateMappingCode(Dictionary<string, string> mappings)
    {
        Console.WriteLine("\n// Copy this code into GetRepositoryReferenceId():");
        Console.WriteLine("var knownRepositoryMappings = new Dictionary<string, string>");
        Console.WriteLine("{");
        
        foreach (var mapping in mappings)
        {
            Console.WriteLine($"    [\"{mapping.Key}\"] = \"{mapping.Value}\", // Auto-discovered");
        }
        
        Console.WriteLine("};");
    }
}
```

### Usage Example
```bash
# Run discovery tool
dotnet run --project Tools/RepositoryIdDiscovery -- \
  --username "your-email@company.com" \
  --password "your-password" \
  --org "your-org-name" \
  --projects "3740958,3739270,3739274"
```

## Option 2: Playwright-based Solution

### Why Playwright?
- Better network interception capabilities
- More reliable than Selenium
- Built-in request/response capture
- Cross-browser support

```csharp
// Using Microsoft.Playwright
public class PlaywrightDiscoveryService
{
    public async Task<Dictionary<string, string>> DiscoverMappingsAsync()
    {
        using var playwright = await Playwright.CreateAsync();
        await using var browser = await playwright.Chromium.LaunchAsync(new() { Headless = true });
        var page = await browser.NewPageAsync();
        
        // Capture network requests
        var repositoryMappings = new Dictionary<string, string>();
        
        page.Request += async (_, request) =>
        {
            if (request.Url.Contains("/api/agent/deployments/") && request.Method == "POST")
            {
                try
                {
                    var postData = request.PostData;
                    if (!string.IsNullOrEmpty(postData) && postData.Contains("repositoryRefIds"))
                    {
                        var json = JObject.Parse(postData);
                        var repoRefIds = json["filter"]?["repositoryRefIds"]?.ToObject<int[]>();
                        
                        if (repoRefIds?.Length > 0)
                        {
                            // Extract repository info and store mapping
                            // Implementation details...
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error parsing request: {ex.Message}");
                }
            }
        };
        
        // Navigate and interact with dashboard...
        await page.GotoAsync("https://semgrep.dev/login");
        // Login process...
        // Repository filtering process...
        
        return repositoryMappings;
    }
}
```

## Option 3: Puppeteer/Node.js Solution

### Advantages
- Excellent network interception
- Mature ecosystem
- Easy HAR file generation

```javascript
// Tools/repository-discovery.js
const puppeteer = require('puppeteer');

async function discoverRepositoryMappings(orgName, credentials) {
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    
    // Enable request interception
    await page.setRequestInterception(true);
    
    const discoveredMappings = new Map();
    
    page.on('request', async (request) => {
        if (request.url().includes('/api/agent/deployments/') && 
            request.method() === 'POST') {
            
            const postData = request.postData();
            if (postData && postData.includes('repositoryRefIds')) {
                try {
                    const payload = JSON.parse(postData);
                    const repoRefIds = payload.filter?.repositoryRefIds;
                    
                    if (repoRefIds?.length > 0) {
                        // Store mapping logic
                        console.log('Discovered repo_ref:', repoRefIds[0]);
                    }
                } catch (e) {
                    console.error('Error parsing request:', e);
                }
            }
        }
        
        request.continue();
    });
    
    // Login and discovery process...
    await page.goto('https://semgrep.dev/login');
    
    // Return mappings in format compatible with C#
    return Object.fromEntries(discoveredMappings);
}
```

## Option 4: Hybrid Approach - HAR File Processor

### Concept
Instead of full automation, create a tool that processes HAR files:

```csharp
public class HarFileProcessor
{
    public Dictionary<string, string> ExtractRepositoryMappings(string harFilePath)
    {
        var harContent = File.ReadAllText(harFilePath);
        var harData = JsonSerializer.Deserialize<HarFile>(harContent);
        
        var mappings = new Dictionary<string, string>();
        
        foreach (var entry in harData.Log.Entries)
        {
            if (entry.Request.Url.Contains("/api/agent/deployments/") &&
                entry.Request.Method == "POST")
            {
                var postData = entry.Request.PostData?.Text;
                if (!string.IsNullOrEmpty(postData) && postData.Contains("repositoryRefIds"))
                {
                    // Parse and extract mappings
                    var repoRef = ExtractRepositoryRefFromJson(postData);
                    // Map to project based on context
                }
            }
        }
        
        return mappings;
    }
}
```

### User Workflow
1. User opens Semgrep Dashboard
2. User applies filters for each repository (one by one)  
3. User exports HAR file from browser dev tools
4. Tool processes HAR file to extract all mappings
5. Tool generates code for integration

## Recommended Implementation

### Phase 1: HAR File Processor (Quickest)
- Build HAR file processing utility
- Provide clear instructions for users
- Generate mapping code automatically

### Phase 2: Playwright Automation (Most Robust)
- Full browser automation
- Reliable network capture
- Cross-platform support

### Phase 3: CLI Integration
- Integrate discovery into main application
- Automated mapping updates
- Configuration management

## Security Considerations

1. **Credential Storage**: Use secure credential management
2. **Rate Limiting**: Respect Semgrep's rate limits
3. **Headless Mode**: Run without GUI for security
4. **Audit Trail**: Log discovery activities
5. **Access Control**: Restrict tool access appropriately

Would you like me to implement one of these approaches? The HAR file processor would be quickest to build and test!