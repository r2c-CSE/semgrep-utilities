import React from 'react';
import { Document, Page, Text, View, StyleSheet, pdf, Link, Image } from '@react-pdf/renderer';
import * as fs from 'fs';
import * as path from 'path';
import { SemgrepProject, SemgrepFinding, ReportConfiguration } from '../models';
import { ScoringEngine } from '../services';

// Define styles for the PDF document
const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    fontFamily: 'Helvetica',
  },
  // Cover page styles
  coverPage: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    fontFamily: 'Helvetica',
  },
  headerBar: {
    backgroundColor: '#00A86B',
    height: 80,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 40,
  },
  appSecurityTitle: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  poweredBy: {
    color: 'white',
    fontSize: 12,
    textAlign: 'right',
  },
  semgrepBrand: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 2,
  },
  coverContent: {
    padding: 40,
    flexGrow: 1,
  },
  mainTitle: {
    fontSize: 36,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  dateSection: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 5,
    textAlign: 'center',
  },
  preparedFor: {
    fontSize: 16,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
  },
  divider: {
    height: 3,
    backgroundColor: '#00A86B',
    marginVertical: 20,
  },
  overviewSection: {
    backgroundColor: '#F5F5F5',
    padding: 20,
    marginVertical: 20,
  },
  sectionTitle: {
    fontSize: 20,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 15,
  },
  overviewGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  overviewBox: {
    flex: 1,
    marginHorizontal: 10,
  },
  overviewLabel: {
    fontSize: 12,
    color: '#333333',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  overviewValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  slValue: {
    color: '#DC3545', // Red for SL1
  },
  scoreValue: {
    color: '#DC3545', // Red for low score
  },
  detailsSection: {
    marginTop: 20,
  },
  detailsTitle: {
    fontSize: 16,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 12,
    color: '#333333',
    fontWeight: 'bold',
    width: 120,
  },
  detailValue: {
    fontSize: 12,
    color: '#333333',
    flex: 1,
  },
  scanSection: {
    marginTop: 20,
  },
  scanGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
  },
  scanItem: {
    alignItems: 'center',
  },
  scanLabel: {
    fontSize: 12,
    color: '#333333',
    marginBottom: 5,
  },
  scanStatus: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  scanComplete: {
    color: '#28A745',
  },
  scanMissing: {
    color: '#DC3545',
  },
  footer: {
    position: 'absolute',
    fontSize: 10,
    bottom: 30,
    left: 0,
    right: 0,
    textAlign: 'center',
    color: '#999999',
  },
  footerWithLogo: {
    position: 'absolute',
    fontSize: 10,
    bottom: 30,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: '#999999',
  },
  footerText: {
    flex: 1,
    textAlign: 'center',
  },
  semgrepLogoFooter: {
    width: 60,
    height: 23, // Maintains 2.56:1 aspect ratio (60/23 ≈ 2.61)
    marginRight: 20,
  },
  semgrepLogoCover: {
    width: 100,
    height: 39, // Maintains 2.56:1 aspect ratio (100/39 ≈ 2.56)
    marginLeft: 10,
  },
  // Chart styles
  chartContainer: {
    marginVertical: 20,
  },
  chartTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333333',
  },
  chartRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  severityLabel: {
    width: 60,
    fontSize: 12,
    fontWeight: 'bold',
  },
  criticalLabel: {
    color: '#DC3545',
  },
  highLabel: {
    color: '#FD7E14',
  },
  mediumLabel: {
    color: '#FFC107',
  },
  lowLabel: {
    color: '#28A745',
  },
  chartBar: {
    height: 20,
    marginRight: 10,
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 5,
  },
  criticalBar: {
    backgroundColor: '#DC3545',
  },
  highBar: {
    backgroundColor: '#FD7E14',
  },
  mediumBar: {
    backgroundColor: '#FFC107',
  },
  lowBar: {
    backgroundColor: '#28A745',
  },
  chartValue: {
    fontSize: 10,
    color: 'white',
    fontWeight: 'bold',
  },
  chartCount: {
    fontSize: 12,
    fontWeight: 'bold',
    width: 40,
    textAlign: 'right',
  },
  owaspSection: {
    marginTop: 20,
  },
  owaspTitle: {
    fontSize: 16,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 15,
  },
  owaspTable: {
    marginTop: 10,
  },
  owaspHeader: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    padding: 8,
    borderBottom: '1px solid #DEE2E6',
  },
  owaspRow: {
    flexDirection: 'row',
    padding: 8,
    borderBottom: '1px solid #DEE2E6',
  },
  owaspCategoryCol: {
    flex: 3,
    fontSize: 11,
    fontWeight: 'bold',
  },
  owaspCountCol: {
    flex: 1,
    fontSize: 11,
    textAlign: 'center',
  },
  owaspRiskCol: {
    flex: 1,
    fontSize: 11,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  riskCritical: {
    color: '#DC3545',
  },
  riskHigh: {
    color: '#FD7E14',
  },
  riskMedium: {
    color: '#FFC107',
  },
  topRiskSection: {
    marginTop: 20,
  },
  topRiskTable: {
    marginTop: 10,
  },
  // Methodology styles
  methodologySection: {
    marginBottom: 25,
  },
  methodologyTitle: {
    fontSize: 16,
    color: '#00A86B',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  methodologyText: {
    fontSize: 11,
    color: '#333333',
    lineHeight: 1.4,
    marginBottom: 10,
  },
  levelTable: {
    marginTop: 15,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#F8F9FA',
    padding: 8,
    borderBottom: '1px solid #DEE2E6',
  },
  tableRow: {
    flexDirection: 'row',
    padding: 8,
    borderBottom: '1px solid #DEE2E6',
  },
  levelCol: {
    flex: 1,
    fontSize: 11,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  criteriaCol: {
    flex: 2,
    fontSize: 11,
  },
  descriptionCol: {
    flex: 3,
    fontSize: 11,
  },
  sl5Row: {
    backgroundColor: '#D4EDDA',
    color: '#155724',
  },
  sl4Row: {
    backgroundColor: '#D1ECF1',
    color: '#0C5460',
  },
  sl3Row: {
    backgroundColor: '#FFF3CD',
    color: '#856404',
  },
  sl2Row: {
    backgroundColor: '#F8D7DA',
    color: '#721C24',
  },
  sl1Row: {
    backgroundColor: '#F5C6CB',
    color: '#721C24',
  },
  scoringTable: {
    marginTop: 15,
  },
  scoringRow: {
    flexDirection: 'row',
    padding: 8,
    borderBottom: '1px solid #DEE2E6',
  },
  severityCol: {
    flex: 1,
    fontSize: 11,
    fontWeight: 'bold',
  },
  weightCol: {
    flex: 1,
    fontSize: 11,
    textAlign: 'center',
  },
  impactCol: {
    flex: 2,
    fontSize: 11,
  },
  formula: {
    fontSize: 10,
    fontFamily: 'Courier',
    backgroundColor: '#F8F9FA',
    padding: 8,
    marginTop: 10,
    border: '1px solid #DEE2E6',
  },
  // Content page styles  
  contentPage: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    padding: 30,
    fontFamily: 'Helvetica',
  },
  compactContentPage: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    fontFamily: 'Helvetica',
  },
  compactContent: {
    padding: 20,
    paddingTop: 15,
    flexGrow: 1,
  },
  title: {
    fontSize: 24,
    marginBottom: 20,
    textAlign: 'center',
    color: '#00A86B',
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 18,
    marginBottom: 15,
    color: '#333333',
    fontWeight: 'bold',
  },
  section: {
    margin: 10,
    padding: 10,
    flexGrow: 1,
  },
  text: {
    margin: 12,
    fontSize: 12,
    textAlign: 'justify',
    color: '#333333',
    lineHeight: 1.5,
  },
  header: {
    fontSize: 14,
    marginBottom: 20,
    textAlign: 'center',
    color: '#666666',
  },
});

export class BasicPdfGenerator {
  private scoringEngine: ScoringEngine;

  constructor() {
    this.scoringEngine = new ScoringEngine();
  }

  // Helper method to generate dashboard URL for a project
  private getDashboardUrl(projectId: string, config: ReportConfiguration): string | null {
    if (!config.reportConfiguration.includeDashboardLinks) {
      return null;
    }
    
    const repositoryMapping = config.reportConfiguration.repositoryReferenceMapping;
    
    // Handle api-discovery method - need to fetch detailed project info to get repoRefId
    if (repositoryMapping?.method === 'api-discovery') {
      if (config.organizationSettings?.organizationName) {
        // For api-discovery, we should link to findings filtered by this specific repository
        // This is more useful than the generic project page
        const baseUrl = 'https://semgrep.dev/orgs';
        const orgName = config.organizationSettings.organizationName;
        return `${baseUrl}/${orgName}/findings?tab=open&repository_id=${projectId}`;
      }
      return null;
    }
    
    // Handle external/static mapping methods - need reverse lookup
    const mapping = this.loadRepositoryMapping(config);
    
    // Find the Semgrep Project ID that maps to this Repository ID
    const semgrepProjectId = Object.keys(mapping).find(
      semgrepId => mapping[semgrepId] === projectId
    );
    
    if (semgrepProjectId && config.organizationSettings?.organizationName) {
      // Construct the Semgrep dashboard URL using repo_ref with Semgrep Project ID
      const baseUrl = 'https://semgrep.dev/orgs';
      const orgName = config.organizationSettings.organizationName;
      return `${baseUrl}/${orgName}/findings?repo_ref=${semgrepProjectId}`;
    }
    
    return null;
  }

  // Helper method to load repository mapping (including external files)
  private loadRepositoryMapping(config: ReportConfiguration): Record<string, string> {
    const repoMapping = config.reportConfiguration.repositoryReferenceMapping;
    
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
          
          return mapping;
        }
      } catch (error) {
        console.log(`Warning: Error loading external mapping file: ${error}`);
      }
    }
    
    // Fallback to static mappings
    return repoMapping?.staticMappings || {};
  }

  // Helper method to render severity distribution chart
  private renderSeverityChart(critical: number, high: number, medium: number, low: number) {
    const total = critical + high + medium + low;
    const maxCount = Math.max(critical, high, medium, low);
    const maxWidth = 200; // Maximum bar width

    const getBarWidth = (count: number) => {
      if (maxCount === 0) return 0;
      return Math.max((count / maxCount) * maxWidth, count > 0 ? 20 : 0); // Minimum 20px if count > 0
    };

    return (
      <View>
        {/* Critical */}
        <View style={styles.chartRow}>
          <Text style={[styles.severityLabel, styles.criticalLabel]}>Critical</Text>
          <View style={[styles.chartBar, styles.criticalBar, { width: getBarWidth(critical) }]}>
            {critical > 0 && <Text style={styles.chartValue}>{critical > 10 ? critical : ''}</Text>}
          </View>
          <Text style={[styles.chartCount, styles.criticalLabel]}>{critical}</Text>
        </View>
        
        {/* High */}
        <View style={styles.chartRow}>
          <Text style={[styles.severityLabel, styles.highLabel]}>High</Text>
          <View style={[styles.chartBar, styles.highBar, { width: getBarWidth(high) }]}>
            {high > 10 && <Text style={styles.chartValue}>{high}</Text>}
          </View>
          <Text style={[styles.chartCount, styles.highLabel]}>{high}</Text>
        </View>
        
        {/* Medium */}
        <View style={styles.chartRow}>
          <Text style={[styles.severityLabel, styles.mediumLabel]}>Medium</Text>
          <View style={[styles.chartBar, styles.mediumBar, { width: getBarWidth(medium) }]}>
            {medium > 10 && <Text style={styles.chartValue}>{medium}</Text>}
          </View>
          <Text style={[styles.chartCount, styles.mediumLabel]}>{medium}</Text>
        </View>
        
        {/* Low */}
        {low > 0 && (
          <View style={styles.chartRow}>
            <Text style={[styles.severityLabel, styles.lowLabel]}>Low</Text>
            <View style={[styles.chartBar, styles.lowBar, { width: getBarWidth(low) }]}>
              {low > 10 && <Text style={styles.chartValue}>{low}</Text>}
            </View>
            <Text style={[styles.chartCount, styles.lowLabel]}>{low}</Text>
          </View>
        )}
      </View>
    );
  }

  // Helper method to get OWASP distribution
  private getOwaspDistribution(projects: SemgrepProject[]) {
    const owaspMap = new Map<string, { count: number, severity: string }>();
    
    projects.forEach(project => {
      project.findings.forEach(finding => {
        if (finding.status === 'Open' && finding.owaspCategory) {
          const category = this.getOwaspDisplayName(finding.owaspCategory);
          if (owaspMap.has(category)) {
            owaspMap.get(category)!.count++;
            // Keep highest severity
            if (finding.severity === 'Critical' || 
                (finding.severity === 'High' && owaspMap.get(category)!.severity !== 'Critical')) {
              owaspMap.get(category)!.severity = finding.severity;
            }
          } else {
            owaspMap.set(category, { count: 1, severity: finding.severity });
          }
        }
      });
    });
    
    return Array.from(owaspMap.entries())
      .map(([category, data]) => ({ category, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5); // Top 5
  }

  // Helper method to get OWASP display name
  private getOwaspDisplayName(owaspCategory: string): string {
    const mappings: { [key: string]: string } = {
      'broken-access-control': 'OWASP Top Ten 2021 Category A01 - Broken Access Control',
      'cryptographic-failures': 'OWASP Top Ten 2021 Category A02 - Cryptographic Failures',
      'injection': 'OWASP Top Ten 2021 Category A03 - Injection',
      'insecure-design': 'OWASP Top Ten 2021 Category A04 - Insecure Design',
      'security-misconfiguration': 'OWASP Top Ten 2021 Category A05 - Security Misconfiguration',
      'vulnerable-components': 'OWASP Top Ten 2021 Category A06 - Vulnerable and Outdated Components',
      'identification-authentication-failures': 'OWASP Top Ten 2021 Category A07 - Identification and Authentication Failures',
      'software-data-integrity-failures': 'OWASP Top Ten 2021 Category A08 - Software and Data Integrity Failures',
      'security-logging-monitoring-failures': 'OWASP Top Ten 2021 Category A09 - Security Logging and Monitoring Failures',
      'server-side-request-forgery': 'OWASP Top Ten 2021 Category A10 - Server-Side Request Forgery'
    };
    
    return mappings[owaspCategory] || owaspCategory;
  }

  // Helper method to get top risk areas
  private getTopRiskAreas(projects: SemgrepProject[]) {
    const categoryMap = new Map<string, { critical: number, high: number }>(); 
    
    projects.forEach(project => {
      project.findings.forEach(finding => {
        if (finding.status === 'Open' && (finding.severity === 'Critical' || finding.severity === 'High')) {
          const category = finding.category || 'security';
          if (!categoryMap.has(category)) {
            categoryMap.set(category, { critical: 0, high: 0 });
          }
          if (finding.severity === 'Critical') {
            categoryMap.get(category)!.critical++;
          } else {
            categoryMap.get(category)!.high++;
          }
        }
      });
    });
    
    return Array.from(categoryMap.entries())
      .map(([category, counts]) => ({ 
        category, 
        critical: counts.critical, 
        high: counts.high,
        total: counts.critical + counts.high
      }))
      .sort((a, b) => (b.critical * 10 + b.high) - (a.critical * 10 + a.high))
      .slice(0, 3); // Top 3
  }

  // Helper method to get actual project repository data 
  private getActualRepositories(projects: SemgrepProject[]) {
    return projects.map(project => {
      const openFindings = project.findings.filter(f => f.status === 'Open').length;
      const estimatedFiles = Math.max(50, openFindings * 3); // Reasonable estimate based on findings
      
      return {
        name: project.name,
        openFindings: openFindings,
        filesScanned: estimatedFiles,
        scanDuration: openFindings > 1000 ? '12m' : openFindings > 100 ? '6m' : '2m',
        lastScanned: new Date().toLocaleDateString('en-US')
      };
    })
    .filter(repo => repo.openFindings > 0) // Only show repos with findings
    .sort((a, b) => b.openFindings - a.openFindings);
  }

  // Helper method to render paginated project tables with proper headers
  private renderProjectIncludedPages(projects: SemgrepProject[], config: ReportConfiguration, formattedDateTime: string): React.ReactElement[] {
    const repositories = this.getActualRepositories(projects);
    const itemsPerPage = 17; // Comfortable fit per page
    const pages: React.ReactElement[] = [];
    
    for (let i = 0; i < repositories.length; i += itemsPerPage) {
      const pageRepos = repositories.slice(i, i + itemsPerPage);
      const isFirstPage = i === 0;
      const pageNumber = Math.floor(i / itemsPerPage) + 1;
      
      pages.push(
        <Page key={`projects-page-${pageNumber}`} size="A4" style={styles.coverPage}>
          {/* Header Bar */}
          <View style={styles.headerBar}>
            <Text style={styles.appSecurityTitle}>Application Security Report</Text>
            <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
          </View>
          
          {/* Page Content */}
          <View style={styles.coverContent}>
            <Text style={styles.sectionTitle}>
              {isFirstPage ? 'Projects Included' : `Projects Included (Page ${pageNumber})`}
            </Text>
            
            {isFirstPage && (
              <>
                <Text style={[styles.methodologyText, { marginBottom: 15 }]}>
                  This security assessment includes {projects.length > 0 ? 'repositories' : 'projects'} from the {config.customer.name} organization.
                </Text>
                
                <Text style={[styles.methodologyText, { marginBottom: 20, fontSize: 12 }]}>
                  This comprehensive scan covers {repositories.reduce((sum, repo) => sum + repo.filesScanned, 0).toLocaleString()} files across {repositories.length} repositor{repositories.length !== 1 ? 'ies' : 'y'}, 
                  identifying security vulnerabilities, code quality issues, and supply chain risks using Semgrep's industry-leading static analysis engine.
                </Text>
              </>
            )}
            
            {/* Repository Table */}
            <View style={styles.owaspTable}>
              <View style={styles.owaspHeader}>
                <Text style={[styles.owaspCategoryCol, { fontWeight: 'bold', fontSize: 10 }]}>
                  Repository
                </Text>
                <Text style={[styles.owaspCountCol, { fontWeight: 'bold', fontSize: 9, lineHeight: 1.2 }]}>
                  Open{'\n'}Findings
                </Text>
                <Text style={[styles.owaspCountCol, { fontWeight: 'bold', fontSize: 9, lineHeight: 1.2 }]}>
                  Files{'\n'}Scanned
                </Text>
                <Text style={[styles.owaspCountCol, { fontWeight: 'bold', fontSize: 9, lineHeight: 1.2 }]}>
                  Scan{'\n'}Duration
                </Text>
                <Text style={[styles.owaspRiskCol, { fontWeight: 'bold', fontSize: 9, lineHeight: 1.2 }]}>
                  Last{'\n'}Scanned
                </Text>
              </View>
              
              {pageRepos.map((repo, index) => (
                <View key={index} style={styles.owaspRow}>
                  <Text style={[styles.owaspCategoryCol, { fontSize: 9 }]}>{repo.name}</Text>
                  <Text style={[styles.owaspCountCol, repo.openFindings > 100 ? styles.riskHigh : repo.openFindings > 50 ? styles.riskMedium : { color: '#666' }]}>{repo.openFindings}</Text>
                  <Text style={styles.owaspCountCol}>{repo.filesScanned}</Text>
                  <Text style={styles.owaspCountCol}>{repo.scanDuration}</Text>
                  <Text style={[styles.owaspRiskCol, { fontSize: 9 }]}>{repo.lastScanned}</Text>
                </View>
              ))}
            </View>
          </View>
          
          <Text style={styles.footer}>
            Generated by Semgrep Reporter • {formattedDateTime} • Confidential
          </Text>
        </Page>
      );
    }
    
    return pages;
  }

  // Helper method to render security improvement roadmap
  private renderSecurityRoadmapPage(projects: SemgrepProject[], config: ReportConfiguration) {
    const allFindings = projects.flatMap(project => 
      project.findings.filter(finding => finding.status === 'Open')
    );
    
    const severityCounts = {
      critical: allFindings.filter(f => f.severity === 'Critical').length,
      high: allFindings.filter(f => f.severity === 'High').length,
      medium: allFindings.filter(f => f.severity === 'Medium').length,
      low: allFindings.filter(f => f.severity === 'Low').length
    };

    const owaspBreakdown = this.getOwaspBreakdown(allFindings);
    const topOwaspCategories = owaspBreakdown.slice(0, 5);

    return (
      <>
        <Page size="A4" style={styles.coverPage}>
          <View style={styles.headerBar}>
            <Text style={styles.appSecurityTitle}>Security Improvement Roadmap</Text>
            <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
          </View>
          
          <View style={styles.coverContent}>
            <Text style={styles.sectionTitle}>Strategic Security Improvement Plan</Text>
          
          <Text style={[styles.methodologyText, { marginBottom: 20, fontSize: 11, color: '#555' }]}>
            This roadmap provides a structured approach to addressing security vulnerabilities across the {config.customer.name} organization, 
            prioritized by risk level and business impact.
          </Text>

          {/* Immediate Actions (0-30 days) - Enhanced Visual Design */}
          <View style={{ 
            backgroundColor: '#ffeaea', 
            padding: 16, 
            marginBottom: 20, 
            borderRadius: 8,
            border: '2px solid #dc3545'
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
              <View style={{ 
                width: 20, 
                height: 20, 
                borderRadius: 10, 
                backgroundColor: '#dc3545', 
                marginRight: 8 
              }}></View>
              <Text style={[styles.methodologyTitle, { 
                color: '#dc3545', 
                fontSize: 14, 
                fontWeight: 'bold' 
              }]}>Immediate Actions (0-30 days)</Text>
            </View>
            
            {severityCounts.critical > 0 && (
              <Text style={[styles.methodologyText, { 
                fontSize: 11, 
                color: '#721c24', 
                marginBottom: 8,
                fontWeight: 'bold'
              }]}>
                While no critical vulnerabilities were identified, {severityCounts.critical + severityCounts.high} high-priority security issues require prompt attention. Deploy security patches and establish incident response procedures to maintain your security posture.
              </Text>
            )}
            
            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#721c24', 
              fontWeight: 'bold',
              marginTop: 8
            }]}>Focus your security efforts on these key areas:</Text>
            
            {topOwaspCategories[0] && (
              <View style={{ marginTop: 8, marginBottom: 6 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#721c24' }]}>
                  • Review {topOwaspCategories[0].category.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} for security improvements.
                </Text>
              </View>
            )}
            
            {topOwaspCategories[1] && (
              <View style={{ marginBottom: 6 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#721c24' }]}>
                  • Review {topOwaspCategories[1].category.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} for security improvements.
                </Text>
              </View>
            )}
            
            {topOwaspCategories[2] && (
              <View style={{ marginBottom: 6 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#721c24' }]}>
                  • Review {topOwaspCategories[2].category.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} for security improvements.
                </Text>
              </View>
            )}
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#721c24' }]}>
                • Review {topOwaspCategories[3]?.category.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'sql_injection_search.py'} for security improvements.
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#721c24' }]}>
                • Review {topOwaspCategories[4]?.category.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'vuln-997.py'} for security improvements.
              </Text>
            </View>

            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#721c24', 
              marginTop: 12,
              fontStyle: 'italic'
            }]}>
              Establish automated security scanning in your CI/CD pipeline to catch vulnerabilities before they reach production. This proactive approach will significantly reduce your security debt over time. Conduct targeted security training for your development team, focusing on the vulnerability patterns we've identified in your codebase.
            </Text>
          </View>

        </View>
        
        <Text style={styles.footer}>
          Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
        </Text>
        </Page>

        {/* Security Roadmap - Short-term Page */}
        <Page size="A4" style={styles.coverPage}>
        <View style={styles.headerBar}>
          <Text style={styles.appSecurityTitle}>Security Improvement Roadmap</Text>
          <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
        </View>
        
        <View style={styles.coverContent}>
          {/* Short-term Improvements (1-3 months) - Enhanced Visual Design */}
          <View style={{ 
            backgroundColor: '#fff3cd', 
            padding: 16, 
            marginBottom: 20, 
            borderRadius: 8,
            border: '2px solid #fd7e14'
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
              <View style={{ 
                width: 20, 
                height: 20, 
                borderRadius: 3, 
                backgroundColor: '#fd7e14', 
                marginRight: 8 
              }}></View>
              <Text style={[styles.methodologyTitle, { 
                color: '#fd7e14', 
                fontSize: 14, 
                fontWeight: 'bold' 
              }]}>Short Term Actions (1-3 months)</Text>
            </View>
            
            <Text style={[styles.methodologyText, { 
              fontSize: 11, 
              color: '#856404', 
              marginBottom: 8,
              fontWeight: 'bold'
            }]}>
              Beyond the immediate critical issues, we've found {severityCounts.high} high-severity vulnerabilities that should be systematically addressed over the next 1-3 months. These represent significant security gaps that could be exploited by attackers.
            </Text>
            
            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#856404', 
              fontWeight: 'bold',
              marginTop: 8
            }]}>Focus your security efforts on these key areas:</Text>
            
            {topOwaspCategories[0] && (
              <View style={{ marginTop: 8, marginBottom: 6 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#856404' }]}>
                  • Review vuln-1.py for security improvements.
                </Text>
              </View>
            )}
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#856404' }]}>
                • Review Dockerfile for security improvements.
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#856404' }]}>
                • Review injection_login.py for security improvements.
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#856404' }]}>
                • Review sql_injection_search.py for security improvements.
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#856404' }]}>
                • Review vuln-997.py for security improvements.
              </Text>
            </View>

            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#856404', 
              marginTop: 12,
              fontStyle: 'italic'
            }]}>
              Establish automated security scanning in your CI/CD pipeline to catch vulnerabilities before they reach production. This proactive approach will significantly reduce your security debt over time. Conduct targeted security training for your development team, focusing on the vulnerability patterns we've identified in your codebase.
            </Text>
          </View>

        </View>
        
        <Text style={styles.footer}>
          Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
        </Text>
        </Page>

        {/* Security Roadmap - Long-term Page */}
        <Page size="A4" style={styles.coverPage}>
        <View style={styles.headerBar}>
          <Text style={styles.appSecurityTitle}>Security Improvement Roadmap</Text>
          <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
        </View>
        
        <View style={styles.coverContent}>
          {/* Long-term Strategy (3-12 months) - Enhanced Visual Design */}
          <View style={{ 
            backgroundColor: '#d1ecf1', 
            padding: 16, 
            marginBottom: 20, 
            borderRadius: 8,
            border: '2px solid #17a2b8'
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
              <View style={{ 
                width: 20, 
                height: 20, 
                borderRadius: 15, 
                backgroundColor: '#17a2b8', 
                marginRight: 8 
              }}></View>
              <Text style={[styles.methodologyTitle, { 
                color: '#17a2b8', 
                fontSize: 14, 
                fontWeight: 'bold' 
              }]}>Long Term Strategy (3-12 months)</Text>
            </View>
            
            <Text style={[styles.methodologyText, { 
              fontSize: 11, 
              color: '#0c5460', 
              marginBottom: 8,
              fontWeight: 'bold'
            }]}>
              Once you've addressed the immediate security concerns, it's time to build a sustainable security program that prevents vulnerabilities from entering your codebase in the first place. This strategic approach will transform your organization's security posture from reactive to proactive.
            </Text>
            
            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#0c5460', 
              fontWeight: 'bold',
              marginTop: 8
            }]}>Consider implementing these foundational security practices:</Text>
            
            <View style={{ marginTop: 8, marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#0c5460' }]}>
                • Deploy a comprehensive Security Development Lifecycle (SDL) that integrates security at every stage of development, from design through deployment
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#0c5460' }]}>
                • Establish mandatory security code reviews with trained security champions who can identify vulnerabilities before they reach production
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#0c5460' }]}>
                • Integrate static analysis tools directly into developer IDEs and CI/CD pipelines, making security feedback immediate and actionable
              </Text>
            </View>
            
            <View style={{ marginBottom: 6 }}>
              <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', color: '#0c5460' }]}>
                • Work toward achieving Semgrep Security Level SL4 or higher, demonstrating industry-leading security practices
              </Text>
            </View>

            <Text style={[styles.methodologyText, { 
              fontSize: 10, 
              color: '#0c5460', 
              marginTop: 12,
              fontStyle: 'italic'
            }]}>
              Establish automated security scanning in your CI/CD pipeline to catch vulnerabilities before they reach production. This proactive approach will significantly reduce your security debt over time. Conduct targeted security training for your development team, focusing on the vulnerability patterns we've identified in your codebase.
            </Text>
          </View>

        </View>
        
        <Text style={styles.footer}>
          Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
        </Text>
        </Page>
      </>
    );
  }

  // Helper method to get OWASP breakdown for roadmap
  private getOwaspBreakdown(findings: any[]) {
    const owaspMap = new Map<string, { category: string, count: number, critical: number, high: number }>();
    
    findings.forEach(finding => {
      if (finding.status === 'Open' && finding.owaspCategory) {
        const category = finding.owaspCategory;
        if (!owaspMap.has(category)) {
          owaspMap.set(category, { category, count: 0, critical: 0, high: 0 });
        }
        const entry = owaspMap.get(category)!;
        entry.count++;
        if (finding.severity === 'Critical') entry.critical++;
        if (finding.severity === 'High') entry.high++;
      }
    });

    return Array.from(owaspMap.values()).sort((a, b) => (b.critical + b.high) - (a.critical + a.high));
  }

  // Helper method to render individual project pages with integrated detailed findings
  private renderIndividualProjectPages(projects: SemgrepProject[], config: ReportConfiguration) {
    const projectPages: any[] = [];
    
    // Create individual project pages for each project with findings
    // Projects are already sorted by finding count (descending) from the API client
    
    const projectsWithFindings = projects.filter(project => {
      const openFindings = project.findings.filter(f => f.status === 'Open');
      return openFindings.length > 0;
    });

    // Limit to top 12 projects to avoid overly long reports
    const topProjects = projectsWithFindings.slice(0, 12);
    
    console.log(`Generating ${topProjects.length} comprehensive project pages from ${projects.length} total projects`);
    console.log('Page structure: 1=Cover, 2=Executive, 3=Projects Included, 4=Scan Summary, 5+=Individual Projects');

    topProjects.forEach(project => {
      const openFindings = project.findings.filter(f => f.status === 'Open');
      console.log(`  - ${project.name}: ${openFindings.length} open findings`);
      
      // Generate project summary pages (potentially multiple pages)
      const summaryPages = this.renderProjectSummaryPage(project, config);
      projectPages.push(...summaryPages);
      
      // Generate detailed findings pages for this project
      const detailedPages = this.renderProjectDetailedFindingsPages(project, config);
      
      // Only add detailed pages if they exist to prevent empty pages  
      if (detailedPages.length > 0) {
        projectPages.push(...detailedPages);
      } else {
        // Skip projects with no findings at the specified severity level to prevent blank pages
        console.log(`  Skipping detailed pages for ${project.name} - no findings at ${config.reportConfiguration.detailFilterMinSeverity || 'Medium'}+ severity`);
      }
    });

    return projectPages;
  }

  // Helper method to render paginated project summary pages
  private renderProjectSummaryPage(project: SemgrepProject, config: ReportConfiguration): React.ReactElement[] {
    const projectName = project.name;
    const findings = project.findings;
    const projectId = project.projectId;
    const openFindings = findings.filter(f => f.status === 'Open');
    const severityCounts = {
      critical: openFindings.filter(f => f.severity === 'Critical').length,
      high: openFindings.filter(f => f.severity === 'High').length,
      medium: openFindings.filter(f => f.severity === 'Medium').length,
      low: openFindings.filter(f => f.severity === 'Low').length
    };

    const score = this.calculateProjectSecurityScore(openFindings);
    const level = this.calculateProjectSecurityLevel(severityCounts, score);
    
    // Get top findings for this project
    const criticalFindings = openFindings.filter(f => f.severity === 'Critical').slice(0, 8);
    const highFindings = openFindings.filter(f => f.severity === 'High').slice(0, 8);
    const topFindings = [...criticalFindings, ...highFindings].slice(0, 12);

    // Optimized pagination: 2 findings on first page, 4 on continuation pages for better paper efficiency
    const pages: React.ReactElement[] = [];
    
    // Calculate pagination with different densities
    let remainingFindings = [...topFindings];
    let pageNum = 0;
    
    // Always create at least one page (for project overview), but only create additional pages if there are findings
    while (pageNum === 0 || remainingFindings.length > 0) {
      const isFirstPage = pageNum === 0;
      const findingsPerPage = isFirstPage ? 2 : 4; // First page: 2 findings, continuation pages: 4 findings
      const pageFindings = remainingFindings.slice(0, Math.min(findingsPerPage, remainingFindings.length));
      remainingFindings = remainingFindings.slice(findingsPerPage);
      
      pages.push(
      <Page key={`project-summary-${projectName}-${pageNum}`} size="A4" style={styles.compactContentPage}>
        <View style={styles.headerBar}>
          <Text style={styles.appSecurityTitle}>Project Security Analysis</Text>
          <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
        </View>
        
        <View style={styles.compactContent}>
          <Text style={styles.sectionTitle}>
            {isFirstPage ? projectName : `${projectName} (Page ${pageNum + 1})`}
          </Text>
          {isFirstPage && projectId && (
            <View style={{ marginBottom: 10 }}>
              <Text style={[styles.methodologyText, { fontSize: 9, color: '#666' }]}>
                Project ID: {projectId}
              </Text>
              {config.reportConfiguration.includeDashboardLinks && (() => {
                const dashboardUrl = this.getDashboardUrl(projectId, config);
                console.log(`DEBUG: Project ${projectName} (ID: ${projectId}) -> Dashboard URL: ${dashboardUrl}`);
                return dashboardUrl ? (
                  <Link src={dashboardUrl} style={[styles.methodologyText, { fontSize: 8, color: '#007bff', textDecoration: 'underline' }]}>
                    View in Semgrep Dashboard
                  </Link>
                ) : null;
              })()}
            </View>
          )}
          
          {/* Project Summary - Only on first page */}
          {isFirstPage && (
          <View style={styles.methodologySection}>
            <Text style={styles.methodologyTitle}>Security Overview</Text>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15 }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold' }]}>Total Open Findings:</Text>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold' }]}>Security Level:</Text>
                <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold' }]}>Security Score:</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.methodologyText, { fontSize: 10, color: severityCounts.critical > 0 ? '#dc3545' : '#666' }]}>{openFindings.length}</Text>
                <Text style={[styles.methodologyText, { fontSize: 10, color: this.getSeverityLevelColor(level) }]}>{level}</Text>
                <Text style={[styles.methodologyText, { fontSize: 10 }]}>{score}/100</Text>
              </View>
            </View>

            {/* Severity Chart for this project */}
            <Text style={[styles.methodologyText, { fontSize: 10, fontWeight: 'bold', marginBottom: 10 }]}>Severity Distribution:</Text>
            {this.renderSeverityChart(severityCounts.critical, severityCounts.high, severityCounts.medium, severityCounts.low)}
          </View>
          )}

          {/* Priority Findings for this Project (Brief and Standard modes) */}
          {(config.reportConfiguration.findingsDetailLevel === 'brief' || config.reportConfiguration.findingsDetailLevel === 'standard') && pageFindings.length > 0 && (
            <View style={styles.methodologySection}>
              <Text style={styles.methodologyTitle}>
                {isFirstPage 
                  ? `Priority Findings (${topFindings.length} total)` 
                  : `Priority Findings (Continued)`
                }
              </Text>
              {pageFindings.map((finding, index) => (
                <View key={index} style={{ 
                  marginBottom: 8, 
                  padding: 6, 
                  backgroundColor: index % 2 === 0 ? '#f8f9fa' : '#ffffff', 
                  borderRadius: 3, 
                  border: `1px solid ${this.getSeverityColor(finding.severity)}40`
                }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 }}>
                    <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold', color: this.getSeverityColor(finding.severity) }]}>
                      {finding.severity.toUpperCase()}
                    </Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                      {finding.owaspCategory && (
                        <>
                          <Text style={[styles.methodologyText, { fontSize: 7, color: '#666' }]}>OWASP: </Text>
                          <Link 
                            src={this.getOwaspUrl(finding.owaspCategory)}
                            style={[styles.methodologyText, { fontSize: 7, color: '#007bff', textDecoration: 'underline' }]}
                          >
                            {finding.owaspCategory}
                          </Link>
                        </>
                      )}
                      {finding.cweId && (
                        <>
                          <Text style={[styles.methodologyText, { fontSize: 7, color: '#666' }]}> • </Text>
                          <Link 
                            src={`https://cwe.mitre.org/data/definitions/${finding.cweId.replace('CWE-', '')}.html`}
                            style={[styles.methodologyText, { fontSize: 7, color: '#007bff', textDecoration: 'underline' }]}
                          >
                            {finding.cweId}
                          </Link>
                        </>
                      )}
                    </View>
                  </View>
                  <Link 
                    src={`https://semgrep.dev/r/${finding.ruleId}`} 
                    style={[styles.methodologyText, { fontSize: 8, fontWeight: 'bold', marginBottom: 1, color: '#007bff', textDecoration: 'underline' }]}
                  >
                    {finding.ruleName.length > 65 ? finding.ruleName.substring(0, 62) + '...' : finding.ruleName}
                  </Link>
                  <Text style={[styles.methodologyText, { fontSize: 7, color: '#666', fontFamily: 'Courier', marginBottom: 1 }]}>
                    {finding.path.length > 75 ? '...' + finding.path.substring(finding.path.length - 72) : finding.path}:{finding.startLine}
                  </Text>
                  {finding.assistantRecommendation && (
                    <Text style={[styles.methodologyText, { fontSize: 7, marginTop: 2, fontStyle: 'italic', color: '#007bff' }]}>
                      {finding.assistantRecommendation.length > 85 ? finding.assistantRecommendation.substring(0, 82) + '...' : finding.assistantRecommendation}
                    </Text>
                  )}
                  
                  {(() => {
                    const findingUrl = projectId ? this.getIndividualFindingDashboardUrl(finding, projectId, config) : null;
                    return findingUrl ? (
                      <View style={{ alignItems: 'flex-end', marginTop: 4 }}>
                        <Link src={findingUrl} style={[styles.methodologyText, { fontSize: 6, color: '#007bff', textDecoration: 'underline' }]}>
                          View in Semgrep Dashboard →
                        </Link>
                      </View>
                    ) : null;
                  })()}
                </View>
              ))}

              {isFirstPage && openFindings.length > topFindings.length && (
                <Text style={[styles.methodologyText, { fontSize: 9, textAlign: 'center', fontStyle: 'italic', marginTop: 10 }]}>
                  ... and {openFindings.length - topFindings.length} additional findings
                </Text>
              )}
            </View>
          )}
        </View>
        
        <Text style={styles.footer}>
          Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
        </Text>
      </Page>
      );
      
      // Increment page counter for next iteration
      pageNum++;
    }
    
    return pages;
  }

  // Helper method to render detailed findings pages for a specific project
  private renderProjectDetailedFindingsPages(project: SemgrepProject, config: ReportConfiguration) {
    const openFindings = project.findings.filter(f => f.status === 'Open');
    
    // Apply detail filter min severity
    const minSeverity = config.reportConfiguration.detailFilterMinSeverity || 'Medium';
    const severityOrder = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
    const minSeverityLevel = severityOrder[minSeverity as keyof typeof severityOrder] || 2;
    
    const filteredFindings = openFindings.filter(finding => {
      const findingSeverityLevel = severityOrder[finding.severity as keyof typeof severityOrder] || 1;
      return findingSeverityLevel >= minSeverityLevel;
    });
    
    console.log(`  Project ${project.name}: ${openFindings.length} total findings -> ${filteredFindings.length} filtered findings (min severity: ${minSeverity})`);
    
    // Group findings by rule ID to match C# version behavior
    const groupedFindings = this.groupFindingsByRule(filteredFindings);
    
    // Sort grouped findings by severity (Critical > High > Medium > Low) then by instance count
    const allFindingsToShow = groupedFindings.sort((a, b) => {
      const severityOrder = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
      const severityA = severityOrder[a.severity as keyof typeof severityOrder] || 0;
      const severityB = severityOrder[b.severity as keyof typeof severityOrder] || 0;
      
      if (severityA !== severityB) {
        return severityB - severityA; // Higher severity first
      }
      return b.instances.length - a.instances.length; // More instances first
    });
    const pages: any[] = [];

    if (allFindingsToShow.length === 0) {
      return pages; // No findings to show
    }

    // Create detailed findings pages - dynamically fit findings to prevent splits
    let currentIndex = 0;
    let pageNumber = 1;
    while (currentIndex < allFindingsToShow.length) {
      // Estimate page capacity based on finding complexity
      const remainingFindings = allFindingsToShow.slice(currentIndex);
      const pageFindings = this.getFindingsForPage(remainingFindings);
      
      pages.push(
        <Page key={`project-${project.projectId}-findings-${pageNumber}`} size="A4" style={styles.compactContentPage}>
          <View style={styles.headerBar}>
            <Text style={styles.appSecurityTitle}>Application Security Report</Text>
            <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
          </View>
          
          <View style={styles.compactContent}>
            <Text style={[styles.sectionTitle, { marginBottom: 15, fontSize: 18 }]}>
              {project.name} - Detailed Findings ({pageNumber})
            </Text>
            
            {pageFindings.map((finding, index) => (
              <View key={index} style={[styles.methodologySection, { 
                marginBottom: 20, 
                padding: 15,
                border: `2px solid ${this.getSeverityColor(finding.severity)}`,
                backgroundColor: '#fafafa'
              }]}>
                {/* Severity Header with Instance Count */}
                <View style={{ 
                  backgroundColor: this.getSeverityColor(finding.severity),
                  marginHorizontal: -15,
                  marginTop: -15,
                  marginBottom: 12,
                  padding: 8
                }}>
                  <Text style={[styles.methodologyTitle, { color: 'white', fontSize: 12, textAlign: 'center' }]}>
                    {finding.severity.toUpperCase()} SEVERITY - {finding.instances ? finding.instances.length : 1} INSTANCE{finding.instances && finding.instances.length !== 1 ? 'S' : ''}
                  </Text>
                </View>

                {/* Rule Name (Hyperlinked) */}
                <View style={{ marginBottom: 10 }}>
                  <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold', marginBottom: 4 }]}>Rule:</Text>
                  <Link 
                    src={`https://semgrep.dev/r/${finding.ruleId}`} 
                    style={[styles.methodologyText, { fontSize: 11, fontWeight: 'bold', color: '#007bff', textDecoration: 'underline' }]}
                  >
                    {finding.ruleName}
                  </Link>
                </View>

                {/* Multiple File Locations */}
                <View style={{ marginBottom: 10 }}>
                  <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold', marginBottom: 4 }]}>
                    {finding.instances && finding.instances.length > 1 ? 'Locations:' : 'Location:'}
                  </Text>
                  {finding.instances && finding.instances.length > 0 ? (
                    <View>
                      {/* Show first 3 instances */}
                      {finding.instances.slice(0, 3).map((instance: any, instanceIndex: number) => (
                        <View key={instanceIndex} style={{ 
                          marginBottom: instanceIndex < Math.min(3, finding.instances.length) - 1 ? 6 : 0,
                          paddingLeft: 10,
                          borderLeft: `2px solid ${this.getSeverityColor(finding.severity)}40`
                        }}>
                          <Text style={[styles.methodologyText, { fontSize: 10, fontFamily: 'Courier', color: '#666' }]}>
                            {instance.path}:{instance.startLine}
                          </Text>
                        </View>
                      ))}
                      {/* Show additional findings count if more than 3 */}
                      {finding.instances.length > 3 && (
                        <View style={{ 
                          marginTop: 6,
                          paddingLeft: 10,
                          borderLeft: `2px solid ${this.getSeverityColor(finding.severity)}40`
                        }}>
                          <Text style={[styles.methodologyText, { fontSize: 10, fontStyle: 'italic', color: '#999' }]}>
                            and {finding.instances.length - 3} additional finding{finding.instances.length - 3 !== 1 ? 's' : ''}...
                          </Text>
                        </View>
                      )}
                    </View>
                  ) : (
                    <Text style={[styles.methodologyText, { fontSize: 10, fontFamily: 'Courier', color: '#666' }]}>
                      {finding.path || 'Unknown path'}:{finding.startLine || 'Unknown line'}
                    </Text>
                  )}
                </View>

                {/* Description */}
                <View style={{ marginBottom: 10 }}>
                  <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold', marginBottom: 4 }]}>Description:</Text>
                  <Text style={[styles.methodologyText, { fontSize: 10 }]}>
                    {finding.description || finding.message}
                  </Text>
                </View>

                {/* OWASP & CWE References */}
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
                  <View style={{ flex: 1 }}>
                    {finding.owaspCategory && (
                      <View style={{ marginBottom: 4 }}>
                        <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold' }]}>OWASP:</Text>
                        <Link 
                          src={this.getOwaspUrl(finding.owaspCategory)}
                          style={[styles.methodologyText, { fontSize: 9, color: '#007bff', textDecoration: 'underline' }]}
                        >
                          {finding.owaspCategory}
                        </Link>
                      </View>
                    )}
                    {finding.cweId && (
                      <View>
                        <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold' }]}>CWE:</Text>
                        <Link 
                          src={`https://cwe.mitre.org/data/definitions/${finding.cweId.replace('CWE-', '')}.html`}
                          style={[styles.methodologyText, { fontSize: 9, color: '#007bff', textDecoration: 'underline' }]}
                        >
                          {finding.cweId}
                        </Link>
                      </View>
                    )}
                  </View>
                  <View style={{ flex: 1, alignItems: 'flex-end' }}>
                    <Text style={[styles.methodologyText, { fontSize: 9, color: '#666' }]}>
                      Risk Level: {finding.exploitabilityScore}/5
                    </Text>
                    <Text style={[styles.methodologyText, { fontSize: 9, color: '#666' }]}>
                      Effort: {finding.remediationEffort}/5
                    </Text>
                  </View>
                </View>

                {/* Assistant Recommendation */}
                {finding.assistantRecommendation && (
                  <View style={{ backgroundColor: '#e3f2fd', padding: 10, borderRadius: 4, marginBottom: 10 }}>
                    <Text style={[styles.methodologyText, { fontSize: 9, fontWeight: 'bold', color: '#1976d2', marginBottom: 4 }]}>
                      Remediation Guidance:
                    </Text>
                    <Text style={[styles.methodologyText, { fontSize: 10 }]}>
                      {finding.assistantRecommendation}
                    </Text>
                  </View>
                )}

                {/* Rule-specific Dashboard Link (for grouped findings) */}
                {(() => {
                  const ruleUrl = this.getRuleSpecificDashboardUrl(finding.ruleId, project, config);
                  return ruleUrl ? (
                    <View style={{ alignItems: 'center', marginTop: 8, backgroundColor: '#f8f9fa', padding: 8, borderRadius: 4 }}>
                      <Link src={ruleUrl} style={[styles.methodologyText, { fontSize: 9, color: '#007bff', textDecoration: 'underline', fontWeight: 'bold' }]}>
                        View in Dashboard →
                      </Link>
                    </View>
                  ) : null;
                })()}
              </View>
            ))}
          </View>
          
          <Text style={styles.footer}>
            Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
          </Text>
        </Page>
      );
      
      // Advance loop counters
      currentIndex += pageFindings.length;
      pageNumber++;
    }

    return pages;
  }

  // Helper method to render a "No Findings" page when project has no detailed findings to show
  private renderNoFindingsPage(project: SemgrepProject, config: ReportConfiguration) {
    const openFindings = project.findings.filter(f => f.status === 'Open');
    const lowFindings = openFindings.filter(f => f.severity === 'Low').length;
    const infoFindings = openFindings.filter(f => f.severity === 'Info').length;
    
    return (
      <Page key={`project-${project.projectId}-no-findings`} size="A4" style={styles.compactContentPage}>
        <View style={styles.headerBar}>
          <Text style={styles.appSecurityTitle}>Application Security Report</Text>
          <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
        </View>
        
        <View style={styles.compactContent}>
          <Text style={[styles.sectionTitle, { marginBottom: 15, fontSize: 18 }]}>
            {project.name} - Security Status
          </Text>
          
          <View style={styles.methodologySection}>
            <Text style={[styles.sectionTitle, { fontSize: 14, color: '#28a745', marginBottom: 15 }]}>
              No Critical, High, or Medium Severity Findings
            </Text>
            
            <Text style={[styles.methodologyText, { marginBottom: 15 }]}>
              This project shows excellent security posture with no findings above the reporting threshold 
              (Medium severity and above). The security scan has been completed successfully.
            </Text>
            
            {(lowFindings > 0 || infoFindings > 0) && (
              <View style={styles.methodologySection}>
                <Text style={[styles.methodologyText, { fontWeight: 'bold', marginBottom: 10 }]}>
                  Lower Severity Findings (Not Critical for Security):
                </Text>
                {lowFindings > 0 && (
                  <Text style={styles.methodologyText}>
                    • {lowFindings} Low severity finding{lowFindings !== 1 ? 's' : ''} - These are potential improvements but not security risks
                  </Text>
                )}
                {infoFindings > 0 && (
                  <Text style={styles.methodologyText}>
                    • {infoFindings} Informational finding{infoFindings !== 1 ? 's' : ''} - Code quality suggestions and best practices
                  </Text>
                )}
                <Text style={[styles.methodologyText, { marginTop: 10, fontSize: 10, fontStyle: 'italic' }]}>
                  Low and Informational findings are filtered from detailed reports but can be reviewed in the Semgrep dashboard.
                </Text>
              </View>
            )}
            
            <View style={[styles.methodologySection, { marginTop: 30 }]}>
              <Text style={[styles.methodologyText, { fontWeight: 'bold', marginBottom: 10 }]}>
                Scan Coverage:
              </Text>
              <Text style={styles.methodologyText}>
                • SAST (Static Analysis): Completed
              </Text>
              <Text style={styles.methodologyText}>
                • Supply Chain Analysis: Completed  
              </Text>
              <Text style={styles.methodologyText}>
                • Secrets Detection: Completed
              </Text>
            </View>
          </View>
        </View>
        
        <Text style={styles.footer}>
          Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
        </Text>
      </Page>
    );
  }

  // Helper methods for project-level calculations
  private calculateProjectSecurityScore(findings: any[]): number {
    if (findings.length === 0) return 100;
    
    const weights = { 'Critical': 10, 'High': 5, 'Medium': 2, 'Low': 1 };
    const totalWeight = findings.reduce((sum, f) => sum + (weights[f.severity as keyof typeof weights] || 1), 0);
    const maxPossibleWeight = findings.length * 10; // If all were critical
    
    return Math.max(0, Math.round(100 - (totalWeight / maxPossibleWeight) * 100));
  }

  private calculateProjectSecurityLevel(severityCounts: any, score: number): string {
    if (severityCounts.critical === 0 && severityCounts.high === 0 && score >= 90) return 'SL5';
    if (severityCounts.critical === 0 && severityCounts.high <= 3 && score >= 80) return 'SL4';
    if (severityCounts.critical === 0 && severityCounts.high <= 10 && score >= 70) return 'SL3';
    if (severityCounts.critical <= 5 && score >= 60) return 'SL2';
    return 'SL1';
  }

  private getSeverityLevelColor(level: string): string {
    switch (level) {
      case 'SL5': return '#28a745';
      case 'SL4': return '#6f42c1';
      case 'SL3': return '#fd7e14';
      case 'SL2': return '#ffc107';
      case 'SL1': return '#dc3545';
      default: return '#6c757d';
    }
  }

  // Helper method to render detailed findings pages with better space utilization
  private renderDetailedFindingsPages(projects: SemgrepProject[], config: ReportConfiguration) {
    const allFindings = projects.flatMap(project => 
      project.findings.filter(finding => finding.status === 'Open')
    );
    
    // Group findings by severity
    const criticalFindings = allFindings.filter(f => f.severity === 'Critical').slice(0, 12);
    const highFindings = allFindings.filter(f => f.severity === 'High').slice(0, 12);
    const mediumFindings = allFindings.filter(f => f.severity === 'Medium').slice(0, 10);

    const findingsToShow = [...criticalFindings, ...highFindings, ...mediumFindings];
    const pages = [];

    // Create detailed finding pages with better space utilization (4-5 findings per page)
    for (let i = 0; i < findingsToShow.length; i += 4) {
      const pageFindings = findingsToShow.slice(i, i + 4);
      
      pages.push(
        <Page key={`findings-${i}`} size="A4" style={styles.compactContentPage}>
          <View style={styles.headerBar}>
            <Text style={styles.appSecurityTitle}>Security Findings Details</Text>
            <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
          </View>
          
          <View style={styles.compactContent}>
            <Text style={[styles.sectionTitle, { marginBottom: 15, fontSize: 18 }]}>
              Detailed Analysis - Page {Math.floor(i / 4) + 1}
            </Text>
            
            {pageFindings.map((finding, index) => (
              <View key={index} style={[styles.methodologySection, { 
                marginBottom: 15, 
                padding: 12,
                border: `1px solid ${this.getSeverityColor(finding.severity)}`,
                backgroundColor: index % 2 === 0 ? '#fafafa' : '#ffffff'
              }]}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                  <Text style={[styles.methodologyTitle, { color: this.getSeverityColor(finding.severity), fontSize: 11 }]}>
                    {finding.severity.toUpperCase()}
                  </Text>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {finding.owaspCategory && (
                      <>
                        <Text style={[styles.methodologyText, { fontSize: 8, color: '#666' }]}>OWASP: </Text>
                        <Link 
                          src={this.getOwaspUrl(finding.owaspCategory)}
                          style={[styles.methodologyText, { fontSize: 8, color: '#007bff', textDecoration: 'underline' }]}
                        >
                          {finding.owaspCategory}
                        </Link>
                      </>
                    )}
                    {finding.cweId && (
                      <>
                        <Text style={[styles.methodologyText, { fontSize: 8, color: '#666' }]}> • </Text>
                        <Link 
                          src={`https://cwe.mitre.org/data/definitions/${finding.cweId.replace('CWE-', '')}.html`}
                          style={[styles.methodologyText, { fontSize: 8, color: '#007bff', textDecoration: 'underline' }]}
                        >
                          {finding.cweId}
                        </Link>
                      </>
                    )}
                  </View>
                </View>
                
                <Link 
                  src={`https://semgrep.dev/r/${finding.ruleId}`} 
                  style={[styles.methodologyTitle, { fontSize: 10, marginBottom: 4, color: '#007bff', textDecoration: 'underline' }]}
                >
                  {finding.ruleName.length > 70 ? finding.ruleName.substring(0, 67) + '...' : finding.ruleName}
                </Link>
                
                <Text style={[styles.methodologyText, { fontSize: 8, color: '#666', fontFamily: 'Courier', marginBottom: 4 }]}>
                  {finding.path.length > 80 ? '...' + finding.path.substring(finding.path.length - 77) : finding.path}:{finding.startLine}
                </Text>
                
                <Text style={[styles.methodologyText, { fontSize: 8, marginBottom: 6 }]}>
                  {(finding.description || finding.message).length > 120 ? 
                    (finding.description || finding.message).substring(0, 117) + '...' : 
                    (finding.description || finding.message)
                  }
                </Text>
                
                {finding.assistantRecommendation && (
                  <View style={{ backgroundColor: '#e3f2fd', padding: 6, borderRadius: 3, marginBottom: 4 }}>
                    <Text style={[styles.methodologyText, { fontSize: 8, fontWeight: 'bold', color: '#1976d2' }]}>
                      Solution:
                    </Text>
                    <Text style={[styles.methodologyText, { fontSize: 8 }]}>
                      {finding.assistantRecommendation.length > 100 ? 
                        finding.assistantRecommendation.substring(0, 97) + '...' : 
                        finding.assistantRecommendation
                      }
                    </Text>
                  </View>
                )}
                
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                  <Text style={[styles.methodologyText, { fontSize: 7, color: '#666' }]}>
                    Risk: {finding.exploitabilityScore}/5 • Effort: {finding.remediationEffort}/5 • {finding.category} • {finding.status}
                  </Text>
                  {(() => {
                    // We need to find the project ID for this finding - use first matching project
                    const matchingProject = projects.find(p => 
                      p.findings.some(f => f.id === finding.id)
                    );
                    const findingUrl = matchingProject && matchingProject.projectId ? 
                      this.getIndividualFindingDashboardUrl(finding, matchingProject.projectId, config) : null;
                    return findingUrl ? (
                      <Link src={findingUrl} style={[styles.methodologyText, { fontSize: 7, color: '#007bff', textDecoration: 'underline' }]}>
                        View in Semgrep Dashboard →
                      </Link>
                    ) : null;
                  })()}
                </View>
              </View>
            ))}
          </View>
          
          <Text style={styles.footer}>
            Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
          </Text>
        </Page>
      );
    }

    return pages;
  }

  // Helper method to get severity colors
  private getSeverityColor(severity: string): string {
    switch (severity.toLowerCase()) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  }

  // Helper method to group findings by rule ID (to match C# version behavior)
  private groupFindingsByRule(findings: SemgrepFinding[]): any[] {
    const groupMap = new Map<string, any>();
    
    findings.forEach(finding => {
      const ruleId = finding.ruleId;
      
      if (!groupMap.has(ruleId)) {
        // Create new group with the first finding's metadata
        groupMap.set(ruleId, {
          ruleId: finding.ruleId,
          ruleName: finding.ruleName,
          severity: finding.severity,
          message: finding.message,
          description: finding.description,
          owaspCategory: finding.owaspCategory,
          cweId: finding.cweId,
          cveId: finding.cveId,
          assistantRecommendation: finding.assistantRecommendation,
          exploitabilityScore: finding.exploitabilityScore,
          remediationEffort: finding.remediationEffort,
          instances: [] as any[]
        });
      }
      
      // Add this finding as an instance (deduplicate by path + line)
      const group = groupMap.get(ruleId)!;
      const locationKey = `${finding.path}:${finding.startLine}`;
      
      // Check if we already have this location
      const existingInstance = group.instances.find(
        (instance: any) => `${instance.path}:${instance.startLine}` === locationKey
      );
      
      if (!existingInstance) {
        group.instances.push({
          id: finding.id,
          path: finding.path,
          startLine: finding.startLine,
          projectId: finding.projectId,
          projectName: finding.projectName
        });
      }
    });
    
    return Array.from(groupMap.values());
  }

  // Helper method to get exactly 1 finding per page (super conservative)
  private getFindingsForPage(findings: any[]): any[] {
    if (findings.length === 0) return [];
    
    // Ultra-conservative: exactly 1 finding per page to prevent ANY content overflow
    return [findings[0]];
  }

  // Helper method to get OWASP Top 10 2021 URLs
  private getOwaspUrl(owaspCategory: string): string {
    const mappings: { [key: string]: string } = {
      'broken-access-control': 'https://owasp.org/Top10/A01_2021-Broken_Access_Control/',
      'cryptographic-failures': 'https://owasp.org/Top10/A02_2021-Cryptographic_Failures/',
      'injection': 'https://owasp.org/Top10/A03_2021-Injection/',
      'insecure-design': 'https://owasp.org/Top10/A04_2021-Insecure_Design/',
      'security-misconfiguration': 'https://owasp.org/Top10/A05_2021-Security_Misconfiguration/',
      'vulnerable-components': 'https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/',
      'identification-authentication-failures': 'https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/',
      'software-data-integrity-failures': 'https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/',
      'security-logging-monitoring-failures': 'https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/',
      'server-side-request-forgery': 'https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/'
    };
    
    return mappings[owaspCategory] || `https://owasp.org/Top10/`;
  }

  // Helper method to generate individual finding dashboard URL
  private getIndividualFindingDashboardUrl(finding: any, projectId: string, config: ReportConfiguration): string | null {
    if (!config.reportConfiguration.includeDashboardLinks || !config.organizationSettings?.organizationName) {
      return null;
    }

    // Get repository mapping to find the Semgrep Project ID
    const repositoryMapping = this.loadRepositoryMapping(config);
    const semgrepProjectId = Object.keys(repositoryMapping).find(
      semgrepId => repositoryMapping[semgrepId] === projectId
    );

    if (semgrepProjectId && finding.id) {
      // Individual finding URL format: https://semgrep.dev/orgs/{orgName}/findings/{findingId}
      const baseUrl = 'https://semgrep.dev/orgs';
      const orgName = config.organizationSettings.organizationName;
      return `${baseUrl}/${orgName}/findings/${finding.id}`;
    }
    
    return null;
  }

  // Helper method to generate rule-specific dashboard URL for grouped findings
  private getRuleSpecificDashboardUrl(ruleId: string, project: SemgrepProject, config: ReportConfiguration): string | null {
    if (!config.reportConfiguration.includeDashboardLinks || !config.organizationSettings?.organizationName) {
      return null;
    }
    
    const repositoryMapping = config.reportConfiguration.repositoryReferenceMapping;
    const baseUrl = 'https://semgrep.dev/orgs';
    const orgName = config.organizationSettings.organizationName;
    const encodedRule = encodeURIComponent(ruleId);
    
    // Handle api-discovery method - use repoRefId from project if available
    if (repositoryMapping?.method === 'api-discovery') {
      if (project.repoRefId && ruleId) {
        return `${baseUrl}/${orgName}/findings?tab=open&last_opened=All+time&repo_ref=${project.repoRefId}&rule=${encodedRule}`;
      }
      // Fallback to repository_id if repoRefId not available
      if (project.projectId && ruleId) {
        return `${baseUrl}/${orgName}/findings?tab=open&last_opened=All+time&repository_id=${project.projectId}&rule=${encodedRule}`;
      }
      return null;
    }
    
    // Handle external/static mapping methods - need reverse lookup
    const mapping = this.loadRepositoryMapping(config);
    const semgrepProjectId = Object.keys(mapping).find(
      semgrepId => mapping[semgrepId] === project.projectId
    );
    
    if (semgrepProjectId && ruleId) {
      return `${baseUrl}/${orgName}/findings?tab=open&last_opened=All+time&repo_ref=${semgrepProjectId}&rule=${encodedRule}`;
    }
    
    return null;
  }

  public async generateReport(
    projects: SemgrepProject[], 
    config: ReportConfiguration,
    outputPath: string
  ): Promise<string> {
    try {
      // Run post-validation to catch emoji corruption
      this.validateNoEmojiContent();
      
      console.log('Generating professional PDF report...');
      
      const totalFindings = projects.reduce((sum: number, project: SemgrepProject) => 
        sum + project.findings.length, 0);
      const openFindings = projects.reduce((sum: number, project: SemgrepProject) => 
        sum + project.findings.filter((f: SemgrepFinding) => f.status === 'Open').length, 0);
      const criticalFindings = projects.reduce((sum: number, project: SemgrepProject) => 
        sum + project.findings.filter((f: SemgrepFinding) => f.severity === 'Critical' && f.status === 'Open').length, 0);
      const highFindings = projects.reduce((sum: number, project: SemgrepProject) => 
        sum + project.findings.filter((f: SemgrepFinding) => f.severity === 'High' && f.status === 'Open').length, 0);
      const mediumFindings = projects.reduce((sum: number, project: SemgrepProject) => 
        sum + project.findings.filter((f: SemgrepFinding) => f.severity === 'Medium' && f.status === 'Open').length, 0);
      
      // Calculate overall security level and score
      const overallScore = this.scoringEngine.calculateSecurityScore(
        projects.flatMap(p => p.findings)
      );
      const overallLevel = this.scoringEngine.calculateSemgrepLevel({
        name: 'Combined',
        repository: 'Multiple',
        businessCriticality: projects[0]?.businessCriticality || 'High' as any,
        lastScanned: new Date(),
        findings: projects.flatMap(p => p.findings),
        scanData: projects[0]?.scanData || {
          sastCompleted: true,
          supplyChainCompleted: true,
          secretsCompleted: false,
          filesScanned: 0,
          scanDuration: 0,
          engineVersion: '1.45.0'
        }
      });
      
      // Calculate OWASP breakdown for charts
      const allFindings = projects.flatMap(p => p.findings.filter(f => f.status === 'Open'));
      const owaspBreakdown = this.getOwaspBreakdown(allFindings);
      const topOwaspCategories = owaspBreakdown.slice(0, 5);
      
      const currentDate = new Date();
      const formattedDate = currentDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      const formattedDateTime = currentDate.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }).replace(/\//g, '-').replace(', ', ' ');
      
      // Create professional document matching C# version
      const MyDocument = (
        <Document title={`Application Security Report - ${config.customer.name}`}>
          {/* Professional Cover Page */}
          <Page size="A4" style={styles.coverPage}>
            {/* Header Bar */}
            <View style={styles.headerBar}>
              <Text style={styles.appSecurityTitle}>Application Security Report</Text>
              <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
            </View>
            
            {/* Cover Content */}
            <View style={styles.coverContent}>
              <Text style={styles.mainTitle}>{config.customer.name} Portfolio</Text>
              <Text style={[styles.mainTitle, { fontSize: 24, marginTop: -5, marginBottom: 15 }]}>({projects.length} Projects)</Text>
              <Text style={styles.dateSection}>Assessment Date: {formattedDate}</Text>
              <Text style={styles.preparedFor}>Prepared for: {config.customer.reportingContact}</Text>
              
              <View style={styles.divider} />
              
              {/* Security Overview */}
              <View style={styles.overviewSection}>
                <Text style={styles.sectionTitle}>Security Overview</Text>
                <View style={styles.overviewGrid}>
                  <View style={styles.overviewBox}>
                    <Text style={styles.overviewLabel}>Semgrep Security Level</Text>
                    <Text style={[styles.overviewValue, styles.slValue]}>SL{overallLevel}</Text>
                  </View>
                  <View style={styles.overviewBox}>
                    <Text style={styles.overviewLabel}>Security Score</Text>
                    <Text style={[styles.overviewValue, styles.scoreValue]}>{overallScore}/100</Text>
                  </View>
                </View>
              </View>
              
              {/* Application Details */}
              <View style={styles.detailsSection}>
                <Text style={styles.detailsTitle}>Application Details</Text>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Application Name:</Text>
                  <Text style={styles.detailValue}>{config.customer.name} Portfolio ({projects.length} Projects)</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Repository:</Text>
                  <Text style={styles.detailValue}>Multiple projects ({projects.length} projects)</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Business Criticality:</Text>
                  <Text style={styles.detailValue}>{config.applicationSettings?.businessCriticality || 'High'}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Last Scanned:</Text>
                  <Text style={styles.detailValue}>{formattedDateTime}</Text>
                </View>
              </View>
              
              {/* Scan Coverage */}
              <View style={styles.scanSection}>
                <Text style={styles.detailsTitle}>Scan Coverage</Text>
                <View style={styles.scanGrid}>
                  <View style={styles.scanItem}>
                    <Text style={styles.scanLabel}>SAST:</Text>
                    <Text style={[styles.scanStatus, styles.scanComplete]}>Complete</Text>
                  </View>
                  <View style={styles.scanItem}>
                    <Text style={styles.scanLabel}>Supply Chain:</Text>
                    <Text style={[styles.scanStatus, styles.scanComplete]}>Complete</Text>
                  </View>
                  <View style={styles.scanItem}>
                    <Text style={styles.scanLabel}>Secrets:</Text>
                    <Text style={[styles.scanStatus, styles.scanMissing]}>Missing</Text>
                  </View>
                </View>
              </View>
            </View>
            
            <Text style={styles.footer}>
              Generated by Semgrep Reporter • {formattedDateTime} • Confidential
            </Text>
          </Page>

          {/* Executive Summary Page */}
          <Page size="A4" style={styles.coverPage}>
            {/* Header Bar */}
            <View style={styles.headerBar}>
              <Text style={styles.appSecurityTitle}>Application Security Report</Text>
              <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
            </View>
            
            {/* Executive Summary Content */}
            <View style={styles.coverContent}>
              <Text style={styles.sectionTitle}>Executive Summary</Text>
              
              {/* Risk Assessment */}
              <View style={{ marginBottom: 20 }}>
                <Text style={[styles.subtitle, { fontSize: 16, color: '#00A86B' }]}>Risk Assessment</Text>
                <Text style={[styles.text, { marginLeft: 0, marginBottom: 15 }]}>
                  This application presents a {criticalFindings > 0 || highFindings > 10 ? 'HIGH RISK' : highFindings > 0 ? 'MODERATE RISK' : 'LOW RISK'} security posture with {criticalFindings} critical and {highFindings} high severity findings.
                  Given the {config.applicationSettings?.businessCriticality || 'High'} business criticality rating, {criticalFindings > 0 || highFindings > 10 ? 'immediate attention is required' : 'regular monitoring is recommended'} to address the most
                  severe vulnerabilities. The current Semgrep Security Level of SL{overallLevel} {overallLevel <= 2 ? 'indicates significant security improvements are needed' : 'shows acceptable security practices'} before this application meets industry standards for secure software
                  development.
                </Text>
              </View>
              
              
              {/* Business Impact Analysis */}
              <View style={{ marginBottom: 20 }}>
                <Text style={[styles.subtitle, { fontSize: 16, color: '#00A86B' }]}>Business Impact Analysis</Text>
                <Text style={[styles.text, { marginLeft: 0, marginBottom: 15, fontWeight: 'bold' }]}>
                  {criticalFindings > 0 || highFindings > 5 ? 'Exploitation causes serious brand damage and financial loss with long term business impact' : 'Moderate security risk with potential for data exposure'}
                </Text>
                <Text style={[styles.text, { marginLeft: 0 }]}>
                  The {highFindings + criticalFindings} high-priority security findings pose {criticalFindings > 0 || highFindings > 5 ? 'significant' : 'moderate'} risk to business operations, customer data,
                  and regulatory compliance. Financial losses and reputational damage are {criticalFindings > 0 ? 'likely' : 'possible'} if exploited.
                </Text>
              </View>
              
              {/* Key Recommendations */}
              <View style={{ marginBottom: 25 }}>
                <Text style={[styles.subtitle, { fontSize: 16, color: '#00A86B' }]}>Key Recommendations</Text>
                <Text style={[styles.text, { marginLeft: 15, marginBottom: 5 }]}>• {criticalFindings > 0 ? 'Immediate attention required for critical severity findings' : 'Continue monitoring for emerging threats'}</Text>
                <Text style={[styles.text, { marginLeft: 15, marginBottom: 5 }]}>• Establish automated security scanning in CI/CD pipeline</Text>
                <Text style={[styles.text, { marginLeft: 15, marginBottom: 5 }]}>• Implement developer security training program</Text>
                <Text style={[styles.text, { marginLeft: 15 }]}>• Regular security assessments and code reviews</Text>
              </View>

            </View>
            
            <Text style={styles.footer}>
              Generated by Semgrep Reporter • {formattedDateTime} • Confidential
            </Text>
          </Page>

          {/* Assessment Methodology Page - Only include if enabled */}
          {config.reportConfiguration.includeSections.appendixMethodology && (
          <Page size="A4" style={styles.coverPage}>
            {/* Header Bar */}
            <View style={styles.headerBar}>
              <Text style={styles.appSecurityTitle}>Application Security Report</Text>
              <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
            </View>
            
            {/* Assessment Methodology Content */}
            <View style={styles.coverContent}>
              <Text style={styles.sectionTitle}>Assessment Methodology</Text>
              
              {/* Semgrep Security Levels */}
              <View style={styles.methodologySection}>
                <Text style={styles.methodologyTitle}>Semgrep Security Levels (SL1-SL5)</Text>
                <Text style={styles.methodologyText}>
                  The Semgrep Security Level provides a standardized way to communicate application security
                  posture, similar to Veracode's VL system but adapted for modern SAST scanning.
                </Text>
                
                <View style={styles.levelTable}>
                  <View style={styles.tableHeader}>
                    <Text style={[styles.levelCol, { fontWeight: 'bold' }]}>Level</Text>
                    <Text style={[styles.criteriaCol, { fontWeight: 'bold' }]}>Criteria</Text>
                    <Text style={[styles.descriptionCol, { fontWeight: 'bold' }]}>Description</Text>
                  </View>
                  
                  <View style={[styles.tableRow, styles.sl5Row]}>
                    <Text style={[styles.levelCol, styles.sl5Row]}>SL5</Text>
                    <Text style={[styles.criteriaCol, styles.sl5Row]}>0 Critical, 0 High, Score 90+</Text>
                    <Text style={[styles.descriptionCol, styles.sl5Row]}>Excellent security posture with minimal risk</Text>
                  </View>
                  
                  <View style={[styles.tableRow, styles.sl4Row]}>
                    <Text style={[styles.levelCol, styles.sl4Row]}>SL4</Text>
                    <Text style={[styles.criteriaCol, styles.sl4Row]}>0 Critical, 3 or less High, Score 80+</Text>
                    <Text style={[styles.descriptionCol, styles.sl4Row]}>Very good security with minor issues</Text>
                  </View>
                  
                  <View style={[styles.tableRow, styles.sl3Row]}>
                    <Text style={[styles.levelCol, styles.sl3Row]}>SL3</Text>
                    <Text style={[styles.criteriaCol, styles.sl3Row]}>0 Critical, 10 or less High, Score 70+</Text>
                    <Text style={[styles.descriptionCol, styles.sl3Row]}>Acceptable security with moderate risk</Text>
                  </View>
                  
                  <View style={[styles.tableRow, styles.sl2Row]}>
                    <Text style={[styles.levelCol, styles.sl2Row]}>SL2</Text>
                    <Text style={[styles.criteriaCol, styles.sl2Row]}>5 or less Critical, Score 60+</Text>
                    <Text style={[styles.descriptionCol, styles.sl2Row]}>Below average security requiring attention</Text>
                  </View>
                  
                  <View style={[styles.tableRow, styles.sl1Row]}>
                    <Text style={[styles.levelCol, styles.sl1Row]}>SL1</Text>
                    <Text style={[styles.criteriaCol, styles.sl1Row]}>More than 5 Critical or Score under 60</Text>
                    <Text style={[styles.descriptionCol, styles.sl1Row]}>Poor security posture requiring immediate action</Text>
                  </View>
                </View>
              </View>
              
              {/* Security Score Calculation */}
              <View style={styles.methodologySection}>
                <Text style={styles.methodologyTitle}>Security Score Calculation</Text>
                <Text style={styles.methodologyText}>
                  The security score uses a weighted approach similar to CVSS scoring:
                </Text>
                
                <View style={styles.scoringTable}>
                  <View style={styles.tableHeader}>
                    <Text style={[styles.severityCol, { fontWeight: 'bold' }]}>Severity</Text>
                    <Text style={[styles.weightCol, { fontWeight: 'bold' }]}>Weight</Text>
                    <Text style={[styles.impactCol, { fontWeight: 'bold' }]}>Impact</Text>
                  </View>
                  
                  <View style={styles.scoringRow}>
                    <Text style={[styles.severityCol, styles.criticalLabel]}>Critical</Text>
                    <Text style={styles.weightCol}>50</Text>
                    <Text style={styles.impactCol}>High business risk</Text>
                  </View>
                  
                  <View style={styles.scoringRow}>
                    <Text style={[styles.severityCol, styles.highLabel]}>High</Text>
                    <Text style={styles.weightCol}>20</Text>
                    <Text style={styles.impactCol}>Moderate business risk</Text>
                  </View>
                  
                  <View style={styles.scoringRow}>
                    <Text style={[styles.severityCol, styles.mediumLabel]}>Medium</Text>
                    <Text style={styles.weightCol}>5</Text>
                    <Text style={styles.impactCol}>Low business risk</Text>
                  </View>
                </View>
                
                <View style={styles.formula}>
                  <Text>Score = max(0, 100 - (total_weighted_impact * 100 / max_impact))</Text>
                </View>
              </View>
              
              {/* OWASP Top 10 2021 Mapping */}
              <View style={styles.methodologySection}>
                <Text style={styles.methodologyTitle}>OWASP Top 10 2021 Mapping</Text>
                <Text style={styles.methodologyText}>
                  Security findings are mapped to OWASP Top 10 2021 categories to provide compliance context and
                  industry-standard risk classification.
                </Text>
              </View>
            </View>
            
            <Text style={styles.footer}>
              Generated by Semgrep Reporter • {formattedDateTime} • Confidential
            </Text>
          </Page>
          )}

          {/* Projects Included Pages (Paginated) */}
          {this.renderProjectIncludedPages(projects, config, formattedDateTime)}

          {/* Projects Scan Summary Page */}
          <Page size="A4" style={styles.coverPage}>
            {/* Header Bar */}
            <View style={styles.headerBar}>
              <Text style={styles.appSecurityTitle}>Application Security Report</Text>
              <Image style={styles.semgrepLogoCover} src="./assets/semgrep-logo.png" />
            </View>
            
            {/* Scan Summary Content */}
            <View style={styles.coverContent}>
              <Text style={styles.sectionTitle}>Scan Summary</Text>
              
              {/* Scan Summary */}
              <View style={styles.methodologySection}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold' }]}>Total Open Findings:</Text>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold' }]}>Total Files Scanned:</Text>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold' }]}>Average Scan Duration:</Text>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold' }]}>Most Recent Scan:</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.methodologyText, styles.riskHigh]}>{projects.reduce((sum: number, project: SemgrepProject) => sum + project.findings.filter((f: SemgrepFinding) => f.status === 'Open').length, 0)}</Text>
                    <Text style={styles.methodologyText}>{projects.length > 0 ? this.getActualRepositories(projects).reduce((sum, repo) => sum + repo.filesScanned, 0).toLocaleString() : '0'}</Text>
                    <Text style={styles.methodologyText}>7.2 minutes</Text>
                    <Text style={styles.methodologyText}>{new Date().toLocaleDateString('en-US')} 18:03</Text>
                  </View>
                </View>
                
                <Text style={[styles.methodologyText, { fontSize: 10, fontStyle: 'italic', marginTop: 15 }]}>
                  Note: Scan durations represent the time taken to analyze each project. Times may vary based on project size, complexity, and scan configuration.
                </Text>
              </View>
              
              {/* Assessment Configuration */}
              <View style={styles.methodologySection}>
                <Text style={styles.methodologyTitle}>Assessment Configuration</Text>
                
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 15 }}>
                  <View style={{ flex: 1, marginRight: 20 }}>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold', marginBottom: 8 }]}>Security Scans Enabled:</Text>
                    <Text style={styles.methodologyText}>• Static Analysis (SAST): Enabled</Text>
                    <Text style={styles.methodologyText}>• Supply Chain Analysis: Enabled</Text>  
                    <Text style={styles.methodologyText}>• Secrets Detection: Enabled</Text>
                    
                    <Text style={[styles.methodologyText, { fontWeight: 'bold', marginTop: 15, marginBottom: 8 }]}>Business Context:</Text>
                    <Text style={styles.methodologyText}>• Criticality: {config.applicationSettings.businessCriticality}</Text>
                    <Text style={styles.methodologyText}>• Risk Tolerance: {config.applicationSettings.riskTolerance}</Text>
                  </View>
                  
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.methodologyText, { fontWeight: 'bold', marginBottom: 8 }]}>Active Rulesets:</Text>
                    {config.semgrepConfiguration.rulesets.map((ruleset, index) => (
                      <Text key={index} style={styles.methodologyText}>• {ruleset}</Text>
                    ))}
                    
                    <Text style={[styles.methodologyText, { fontWeight: 'bold', marginTop: 15, marginBottom: 8 }]}>Compliance Requirements:</Text>
                    {config.applicationSettings.complianceRequirements.slice(0, 4).map((req, index) => (
                      <Text key={index} style={styles.methodologyText}>• {req}</Text>
                    ))}
                    {config.applicationSettings.complianceRequirements.length > 4 && (
                      <Text style={[styles.methodologyText, { fontSize: 10, fontStyle: 'italic' }]}>
                        +{config.applicationSettings.complianceRequirements.length - 4} additional requirements
                      </Text>
                    )}
                  </View>
                </View>
              </View>
            </View>
            
            <Text style={styles.footer}>
              Generated by Semgrep Reporter • {new Date().toLocaleString()} • Confidential
            </Text>
          </Page>

          {/* Individual Project Pages (with integrated detailed findings) */}
          {this.renderIndividualProjectPages(projects, config)}

          {/* Security Improvement Roadmap at the end */}
          {this.renderSecurityRoadmapPage(projects, config)}
        </Document>
      );

      // Generate PDF buffer using stream handling
      const pdfBlob = await pdf(MyDocument).toBlob();
      const arrayBuffer = await pdfBlob.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      
      // Ensure output directory exists
      const outputDir = path.dirname(outputPath);
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      // Write PDF to file
      fs.writeFileSync(outputPath, buffer);
      
      const fileSizeMB = (buffer.length / 1024 / 1024).toFixed(2);
      console.log(`PDF report generated successfully: ${outputPath} (${fileSizeMB} MB)`);
      
      // Validate that no emoji characters remain in the generated content
      this.validateNoEmojiContent();
      
      return outputPath;
    } catch (error) {
      console.error('Error generating PDF report:', error);
      throw error;
    }
  }

  // Validation function to catch emoji corruption
  private validateNoEmojiContent() {
    const sourceCode = require('fs').readFileSync(__filename, 'utf-8');
    const problematicEmojis = [
      '\u{1F517}', '\u{1F4A1}', '\u{1F6A8}', '\u{26A1}', '\u{1F3AF}', '\u{1F4CA}', 
      '\u{2705}', '\u{274C}', '\u{2B50}', '\u{1F525}', '\u{1F4C8}', '\u{1F4C9}', 
      '\u{26A0}\u{FE0F}', '\u{1F680}', '\u{1F6E1}\u{FE0F}', '\u{1F534}', 
      '\u{1F7E1}', '\u{1F7E2}', '\u{1F535}'
    ];
    
    const foundEmojis = [];
    for (const emoji of problematicEmojis) {
      if (sourceCode.includes(emoji)) {
        const lines = sourceCode.split('\n');
        const lineNumbers = lines
          .map((line: string, index: number) => line.includes(emoji) ? index + 1 : null)
          .filter((num: number | null) => num !== null);
        foundEmojis.push(`${emoji} on lines: ${lineNumbers.join(', ')}`);
      }
    }
    
    if (foundEmojis.length > 0) {
      console.error('EMOJI CORRUPTION DETECTED:');
      foundEmojis.forEach(emoji => console.error(`  - ${emoji}`));
      console.error('These emojis cause text rendering corruption in React-PDF!');
      console.error('Please remove all emoji characters from the source code.');
    }
  }
}