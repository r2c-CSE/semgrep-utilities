import { ScanMetadata } from './SemgrepFinding';

export interface ReportConfiguration {
  customer: CustomerInfo;
  project?: ProjectSettings; // Backward compatibility
  projects: ProjectSettings[];
  applicationSettings: ApplicationSettings;
  reportConfiguration: ReportConfigSettings;
  semgrepConfiguration: SemgrepConfiguration;
  integrationSettings: IntegrationSettings;
  organizationSettings?: OrganizationSettings;
}

export interface CustomerInfo {
  name: string;
  industry: string;
  reportingContact: string;
}

export interface ProjectSettings {
  semgrepProjectId: string;
  include: boolean;
  
  // Optional overrides - if not provided, will be fetched from Semgrep API
  name?: string;
  repository?: string;
  lastScanned?: Date;
  scanData?: ScanMetadata;
}

export interface ApplicationSettings {
  businessCriticality: string;
  complianceRequirements: string[];
  riskTolerance: string;
}

export interface ReportConfigSettings {
  includeSections: IncludeSections;
  severityThresholds: SeverityThresholds;
  outputFormats: string[];
  branding: BrandingSettings;
  detailFilterMinSeverity: string; // 'Low', 'Medium', 'High', 'Critical'
  findingsDetailLevel: string; // 'standard', 'brief'
  includeDashboardLinks: boolean;
  repositoryReferenceMapping?: RepositoryReferenceMapping;
}

export interface IncludeSections {
  executiveSummary: boolean;
  securityScorecard: boolean;
  owaspMapping: boolean;
  findingsDetails: boolean;
  remediationRoadmap: boolean;
  complianceMatrix: boolean;
  appendixMethodology: boolean;
}

export interface SeverityThresholds {
  blockingFindings: string[];
  expeditedFindings: string[];
  scheduledFindings: string[];
}

export interface BrandingSettings {
  companyLogo: string;
  primaryColor: string;
  accentColor: string;
}

export interface SemgrepConfiguration {
  requiredScans: RequiredScans;
  rulesets: string[];
  minimumSemgrepLevel: string;
}

export interface RequiredScans {
  sast: boolean;
  supplyChain: boolean;
  secrets: boolean;
}

export interface IntegrationSettings {
  jiraTicketCreation: boolean;
  slackNotifications: boolean;
  emailReporting: EmailReporting;
}

export interface EmailReporting {
  enabled: boolean;
  recipients: string[];
  frequency: string;
}

export interface OrganizationSettings {
  organizationName: string;
  apiToken: string;
}

export interface RepositoryReferenceMapping {
  method: string; // 'simplified', 'static', 'playwright', 'external'
  staticMappings: Record<string, string>;
  playwrightConfig?: PlaywrightConfig;
  externalMappingFile?: string;
}

export interface PlaywrightConfig {
  enabled: boolean;
  username: string;
  password: string;
  organizationSlug: string;
  cacheResults: boolean;
  cacheFile: string;
}