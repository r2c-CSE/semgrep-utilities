export interface SemgrepFinding {
  id: string;
  ruleId: string;
  ruleName: string;
  path: string;
  startLine: number;
  severity: string; // 'Critical', 'High', 'Medium', 'Low'
  message: string;
  description: string;
  category: string;
  foundAt: Date;
  status: string; // 'Open', 'Fixed', 'Ignored'
  owaspCategory?: string;
  cweId?: string;
  cveId?: string;
  exploitabilityScore: number; // 1-5 scale
  remediationEffort: number; // 1-5 scale
  
  // Project association
  projectName: string;
  projectId: string;
  
  // AI Assistant recommendations
  assistantRecommendation?: string;
  triageState?: string; // 'reviewed', 'needs_review', etc.
}

export interface SemgrepProject {
  name: string;
  repository: string;
  projectId?: string;
  repoRefId?: string; // Optional repo_ref for dashboard links
  businessCriticality: BusinessCriticality;
  lastScanned: Date;
  findings: SemgrepFinding[];
  scanData: ScanMetadata;
}

export interface ScanMetadata {
  sastCompleted: boolean;
  supplyChainCompleted: boolean;
  secretsCompleted: boolean;
  filesScanned: number;
  scanDuration: number; // Duration in milliseconds
  engineVersion: string;
}

export enum BusinessCriticality {
  VeryLow = 1,    // BC1
  Low = 2,        // BC2  
  Medium = 3,     // BC3
  High = 4,       // BC4
  VeryHigh = 5    // BC5
}

export enum SemgrepLevel {
  SL1 = 1,  // Basic scan completion
  SL2 = 2,  // ≤5 Critical findings + score ≥60
  SL3 = 3,  // 0 Critical, ≤10 High + score ≥70 (Enterprise Ready)
  SL4 = 4,  // 0 Critical, ≤3 High + score ≥80
  SL5 = 5   // 0 Critical, 0 High + score ≥90 (Veracode VL compliant)
}

export type SeverityLevel = 'Critical' | 'High' | 'Medium' | 'Low';
export type FindingStatus = 'Open' | 'Fixed' | 'Ignored';
export type ReportType = 'brief' | 'standard';