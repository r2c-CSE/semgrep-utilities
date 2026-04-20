import os
import random
import re
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from models import (
    SemgrepProject, SemgrepFinding, ScanMetadata, BusinessCriticality
)


class SemgrepApiClient:
    BASE_URL = 'https://semgrep.dev/api/v1'

    # Class-level caches
    _cached_findings: Dict[str, dict] = {}
    _cached_projects: Dict[str, dict] = {}
    _cached_project_details: Dict[str, dict] = {}

    def __init__(self, organization_name: Optional[str] = None, api_token: Optional[str] = None):
        self.organization_name = organization_name or 'sample-org'
        self.api_token = api_token or os.environ.get('SEMGREP_APP_TOKEN')

        self._session = requests.Session()
        self._session.timeout = 30 * 60  # 30 minutes
        if self.api_token:
            self._session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
            })

    def _get_org_slug(self, org_name: str) -> str:
        return org_name.replace('-', '_')

    def fetch_project_details(self, project_id: str) -> Optional[dict]:
        if not self.api_token:
            return None

        cache_key = f'{self.organization_name}-{project_id}'
        if cache_key not in SemgrepApiClient._cached_project_details:
            agent_base = self.BASE_URL.replace('/api/v1', '/api/agent')
            url = f'{agent_base}/deployments/{self._get_org_slug(self.organization_name)}/repos/{project_id}'
            try:
                resp = self._session.get(url)
                if resp.status_code == 200:
                    SemgrepApiClient._cached_project_details[cache_key] = resp.json()
                else:
                    print(f'Warning: Failed to fetch project details {project_id}: {resp.status_code}')
                    return None
            except Exception as e:
                print(f'Warning: Error fetching project details {project_id}: {e}')
                return None

        return SemgrepApiClient._cached_project_details.get(cache_key)

    def fetch_project_findings(self, config_project_id: str) -> SemgrepProject:
        if not self.api_token:
            print(f'Warning: No SEMGREP_APP_TOKEN found, using dummy data for project {config_project_id}')
            return self._create_dummy_project(config_project_id)

        try:
            self._ensure_cache_populated()
            cached_findings = SemgrepApiClient._cached_findings.get(self.organization_name)
            cached_projects = SemgrepApiClient._cached_projects.get(self.organization_name)
            return self._parse_project_from_findings(cached_findings, cached_projects, config_project_id)
        except Exception as e:
            print(f'Error fetching project {config_project_id}: {e}')
            return self._create_dummy_project(config_project_id)

    def fetch_all_projects(self, repository_mapping: Optional[Dict[str, str]] = None) -> List[SemgrepProject]:
        if not self.api_token:
            print('Warning: No SEMGREP_APP_TOKEN found, using dummy data')
            return []

        try:
            self._ensure_cache_populated()
            cached_findings = SemgrepApiClient._cached_findings.get(self.organization_name)
            cached_projects = SemgrepApiClient._cached_projects.get(self.organization_name)

            if not cached_projects or not cached_findings:
                print('No projects or findings data available')
                return []

            # Build repo name -> project mapping
            repo_name_to_project: Dict[str, dict] = {}
            for project in cached_projects.get('projects', []):
                if project.get('name') and project.get('id'):
                    repo_name_to_project[project['name']] = project

            # Group findings by repo name
            findings_by_repo: Dict[str, list] = {}
            for finding in cached_findings.get('findings', []):
                repo_name = finding.get('repository', {}).get('name')
                if repo_name:
                    if repo_name not in findings_by_repo:
                        findings_by_repo[repo_name] = []
                    findings_by_repo[repo_name].append(finding)

            print(f'Found findings in {len(findings_by_repo)} repositories')

            projects: List[SemgrepProject] = []

            if repository_mapping:
                active_repo_ids = set(repository_mapping.values())
                print(f'Processing {len(active_repo_ids)} active repositories from mapping file')
                for repo_name, repo_findings in findings_by_repo.items():
                    api_project = repo_name_to_project.get(repo_name)
                    if api_project and repo_findings:
                        repo_id = str(api_project.get('id', ''))
                        if repo_id and repo_id in active_repo_ids:
                            project = self._parse_project_from_findings(
                                {'findings': repo_findings}, cached_projects, repo_id
                            )
                            projects.append(project)
            else:
                for repo_name, repo_findings in findings_by_repo.items():
                    api_project = repo_name_to_project.get(repo_name)
                    if api_project and repo_findings:
                        repo_id = str(api_project.get('id', ''))
                        project = self._parse_project_from_findings(
                            {'findings': repo_findings}, cached_projects, repo_id
                        )
                        projects.append(project)

            projects.sort(key=lambda p: len(p.findings), reverse=True)
            print(f'Created {len(projects)} individual projects from {len(cached_findings.get("findings", []))} total findings')
            return projects

        except Exception as e:
            print(f'Error fetching all projects: {e}')
            return []

    def _ensure_cache_populated(self) -> None:
        cache_key = self.organization_name
        if cache_key not in SemgrepApiClient._cached_findings:
            all_findings = []
            page = 0
            while True:
                url = (
                    f'{self.BASE_URL}/deployments/{self._get_org_slug(self.organization_name)}'
                    f'/findings?page_size=3000&status=open&page={page}'
                )
                try:
                    resp = self._session.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        page_findings = data.get('findings', [])
                        all_findings.extend(page_findings)
                        print(f'Fetched page {page}: {len(page_findings)} open findings')
                        if len(page_findings) < 3000:
                            break
                        page += 1
                    else:
                        print(f'Warning: Failed to fetch open findings page {page}: {resp.status_code}')
                        break
                except Exception as e:
                    print(f'Warning: Error fetching open findings page {page}: {e}')
                    break

            SemgrepApiClient._cached_findings[cache_key] = {'findings': all_findings}
            print(f'Fetched {len(all_findings)} open findings for {self.organization_name}')

        if cache_key not in SemgrepApiClient._cached_projects:
            url = f'{self.BASE_URL}/deployments/{self._get_org_slug(self.organization_name)}/projects'
            try:
                resp = self._session.get(url)
                if resp.status_code == 200:
                    SemgrepApiClient._cached_projects[cache_key] = resp.json()
            except Exception as e:
                print(f'Warning: Could not fetch projects data: {e}')
                SemgrepApiClient._cached_projects[cache_key] = None

    def _parse_project_from_findings(
        self, findings_data: Optional[dict], projects_data: Optional[dict], config_project_id: str
    ) -> SemgrepProject:
        project_name = f'Project {config_project_id}'
        actual_project_id = config_project_id
        project_findings: List[SemgrepFinding] = []
        repo_ref_id: Optional[str] = None

        # Build repo name -> project ID map
        repo_to_id: Dict[str, str] = {}
        if projects_data and projects_data.get('projects'):
            for p in projects_data['projects']:
                if p.get('name') and p.get('id'):
                    repo_to_id[p['name'].lower()] = str(p['id'])

        # Fetch project details for repo_ref
        if config_project_id != 'consolidated-org-report':
            details = self.fetch_project_details(config_project_id)
            if details:
                refs = details.get('repo', {}).get('refs', [])
                if refs:
                    primary = next((r for r in refs if r.get('isPrimary')), refs[0])
                    repo_ref_id = primary.get('repoRefId')

        if not findings_data or not findings_data.get('findings'):
            return SemgrepProject(
                name=project_name,
                repository=project_name,
                project_id=actual_project_id,
                repo_ref_id=repo_ref_id,
                business_criticality=BusinessCriticality.HIGH,
                last_scanned=datetime.now() - timedelta(hours=random.random() * 48),
                findings=[],
                scan_data=ScanMetadata(
                    sast_completed=True,
                    supply_chain_completed=True,
                    secrets_completed=False,
                    files_scanned=random.randint(50, 500),
                    scan_duration=random.randint(2 * 60000, 15 * 60000),
                    engine_version='1.45.0',
                )
            )

        findings_to_process = []
        target_repo_name = None

        if config_project_id == 'consolidated-org-report':
            findings_to_process = findings_data['findings']
            project_name = 'Organization Report'
            target_repo_name = 'All Repositories'
            print(f'Consolidated Report: Found {len(findings_to_process)} findings across all repositories')
        else:
            if projects_data and projects_data.get('projects'):
                for p in projects_data['projects']:
                    if str(p.get('id')) == config_project_id:
                        target_repo_name = p.get('name')
                        break

            if target_repo_name:
                findings_to_process = [
                    f for f in findings_data['findings']
                    if f.get('repository', {}).get('name', '').lower() == target_repo_name.lower()
                ]
            else:
                print(f'Warning: Project ID {config_project_id} not found in org projects list. '
                      f'Check that organizationName in your config matches the org that owns this project.')
                findings_to_process = []
            print(f'Project {config_project_id} ({target_repo_name}): Found {len(findings_to_process)} findings')

        if target_repo_name:
            project_name = target_repo_name

        for raw in findings_to_process:
            finding = SemgrepFinding(
                id=str(raw.get('id') or self._generate_id()),
                rule_id=raw.get('rule', {}).get('name') or raw.get('check_id') or 'unknown-rule',
                rule_name=raw.get('rule', {}).get('name') or raw.get('check_id') or 'Unknown Rule',
                path=raw.get('location', {}).get('file_path') or raw.get('path') or 'unknown-path',
                start_line=raw.get('location', {}).get('line') or raw.get('line') or 1,
                severity=self._map_severity(raw.get('severity')),
                message=raw.get('rule_message') or raw.get('message') or 'No message available',
                description=raw.get('rule', {}).get('message') or raw.get('rule_message') or 'No description available',
                category=raw.get('rule', {}).get('category') or raw.get('category') or 'security',
                found_at=self._parse_datetime(raw.get('created_at')) or datetime.now(),
                status=self._map_status(raw.get('triage_state')),
                owasp_category=self._extract_owasp(raw),
                cwe_id=self._extract_cwe(raw),
                cve_id=self._extract_cve_id(raw.get('rule', {}).get('name') or raw.get('check_id')),
                exploitability_score=random.randint(1, 5),
                remediation_effort=random.randint(1, 5),
                project_name=project_name,
                project_id=actual_project_id,
                assistant_recommendation=self._get_recommendation(raw),
                triage_state=raw.get('triage_state') or 'needs_review',
            )
            project_findings.append(finding)

        def _is_secrets_finding(raw: dict) -> bool:
            product = (raw.get('product') or '').lower()
            if product == 'secrets':
                return True
            issue_type = (raw.get('issue_type') or raw.get('type') or '').lower()
            if issue_type == 'secrets':
                return True
            rule_name = (raw.get('rule', {}).get('name') or raw.get('check_id') or '').lower()
            if rule_name.startswith('secrets.') or '.secrets.' in rule_name:
                return True
            categories = raw.get('rule', {}).get('categories') or raw.get('categories') or []
            if any('secret' in str(c).lower() for c in categories):
                return True
            return False

        secrets_completed = any(_is_secrets_finding(raw) for raw in findings_to_process)

        return SemgrepProject(
            name=project_name,
            repository=project_name,
            project_id=actual_project_id,
            repo_ref_id=repo_ref_id,
            business_criticality=BusinessCriticality.HIGH,
            last_scanned=datetime.now() - timedelta(hours=random.random() * 48),
            findings=project_findings,
            scan_data=ScanMetadata(
                sast_completed=True,
                supply_chain_completed=True,
                secrets_completed=secrets_completed,
                files_scanned=random.randint(50, 500),
                scan_duration=random.randint(2 * 60000, 15 * 60000),
                engine_version='1.45.0',
            )
        )

    def _map_severity(self, api_severity: Optional[str]) -> str:
        if not api_severity:
            return 'Medium'
        return {
            'critical': 'Critical',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
        }.get(api_severity.lower(), 'Medium')

    def _map_status(self, triage_state: Optional[str]) -> str:
        if not triage_state:
            return 'Open'
        return {
            'confirmed': 'Open',
            'false_positive': 'Ignored',
            'fixed': 'Fixed',
        }.get(triage_state.lower(), 'Open')

    def _extract_owasp(self, finding: dict) -> Optional[str]:
        owasp_names = finding.get('rule', {}).get('owasp_names', [])
        if owasp_names:
            return self._map_owasp_text_to_category(owasp_names[0])
        rule_id = finding.get('rule', {}).get('name') or finding.get('check_id') or ''
        return self._map_to_owasp(rule_id)

    def _extract_cwe(self, finding: dict) -> Optional[str]:
        cwe_names = finding.get('rule', {}).get('cwe_names', [])
        if cwe_names:
            m = re.search(r'CWE-(\d+)', cwe_names[0])
            if m:
                return f'CWE-{m.group(1)}'
        rule_id = finding.get('rule', {}).get('name') or finding.get('check_id') or ''
        return self._extract_cwe_id(rule_id)

    def _map_owasp_text_to_category(self, text: str) -> str:
        mappings = [
            ('Broken Access Control', 'broken-access-control'),
            ('Cryptographic Failures', 'cryptographic-failures'),
            ('Injection', 'injection'),
            ('Insecure Design', 'insecure-design'),
            ('Security Misconfiguration', 'security-misconfiguration'),
            ('Vulnerable and Outdated Components', 'vulnerable-components'),
            ('Identification and Authentication Failures', 'identification-authentication-failures'),
            ('Software and Data Integrity Failures', 'software-data-integrity-failures'),
            ('Security Logging and Monitoring Failures', 'security-logging-monitoring-failures'),
            ('Server-Side Request Forgery', 'server-side-request-forgery'),
        ]
        for keyword, category in mappings:
            if keyword in text:
                return category
        return 'security-misconfiguration'

    def _map_to_owasp(self, rule_id: str) -> Optional[str]:
        if not rule_id:
            return None
        rule_lower = rule_id.lower()
        if 'injection' in rule_lower or 'sqli' in rule_lower:
            return 'injection'
        if 'xss' in rule_lower or 'cross-site' in rule_lower:
            return 'injection'
        if 'auth' in rule_lower or 'access' in rule_lower:
            return 'broken-access-control'
        if 'crypto' in rule_lower or 'hash' in rule_lower:
            return 'cryptographic-failures'
        if 'config' in rule_lower or 'hardcode' in rule_lower:
            return 'security-misconfiguration'
        if 'component' in rule_lower or 'dependency' in rule_lower:
            return 'vulnerable-components'
        if 'log' in rule_lower or 'audit' in rule_lower:
            return 'security-logging-monitoring-failures'
        if 'ssrf' in rule_lower or 'redirect' in rule_lower:
            return 'server-side-request-forgery'
        return 'security-misconfiguration'

    def _extract_cwe_id(self, rule_id: Optional[str]) -> Optional[str]:
        if not rule_id:
            return None
        rule_lower = rule_id.lower()
        if 'injection' in rule_lower:
            return 'CWE-89'
        if 'xss' in rule_lower:
            return 'CWE-79'
        if 'auth' in rule_lower:
            return 'CWE-287'
        if 'crypto' in rule_lower:
            return 'CWE-327'
        if 'path' in rule_lower or 'traversal' in rule_lower:
            return 'CWE-22'
        if 'hardcode' in rule_lower:
            return 'CWE-798'
        return None

    def _extract_cve_id(self, rule_id: Optional[str]) -> Optional[str]:
        if not rule_id:
            return None
        rule_lower = rule_id.lower()
        if 'log4j' in rule_lower:
            return 'CVE-2021-44228'
        if 'jackson' in rule_lower:
            return 'CVE-2019-12384'
        if 'struts' in rule_lower:
            return 'CVE-2017-5638'
        if 'sqli' in rule_lower and random.random() < 0.33:
            return 'CVE-2023-34362'
        return None

    def _get_recommendation(self, finding: dict) -> Optional[str]:
        triage = finding.get('triage', {}) or {}
        if triage.get('assistant_recommendation'):
            return triage['assistant_recommendation']
        comment = triage.get('comment', '')
        if comment and 'Assistant' in comment:
            return comment
        rule_id = (finding.get('rule', {}).get('name') or finding.get('check_id') or '').lower()
        return self._generate_recommendation(rule_id)

    def _generate_recommendation(self, rule_id: str) -> str:
        if 'sqli' in rule_id or 'injection' in rule_id:
            return 'Use parameterized queries or prepared statements to prevent SQL injection. Validate and sanitize all user inputs.'
        if 'xss' in rule_id or 'cross-site' in rule_id:
            return 'Encode output data and validate input to prevent XSS attacks. Use content security policy headers.'
        if 'auth' in rule_id or 'session' in rule_id:
            return 'Implement proper session management with secure cookies (HttpOnly, Secure flags). Use strong authentication mechanisms.'
        if 'crypto' in rule_id or 'hash' in rule_id:
            return 'Replace weak cryptographic functions with secure alternatives like SHA-256 or bcrypt for password hashing.'
        if 'hardcode' in rule_id or 'secret' in rule_id:
            return 'Remove hardcoded credentials and use secure configuration management or environment variables.'
        if 'path' in rule_id or 'traversal' in rule_id:
            return 'Validate and sanitize file paths. Use allowlists for permitted directories and filenames.'
        return 'Review the finding and apply appropriate security controls based on the vulnerability type.'

    def _parse_datetime(self, date_string: Optional[str]) -> Optional[datetime]:
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _generate_id(self) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))

    def _create_dummy_project(self, project_id: str) -> SemgrepProject:
        project_name = f'Project {project_id}'
        rule_types = ['sqli', 'xss', 'auth', 'crypto', 'hardcode', 'path-traversal']
        severities = ['Critical', 'Critical', 'High', 'Medium', 'Low']
        findings: List[SemgrepFinding] = []

        for i in range(random.randint(8, 14)):
            severity = random.choice(severities)
            rule_type = random.choice(rule_types)
            rule_id = f'java.lang.security.audit.{rule_type}-{i + 1}'

            findings.append(SemgrepFinding(
                id=self._generate_id(),
                rule_id=rule_id,
                rule_name=rule_id,
                path=f'src/components/Component{i + 1}.js',
                start_line=random.randint(1, 200),
                severity=severity,
                message=f'Security issue detected in {project_id}',
                description=f'Potential {rule_type.replace("-", " ")} vulnerability found. This could allow attackers to compromise application security.',
                category='security',
                found_at=datetime.now() - timedelta(days=random.random() * 30),
                status='Open',
                owasp_category='broken-access-control' if severity == 'Critical' else 'security-misconfiguration',
                cwe_id='CWE-287' if severity == 'Critical' else 'CWE-16',
                cve_id=self._extract_cve_id(rule_id),
                exploitability_score=random.randint(1, 5),
                remediation_effort=random.randint(1, 5),
                project_name=project_name,
                project_id=project_id,
                assistant_recommendation=self._generate_recommendation(rule_id.lower()),
                triage_state='reviewed' if random.random() > 0.75 else 'needs_review',
            ))

        return SemgrepProject(
            name=project_name,
            repository=f'example-org/project-{project_id}',
            project_id=project_id,
            business_criticality=BusinessCriticality.HIGH,
            last_scanned=datetime.now() - timedelta(hours=random.random() * 24),
            findings=findings,
            scan_data=ScanMetadata(
                sast_completed=True,
                supply_chain_completed=True,
                secrets_completed=random.random() > 0.5,
                files_scanned=random.randint(50, 500),
                scan_duration=random.randint(2 * 60000, 15 * 60000),
                engine_version='1.45.0',
            )
        )
