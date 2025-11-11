# Semgrep Security Reporter (Node.js Version)

A Node.js/TypeScript implementation of the Semgrep Security Report Generator using React-PDF instead of QuestPDF for cost optimization and better integration with Semgrep's existing Node.js technology stack.

## Features

✅ **Complete Node.js Conversion**: Migrated from C# to Node.js/TypeScript  
✅ **React-PDF Integration**: Cost-effective PDF generation without $1000 QuestPDF licensing  
✅ **Semgrep API Integration**: Full support for fetching findings with pagination and caching  
✅ **Business Logic Ported**: Security scoring, OWASP Top 10 2021 mapping, and Semgrep Levels  
✅ **Configuration System**: JSON-based configuration with customer branding support  
✅ **Dummy Data Mode**: Development and demo mode when no API token is provided  

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Semgrep API token (get from [Semgrep Settings](https://semgrep.dev/orgs/[your-org]/settings/tokens))

### Installation & Setup

```bash
# Clone and install dependencies
npm install

# Set up environment (CRITICAL - Never commit with real tokens!)
cp .env.example .env
# Edit .env and add your SEMGREP_APP_TOKEN

# Configure your report
cp config/sample-config.json config/my-org-config.json
# Edit config file, but keep apiToken empty (use env var)
```

### Security Best Practices ⚠️

**NEVER commit API tokens to version control!**

✅ **Correct**: Use environment variables
```bash
export SEMGREP_APP_TOKEN=your_token_here
npm run dev config/my-org-config.json
```

❌ **WRONG**: Hardcoding tokens in config files
```json
{
  "organizationSettings": {
    "apiToken": "hardcoded_token_here"  // Never do this!
  }
}
```

### Run Report Generation
```bash
# Development mode with structured logging
SEMGREP_APP_TOKEN=your_token npm run dev config/your-config.json

# Production build
npm run build
SEMGREP_APP_TOKEN=your_token npm start config/your-config.json
```

## Project Structure

```
src/
├── models/           # TypeScript interfaces and enums
├── services/         # API client, configuration, scoring engine
├── pdf/             # React-PDF document generation
└── index.ts         # Main application entry point
```

## Key Components

- **SemgrepApiClient**: Handles API calls with pagination, caching, and fallback to dummy data
- **ConfigurationManager**: Loads and validates JSON configuration files  
- **ScoringEngine**: Calculates security scores and Semgrep Levels (SL1-SL5)
- **BasicPdfGenerator**: React-PDF document generation with professional layouts

## Configuration

The application uses JSON configuration files with the following key sections:

- `customer`: Organization information and branding
- `projects`: Semgrep project IDs to include in the report  
- `reportConfiguration`: PDF customization and filtering options
- `organizationSettings`: API credentials and organization name

## Output

Generated PDF reports include:

1. **Executive Summary**: High-level security assessment overview
2. **Project Summary**: Per-project statistics and security levels
3. **Findings Details**: Detailed vulnerability listings with OWASP mapping

## Demo Mode

When no API token is provided, the application generates realistic dummy data to demonstrate functionality:

```bash
# Remove or empty the apiToken in your config
"organizationSettings": {
  "organizationName": "demo-organization", 
  "apiToken": ""
}
```

## Technology Stack

- **Node.js + TypeScript**: Type-safe JavaScript runtime
- **React-PDF**: PDF generation library (replaces QuestPDF)
- **Winston**: Structured logging system
- **Axios**: HTTP client for API calls

## Semgrep Coding Standards Compliance ✅

This project follows the [Semgrep Coding Standards](https://github.com/kyle-semgrep/Semgrep_Coding_Standards) for security and best practices:

### Security ⚠️
- ✅ **No hardcoded secrets**: All API tokens use environment variables
- ✅ **Environment variable pattern**: Uses `process.env.SEMGREP_APP_TOKEN`
- ✅ **Token scanning**: Project regularly scanned for leaked credentials
- ✅ **Secure defaults**: Empty tokens in config files force env var usage

### Logging 📝
- ✅ **Structured logging**: Winston for operational logs
- ✅ **CLI separation**: Separate `CLIOutput` for user-facing messages
- ✅ **Context-aware**: API calls, security events, and performance metrics
- ✅ **No console.log**: Reserved for CLI user interaction only

### Code Quality 🧹
- ✅ **Clean directory structure**: Removed redundant/development files
- ✅ **TypeScript**: Full type safety and modern JavaScript
- ✅ **Documentation**: Comprehensive README and code comments
- ✅ **Error handling**: Structured error logging and graceful failures

### Emergency Protocol 🚨
If tokens are accidentally committed:
1. Immediately revoke the exposed token in Semgrep dashboard
2. Generate a new token 
3. Update environment variables
4. Commit fixes with security context
5. Force push to remove history if needed

## Development Guidelines

### Pre-Commit Checklist
- [ ] No hardcoded secrets (scan with `git secrets` or Semgrep)
- [ ] Structured logging used (no console.log for operations)
- [ ] Environment variables documented in .env.example
- [ ] README updated with changes
- [ ] All API calls tested with real tokens
- **Axios**: HTTP client for Semgrep API calls
- **Express**: Optional web server capabilities

## Migration from C# Version

This Node.js version maintains feature parity with the original C# implementation while:

- Eliminating $1000 QuestPDF licensing cost
- Aligning with Semgrep's Node.js/React-PDF technology stack  
- Providing better integration opportunities with Semgrep's product
- Supporting the same configuration format and business logic

## Development Status

✅ **Phase 1-4 Complete**: Core functionality, API integration, and basic PDF generation  
🔄 **Phase 5-6 In Progress**: Enhanced PDF components and advanced layouts  
⏳ **Phase 7-10 Planned**: Dashboard integration, performance optimization, and documentation

---

Generated with ❤️ for Semgrep Solutions Engineering