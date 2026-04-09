from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class CustomerInfo:
    name: str
    industry: str
    reporting_contact: str


@dataclass
class ProjectSettings:
    semgrep_project_id: str
    include: bool
    name: Optional[str] = None
    repository: Optional[str] = None


@dataclass
class ApplicationSettings:
    business_criticality: str
    compliance_requirements: List[str]
    risk_tolerance: str


@dataclass
class IncludeSections:
    executive_summary: bool = True
    security_scorecard: bool = True
    owasp_mapping: bool = True
    findings_details: bool = True
    remediation_roadmap: bool = True
    compliance_matrix: bool = False
    appendix_methodology: bool = False


@dataclass
class SeverityThresholds:
    blocking_findings: List[str] = field(default_factory=lambda: ['Critical'])
    expedited_findings: List[str] = field(default_factory=lambda: ['Critical', 'High'])
    scheduled_findings: List[str] = field(default_factory=lambda: ['Medium', 'Low'])


@dataclass
class BrandingSettings:
    company_logo: str = './assets/semgrep.svg'
    primary_color: str = '#2dcda7'
    accent_color: str = '#deede8'


@dataclass
class RepositoryReferenceMapping:
    method: str = 'static'
    static_mappings: Dict[str, str] = field(default_factory=dict)
    external_mapping_file: Optional[str] = None


@dataclass
class ReportConfigSettings:
    include_sections: IncludeSections
    severity_thresholds: SeverityThresholds
    branding: BrandingSettings
    output_formats: List[str] = field(default_factory=lambda: ['PDF'])
    detail_filter_min_severity: str = 'Medium'
    findings_detail_level: str = 'standard'
    include_dashboard_links: bool = True
    repository_reference_mapping: Optional[RepositoryReferenceMapping] = None


@dataclass
class RequiredScans:
    sast: bool = True
    supply_chain: bool = True
    secrets: bool = True


@dataclass
class SemgrepConfiguration:
    required_scans: RequiredScans
    rulesets: List[str] = field(default_factory=list)
    minimum_semgrep_level: str = 'SL3'


@dataclass
class EmailReporting:
    enabled: bool = False
    recipients: List[str] = field(default_factory=list)
    frequency: str = 'weekly'


@dataclass
class IntegrationSettings:
    jira_ticket_creation: bool = False
    slack_notifications: bool = False
    email_reporting: EmailReporting = field(default_factory=EmailReporting)


@dataclass
class OrganizationSettings:
    organization_name: str
    api_token: str = ''


@dataclass
class ReportConfiguration:
    customer: CustomerInfo
    projects: List[ProjectSettings]
    application_settings: ApplicationSettings
    report_configuration: ReportConfigSettings
    semgrep_configuration: SemgrepConfiguration
    integration_settings: IntegrationSettings
    organization_settings: Optional[OrganizationSettings] = None
