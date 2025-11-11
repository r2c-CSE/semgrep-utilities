import { SemgrepProject, SemgrepFinding, SemgrepLevel, BusinessCriticality } from '../models';

export class ScoringEngine {
  public calculateSemgrepLevel(project: SemgrepProject): SemgrepLevel {
    const findings = project.findings;
    const criticalCount = findings.filter(f => f.severity === 'Critical' && f.status === 'Open').length;
    const highCount = findings.filter(f => f.severity === 'High' && f.status === 'Open').length;
    const score = this.calculateSecurityScore(findings);

    // Semgrep Level calculation based on Veracode VL system
    if (criticalCount === 0 && highCount === 0 && score >= 90) {
      return SemgrepLevel.SL5;
    }
    
    if (criticalCount === 0 && highCount <= 3 && score >= 80) {
      return SemgrepLevel.SL4;
    }
      
    if (criticalCount === 0 && highCount <= 10 && score >= 70) {
      return SemgrepLevel.SL3;
    }
      
    if (criticalCount <= 5 && score >= 60) {
      return SemgrepLevel.SL2;
    }
      
    return SemgrepLevel.SL1;
  }

  public calculateSecurityScore(findings: SemgrepFinding[]): number {
    if (findings.length === 0) return 100;

    const openFindings = findings.filter(f => f.status === 'Open');
    if (openFindings.length === 0) return 100;

    // Weight findings by severity (similar to CVSS-based approach)
    const criticalWeight = 50;
    const highWeight = 20;
    const mediumWeight = 5;
    const lowWeight = 1;

    let totalImpact = 0;
    for (const finding of openFindings) {
      const weight = this.getSeverityWeight(finding.severity, criticalWeight, highWeight, mediumWeight, lowWeight);
      totalImpact += weight;
    }

    // Normalize to 0-100 scale (diminishing returns for many findings)
    const maxImpact = 1000; // Adjust based on typical finding volumes
    const rawScore = Math.max(0, 100 - (totalImpact * 100.0 / maxImpact));
    
    return Math.round(rawScore);
  }

  private getSeverityWeight(severity: string, criticalWeight: number, highWeight: number, mediumWeight: number, lowWeight: number): number {
    switch (severity) {
      case 'Critical': return criticalWeight;
      case 'High': return highWeight;
      case 'Medium': return mediumWeight;
      case 'Low': return lowWeight;
      default: return lowWeight;
    }
  }

  public getOwaspTop10Distribution(findings: SemgrepFinding[]): Record<string, number> {
    const owaspMap: Record<string, string> = {
      'broken-access-control': 'OWASP Top Ten 2021 Category A01 - Broken Access Control',
      'cryptographic-failures': 'OWASP Top Ten 2021 Category A02 - Cryptographic Failures',
      'injection': 'OWASP Top Ten 2021 Category A03 - Injection',
      'insecure-design': 'OWASP Top Ten 2021 Category A04 - Insecure Design',
      'security-misconfiguration': 'OWASP Top Ten 2021 Category A05 - Security Misconfiguration',
      'vulnerable-outdated-components': 'OWASP Top Ten 2021 Category A06 - Vulnerable and Outdated Components',
      'identification-authentication-failures': 'OWASP Top Ten 2021 Category A07 - Identification and Authentication Failures',
      'software-data-integrity-failures': 'OWASP Top Ten 2021 Category A08 - Software and Data Integrity Failures',
      'security-logging-monitoring-failures': 'OWASP Top Ten 2021 Category A09 - Security Logging and Monitoring Failures',
      'server-side-request-forgery': 'OWASP Top Ten 2021 Category A10 - Server-Side Request Forgery (SSRF)'
    };

    const distribution: Record<string, number> = {};
    
    for (const finding of findings.filter(f => f.status === 'Open')) {
      const category = this.mapFindingToOwaspCategory(finding);
      if (category && Object.values(owaspMap).includes(category)) {
        distribution[category] = (distribution[category] || 0) + 1;
      }
    }

    return distribution;
  }

  private mapFindingToOwaspCategory(finding: SemgrepFinding): string | undefined {
    // Map Semgrep rule categories to OWASP Top 10 2021
    const categoryLower = finding.category.toLowerCase();
    const ruleLower = finding.ruleId.toLowerCase();

    // A01 - Broken Access Control (now #1 priority)
    if (categoryLower.includes('access') || categoryLower.includes('authorization') || ruleLower.includes('authz')) {
      return 'OWASP Top Ten 2021 Category A01 - Broken Access Control';
    }
      
    // A02 - Cryptographic Failures (was Sensitive Data Exposure)
    if (categoryLower.includes('crypto') || ruleLower.includes('hash') || categoryLower.includes('secret') || 
        ruleLower.includes('weak') || categoryLower.includes('encryption')) {
      return 'OWASP Top Ten 2021 Category A02 - Cryptographic Failures';
    }
      
    // A03 - Injection (dropped from #1 to #3)
    if (categoryLower.includes('injection') || ruleLower.includes('sql') || ruleLower.includes('command') ||
        categoryLower.includes('xss') || ruleLower.includes('cross-site')) {
      return 'OWASP Top Ten 2021 Category A03 - Injection';
    }
      
    // A04 - Insecure Design (new category)
    if (categoryLower.includes('design') || categoryLower.includes('architecture')) {
      return 'OWASP Top Ten 2021 Category A04 - Insecure Design';
    }
      
    // A05 - Security Misconfiguration
    if (categoryLower.includes('config') || ruleLower.includes('default') || categoryLower.includes('misconfiguration')) {
      return 'OWASP Top Ten 2021 Category A05 - Security Misconfiguration';
    }
      
    // A06 - Vulnerable and Outdated Components
    if (categoryLower.includes('component') || categoryLower.includes('dependency') || categoryLower.includes('vulnerable')) {
      return 'OWASP Top Ten 2021 Category A06 - Vulnerable and Outdated Components';
    }
      
    // A07 - Identification and Authentication Failures (was Broken Authentication)
    if (categoryLower.includes('auth') || ruleLower.includes('session') || categoryLower.includes('authentication')) {
      return 'OWASP Top Ten 2021 Category A07 - Identification and Authentication Failures';
    }
      
    // A08 - Software and Data Integrity Failures (new category)
    if (categoryLower.includes('integrity') || categoryLower.includes('deserialization') || categoryLower.includes('pipeline')) {
      return 'OWASP Top Ten 2021 Category A08 - Software and Data Integrity Failures';
    }
      
    // A09 - Security Logging and Monitoring Failures
    if (categoryLower.includes('logging') || categoryLower.includes('monitoring') || categoryLower.includes('audit')) {
      return 'OWASP Top Ten 2021 Category A09 - Security Logging and Monitoring Failures';
    }
      
    // A10 - Server-Side Request Forgery (new category)
    if (categoryLower.includes('ssrf') || ruleLower.includes('request-forgery') || categoryLower.includes('server-side')) {
      return 'OWASP Top Ten 2021 Category A10 - Server-Side Request Forgery (SSRF)';
    }

    return undefined;
  }

  public getBusinessCriticalityDescription(criticality: BusinessCriticality): string {
    switch (criticality) {
      case BusinessCriticality.VeryHigh:
        return 'Mission critical for business/safety of life and limb on the line';
      case BusinessCriticality.High:
        return 'Exploitation causes serious brand damage and financial loss with long term business impact';
      case BusinessCriticality.Medium:
        return 'Applications connected to the internet that process financial or private customer information';
      case BusinessCriticality.Low:
        return 'Typically internal applications with non-critical business impact';
      case BusinessCriticality.VeryLow:
        return 'Applications with no material business impact';
      default:
        return 'Not specified';
    }
  }
}