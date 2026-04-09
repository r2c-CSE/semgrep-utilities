import json
import os
from typing import Dict, List, Optional

from models import (
    ReportConfiguration, CustomerInfo, ProjectSettings,
    ApplicationSettings, ReportConfigSettings, IncludeSections,
    SeverityThresholds, BrandingSettings, SemgrepConfiguration,
    RequiredScans, IntegrationSettings, EmailReporting,
    OrganizationSettings, RepositoryReferenceMapping
)


class ConfigurationManager:
    def __init__(self, config_path: str = 'config/sample-config.json'):
        self._config = self._load_configuration(config_path)

    def _load_configuration(self, config_path: str) -> ReportConfiguration:
        full_path = os.path.abspath(config_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f'Configuration file not found: {full_path}')

        with open(full_path, 'r') as f:
            data = json.load(f)

        config = self._parse_configuration(data)
        self._validate_configuration(config)

        print(f'Configuration loaded for: {config.customer.name}')
        return config

    def _parse_configuration(self, data: dict) -> ReportConfiguration:
        customer = CustomerInfo(
            name=data['customer']['name'],
            industry=data['customer'].get('industry', ''),
            reporting_contact=data['customer'].get('reportingContact', ''),
        )

        projects_raw = data.get('projects', [])
        if not projects_raw and 'project' in data:
            projects_raw = [data['project']]
        projects = [
            ProjectSettings(
                semgrep_project_id=p['semgrepProjectId'],
                include=p.get('include', True),
                name=p.get('name'),
                repository=p.get('repository'),
            )
            for p in projects_raw
        ]

        app = data.get('applicationSettings', {})
        application_settings = ApplicationSettings(
            business_criticality=app.get('businessCriticality', 'High'),
            compliance_requirements=app.get('complianceRequirements', []),
            risk_tolerance=app.get('riskTolerance', 'Low'),
        )

        rc = data.get('reportConfiguration', {})
        sections = rc.get('includeSections', {})
        include_sections = IncludeSections(
            executive_summary=sections.get('executiveSummary', True),
            security_scorecard=sections.get('securityScorecard', True),
            owasp_mapping=sections.get('owaspMapping', True),
            findings_details=sections.get('findingsDetails', True),
            remediation_roadmap=sections.get('remediationRoadmap', True),
            compliance_matrix=sections.get('complianceMatrix', False),
            appendix_methodology=sections.get('appendixMethodology', False),
        )

        thresholds = rc.get('severityThresholds', {})
        severity_thresholds = SeverityThresholds(
            blocking_findings=thresholds.get('blockingFindings', ['Critical']),
            expedited_findings=thresholds.get('expeditedFindings', ['Critical', 'High']),
            scheduled_findings=thresholds.get('scheduledFindings', ['Medium', 'Low']),
        )

        branding_raw = rc.get('branding', {})
        branding = BrandingSettings(
            company_logo=branding_raw.get('companyLogo', './assets/semgrep.svg'),
            primary_color=branding_raw.get('primaryColor', '#2dcda7'),
            accent_color=branding_raw.get('accentColor', '#deede8'),
        )

        repo_mapping_raw = rc.get('repositoryReferenceMapping')
        repo_mapping = None
        if repo_mapping_raw:
            repo_mapping = RepositoryReferenceMapping(
                method=repo_mapping_raw.get('method', 'static'),
                static_mappings=repo_mapping_raw.get('staticMappings') or {},
                external_mapping_file=repo_mapping_raw.get('externalMappingFile'),
            )

        report_config = ReportConfigSettings(
            include_sections=include_sections,
            severity_thresholds=severity_thresholds,
            branding=branding,
            output_formats=rc.get('outputFormats', ['PDF']),
            detail_filter_min_severity=rc.get('detailFilterMinSeverity', 'Medium'),
            findings_detail_level=rc.get('findingsDetailLevel', 'standard'),
            include_dashboard_links=rc.get('includeDashboardLinks', True),
            repository_reference_mapping=repo_mapping,
        )

        sc = data.get('semgrepConfiguration', {})
        required_scans_raw = sc.get('requiredScans', {})
        semgrep_config = SemgrepConfiguration(
            required_scans=RequiredScans(
                sast=required_scans_raw.get('sast', True),
                supply_chain=required_scans_raw.get('supplyChain', True),
                secrets=required_scans_raw.get('secrets', True),
            ),
            rulesets=sc.get('rulesets', []),
            minimum_semgrep_level=sc.get('minimumSemgrepLevel', 'SL3'),
        )

        integ = data.get('integrationSettings', {})
        email_raw = integ.get('emailReporting', {})
        integration_settings = IntegrationSettings(
            jira_ticket_creation=integ.get('jiraTicketCreation', False),
            slack_notifications=integ.get('slackNotifications', False),
            email_reporting=EmailReporting(
                enabled=email_raw.get('enabled', False),
                recipients=email_raw.get('recipients', []),
                frequency=email_raw.get('frequency', 'weekly'),
            ),
        )

        org_raw = data.get('organizationSettings', {})
        org_settings = OrganizationSettings(
            organization_name=org_raw.get('organizationName', ''),
            api_token=org_raw.get('apiToken', ''),
        ) if org_raw else None

        return ReportConfiguration(
            customer=customer,
            projects=projects,
            application_settings=application_settings,
            report_configuration=report_config,
            semgrep_configuration=semgrep_config,
            integration_settings=integration_settings,
            organization_settings=org_settings,
        )

    def _validate_configuration(self, config: ReportConfiguration) -> None:
        if not config.customer.name:
            raise ValueError('Customer name is required in configuration')
        if not config.organization_settings or not config.organization_settings.organization_name:
            raise ValueError('Organization name is required in configuration')
        active = [p for p in config.projects if p.include]
        if not active:
            raise ValueError('At least one project must be configured')

    def get_configuration(self) -> ReportConfiguration:
        return self._config

    def get_customer_name(self) -> str:
        return self._config.customer.name

    def get_organization_name(self) -> str:
        return self._config.organization_settings.organization_name if self._config.organization_settings else 'unknown'

    def get_api_token(self) -> Optional[str]:
        token = (
            self._config.organization_settings.api_token
            if self._config.organization_settings
            else None
        )
        return token or os.environ.get('SEMGREP_APP_TOKEN') or None

    def get_projects(self) -> List[ProjectSettings]:
        return [p for p in self._config.projects if p.include]

    def get_primary_color(self) -> str:
        return self._config.report_configuration.branding.primary_color or '#2dcda7'

    def get_accent_color(self) -> str:
        return self._config.report_configuration.branding.accent_color or '#deede8'

    def get_detail_filter_min_severity(self) -> str:
        return self._config.report_configuration.detail_filter_min_severity or 'Medium'

    def get_findings_detail_level(self) -> str:
        return self._config.report_configuration.findings_detail_level or 'standard'

    def should_include_dashboard_links(self) -> bool:
        return self._config.report_configuration.include_dashboard_links

    def get_repository_reference_mapping(self) -> Dict[str, str]:
        repo_mapping = self._config.report_configuration.repository_reference_mapping
        if repo_mapping and repo_mapping.external_mapping_file:
            mapping_path = os.path.abspath(repo_mapping.external_mapping_file)
            if os.path.exists(mapping_path):
                try:
                    with open(mapping_path, 'r') as f:
                        mapping_array = json.load(f)
                    mapping = {}
                    for entry in mapping_array:
                        if entry.get('ID') and entry.get('Repository ID'):
                            mapping[entry['ID']] = entry['Repository ID']
                    print(f'Loaded {len(mapping)} repository mappings from external file')
                    return mapping
                except Exception as e:
                    print(f'Warning: Error loading external mapping file: {e}')
        return repo_mapping.static_mappings if repo_mapping else {}

    def get_compliance_requirements(self) -> List[str]:
        return self._config.application_settings.compliance_requirements or []

    def get_business_criticality(self) -> str:
        return self._config.application_settings.business_criticality or 'High'
