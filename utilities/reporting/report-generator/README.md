# Semgrep Security Reporter (Node.js Version)

A Node.js/TypeScript implementation of the Semgrep Security Report Generator using React-PDF.

## Features

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
- **React-PDF**: PDF generation library
- **Winston**: Structured logging system
- **Axios**: HTTP client for API calls

Generated with ❤️ by Semgrep Solutions Engineering