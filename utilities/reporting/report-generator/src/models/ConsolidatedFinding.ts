import { SemgrepFinding } from './SemgrepFinding';

export interface ConsolidatedFinding {
  ruleId: string;
  ruleName: string;
  count: number;
  severity: string;
  owaspCategory?: string;
  cweId?: string;
  cveId?: string;
  description: string;
  assistantRecommendation?: string;
  instances: SemgrepFinding[];
  projectId: string; // For dashboard linking
}