from typing import Dict, List, Optional

from models import SemgrepProject, SemgrepFinding, SemgrepLevel, BusinessCriticality


class ScoringEngine:
    def calculate_semgrep_level(self, project: SemgrepProject) -> SemgrepLevel:
        findings = project.findings
        critical_count = sum(1 for f in findings if f.severity == 'Critical' and f.status == 'Open')
        high_count = sum(1 for f in findings if f.severity == 'High' and f.status == 'Open')
        score = self.calculate_security_score(findings)

        if critical_count == 0 and high_count == 0 and score >= 90:
            return SemgrepLevel.SL5
        if critical_count == 0 and high_count <= 3 and score >= 80:
            return SemgrepLevel.SL4
        if critical_count == 0 and high_count <= 10 and score >= 70:
            return SemgrepLevel.SL3
        if critical_count <= 5 and score >= 60:
            return SemgrepLevel.SL2
        return SemgrepLevel.SL1

    def calculate_security_score(self, findings: List[SemgrepFinding]) -> int:
        if not findings:
            return 100

        open_findings = [f for f in findings if f.status == 'Open']
        if not open_findings:
            return 100

        critical_weight = 50
        high_weight = 20
        medium_weight = 5
        low_weight = 1

        total_impact = 0
        for finding in open_findings:
            weight = self._get_severity_weight(
                finding.severity, critical_weight, high_weight, medium_weight, low_weight
            )
            total_impact += weight

        max_impact = 1000
        raw_score = max(0, 100 - (total_impact * 100.0 / max_impact))
        return round(raw_score)

    def _get_severity_weight(
        self, severity: str,
        critical_weight: int, high_weight: int,
        medium_weight: int, low_weight: int
    ) -> int:
        weights = {
            'Critical': critical_weight,
            'High': high_weight,
            'Medium': medium_weight,
            'Low': low_weight,
        }
        return weights.get(severity, low_weight)

    def get_owasp_top10_distribution(self, findings: List[SemgrepFinding]) -> Dict[str, int]:
        distribution: Dict[str, int] = {}
        for finding in findings:
            if finding.status != 'Open':
                continue
            category = self._map_finding_to_owasp_category(finding)
            if category:
                distribution[category] = distribution.get(category, 0) + 1
        return distribution

    def _map_finding_to_owasp_category(self, finding: SemgrepFinding) -> Optional[str]:
        category_lower = finding.category.lower()
        rule_lower = finding.rule_id.lower()

        if 'access' in category_lower or 'authorization' in category_lower or 'authz' in rule_lower:
            return 'OWASP Top Ten 2021 Category A01 - Broken Access Control'
        if 'crypto' in category_lower or 'hash' in rule_lower or 'secret' in category_lower or \
                'weak' in rule_lower or 'encryption' in category_lower:
            return 'OWASP Top Ten 2021 Category A02 - Cryptographic Failures'
        if 'injection' in category_lower or 'sql' in rule_lower or 'command' in rule_lower or \
                'xss' in category_lower or 'cross-site' in rule_lower:
            return 'OWASP Top Ten 2021 Category A03 - Injection'
        if 'design' in category_lower or 'architecture' in category_lower:
            return 'OWASP Top Ten 2021 Category A04 - Insecure Design'
        if 'config' in category_lower or 'default' in rule_lower or 'misconfiguration' in category_lower:
            return 'OWASP Top Ten 2021 Category A05 - Security Misconfiguration'
        if 'component' in category_lower or 'dependency' in category_lower or 'vulnerable' in category_lower:
            return 'OWASP Top Ten 2021 Category A06 - Vulnerable and Outdated Components'
        if 'auth' in category_lower or 'session' in rule_lower or 'authentication' in category_lower:
            return 'OWASP Top Ten 2021 Category A07 - Identification and Authentication Failures'
        if 'integrity' in category_lower or 'deserialization' in category_lower or 'pipeline' in category_lower:
            return 'OWASP Top Ten 2021 Category A08 - Software and Data Integrity Failures'
        if 'logging' in category_lower or 'monitoring' in category_lower or 'audit' in category_lower:
            return 'OWASP Top Ten 2021 Category A09 - Security Logging and Monitoring Failures'
        if 'ssrf' in category_lower or 'request-forgery' in rule_lower or 'server-side' in category_lower:
            return 'OWASP Top Ten 2021 Category A10 - Server-Side Request Forgery (SSRF)'
        return None

    def get_business_criticality_description(self, criticality: BusinessCriticality) -> str:
        descriptions = {
            BusinessCriticality.VERY_HIGH: 'Mission critical for business/safety of life and limb on the line',
            BusinessCriticality.HIGH: 'Exploitation causes serious brand damage and financial loss with long term business impact',
            BusinessCriticality.MEDIUM: 'Applications connected to the internet that process financial or private customer information',
            BusinessCriticality.LOW: 'Typically internal applications with non-critical business impact',
            BusinessCriticality.VERY_LOW: 'Applications with no material business impact',
        }
        return descriptions.get(criticality, 'Not specified')
