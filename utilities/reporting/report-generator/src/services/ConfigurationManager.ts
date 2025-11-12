import * as fs from 'fs';
import * as path from 'path';
import { ReportConfiguration, ProjectSettings } from '../models';

export class ConfigurationManager {
  private config: ReportConfiguration;

  constructor(configPath: string = 'config/sample-config.json') {
    this.config = this.loadConfiguration(configPath);
  }

  private loadConfiguration(configPath: string): ReportConfiguration {
    try {
      const fullPath = path.resolve(configPath);
      
      if (!fs.existsSync(fullPath)) {
        throw new Error(`Configuration file not found: ${fullPath}`);
      }

      const configData = fs.readFileSync(fullPath, 'utf-8');
      const config = JSON.parse(configData) as ReportConfiguration;
      
      // Validate required fields
      this.validateConfiguration(config);
      
      console.log(`✓ Configuration loaded for: ${config.customer.name}`);
      
      return config;
    } catch (error) {
      console.error(`Error loading configuration: ${error}`);
      throw error;
    }
  }

  private validateConfiguration(config: ReportConfiguration): void {
    if (!config.customer?.name) {
      throw new Error('Customer name is required in configuration');
    }

    if (!config.organizationSettings?.organizationName) {
      throw new Error('Organization name is required in configuration');
    }

    // Ensure we have projects to process
    const allProjects = this.getAllProjects(config);
    if (allProjects.length === 0) {
      throw new Error('At least one project must be configured');
    }
  }

  private getAllProjects(config: ReportConfiguration): ProjectSettings[] {
    // Support backward compatibility
    if (config.projects && config.projects.length > 0) {
      return config.projects.filter(p => p.include);
    }
    
    if (config.project) {
      return [config.project];
    }
    
    return [];
  }

  public getConfiguration(): ReportConfiguration {
    return this.config;
  }

  public getCustomerName(): string {
    return this.config.customer.name;
  }

  public getOrganizationName(): string {
    return this.config.organizationSettings?.organizationName || 'unknown';
  }

  public getApiToken(): string | undefined {
    return this.config.organizationSettings?.apiToken || process.env.SEMGREP_APP_TOKEN;
  }

  public getProjects(): ProjectSettings[] {
    return this.getAllProjects(this.config);
  }

  public getPrimaryColor(): string {
    return this.config.reportConfiguration.branding.primaryColor || '#2dcda7';
  }

  public getAccentColor(): string {
    return this.config.reportConfiguration.branding.accentColor || '#deede8';
  }

  public getDetailFilterMinSeverity(): string {
    return this.config.reportConfiguration.detailFilterMinSeverity || 'Medium';
  }

  public getFindingsDetailLevel(): string {
    return this.config.reportConfiguration.findingsDetailLevel || 'standard';
  }

  public shouldIncludeDashboardLinks(): boolean {
    return this.config.reportConfiguration.includeDashboardLinks ?? true;
  }

  public getRepositoryReferenceMapping(): Record<string, string> {
    const repoMapping = this.config.reportConfiguration.repositoryReferenceMapping;
    
    // If external mapping file is specified, load it
    if (repoMapping?.externalMappingFile) {
      try {
        const mappingPath = path.resolve(repoMapping.externalMappingFile);
        if (fs.existsSync(mappingPath)) {
          const mappingData = fs.readFileSync(mappingPath, 'utf-8');
          const mappingArray = JSON.parse(mappingData);
          
          // Convert the array format to ID -> Repository ID mapping
          const mapping: Record<string, string> = {};
          for (const entry of mappingArray) {
            if (entry.ID && entry['Repository ID']) {
              mapping[entry.ID] = entry['Repository ID'];
            }
          }
          
          console.log(`✓ Loaded ${Object.keys(mapping).length} repository mappings from external file`);
          return mapping;
        } else {
          console.log(`Warning: External mapping file not found: ${mappingPath}`);
        }
      } catch (error) {
        console.log(`Warning: Error loading external mapping file: ${error}`);
      }
    }
    
    // Fallback to static mappings
    return repoMapping?.staticMappings || {};
  }

  public getCompanyLogo(): string {
    return this.config.reportConfiguration.branding.companyLogo || './assets/semgrep.svg';
  }

  public getReportSections() {
    return this.config.reportConfiguration.includeSections;
  }

  public getSeverityThresholds() {
    return this.config.reportConfiguration.severityThresholds;
  }

  public getComplianceRequirements(): string[] {
    return this.config.applicationSettings.complianceRequirements || [];
  }

  public getBusinessCriticality(): string {
    return this.config.applicationSettings.businessCriticality || 'High';
  }
}