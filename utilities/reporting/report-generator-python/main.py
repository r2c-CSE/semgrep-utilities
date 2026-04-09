#!/usr/bin/env python3
"""Semgrep Security Reporter - Python port of the Node.js report generator."""

import os
import sys
from datetime import datetime
from typing import List

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from models import SemgrepProject
from services import ConfigurationManager, SemgrepApiClient, ScoringEngine
from pdf import BasicPdfGenerator


def main() -> None:
    print('Starting Semgrep Security Reporter')

    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config/sample-config.json'
    print(f'Loading configuration from: {config_path}')

    config_manager = ConfigurationManager(config_path)
    config = config_manager.get_configuration()

    token_status = 'Provided' if config_manager.get_api_token() else 'Using dummy data'
    print(f'Processing report for: {config.customer.name}')
    print(f'Organization: {config_manager.get_organization_name()}')
    print(f'API Token: {token_status}')

    api_client = SemgrepApiClient(
        organization_name=config_manager.get_organization_name(),
        api_token=config_manager.get_api_token(),
    )

    projects: List[SemgrepProject] = []
    project_configs = config_manager.get_projects()

    is_consolidated = (
        len(project_configs) == 1 and
        project_configs[0].semgrep_project_id == 'consolidated-org-report'
    )
    is_auto_discover = (
        len(project_configs) == 1 and
        project_configs[0].semgrep_project_id == 'auto-discover-all'
    )

    if is_consolidated:
        print('Fetching individual projects for consolidated organizational report:')
        repo_mapping = config_manager.get_repository_reference_mapping()
        individual = api_client.fetch_all_projects(repo_mapping if repo_mapping else None)

        if individual:
            projects.extend(individual)
            print(f'    Found {len(individual)} individual repositories')
            for p in individual:
                open_count = sum(1 for f in p.findings if f.status == 'Open')
                print(f'    - {p.name}: {len(p.findings)} findings ({open_count} open)')
        else:
            print('    ! Failed to fetch individual projects, falling back to consolidated approach')
            project = api_client.fetch_project_findings('consolidated-org-report')
            projects.append(project)
            open_count = sum(1 for f in project.findings if f.status == 'Open')
            print(f'    Found {len(project.findings)} findings ({open_count} open)')

    elif is_auto_discover:
        print('Auto-discovering all projects:')
        individual = api_client.fetch_all_projects()
        if individual:
            projects.extend(individual)
            print(f'    Auto-discovered {len(individual)} individual repositories')
            for p in individual:
                open_count = sum(1 for f in p.findings if f.status == 'Open')
                print(f'    - {p.name}: {len(p.findings)} findings ({open_count} open)')
        else:
            print('    ! No projects found during auto-discovery')

    else:
        print(f'Fetching data for {len(project_configs)} project(s):')
        for project_config in project_configs:
            print(f'  - Processing project: {project_config.semgrep_project_id}')
            project = api_client.fetch_project_findings(project_config.semgrep_project_id)
            projects.append(project)
            open_count = sum(1 for f in project.findings if f.status == 'Open')
            print(f'    Found {len(project.findings)} findings ({open_count} open)')

    total_findings = sum(len(p.findings) for p in projects)
    open_findings = sum(
        sum(1 for f in p.findings if f.status == 'Open') for p in projects
    )
    print(f'\nOverall Statistics:')
    print(f'  - Total Findings: {total_findings}')
    print(f'  - Open Findings: {open_findings}')
    print(f'  - Fixed/Ignored: {total_findings - open_findings}')

    scoring_engine = ScoringEngine()
    print('\nSecurity Levels:')
    for project in projects:
        level = int(scoring_engine.calculate_semgrep_level(project))
        score = scoring_engine.calculate_security_score(project.findings)
        print(f'  - {project.name}: SL{level} (Score: {score})')

    print('\nGenerating PDF report...')
    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    safe_name = config.customer.name.lower().replace(' ', '-')
    output_path = os.path.join('output', f'semgrep-report-{safe_name}-{timestamp}.pdf')

    pdf_generator = BasicPdfGenerator()
    generated_path = pdf_generator.generate_report(projects, config, output_path)

    print('\nReport generation complete!')
    print(f'Report saved to: {generated_path}')
    print('\nNext steps:')
    print('  - Review the generated PDF report')
    print('  - Share with stakeholders')
    print('  - Begin remediation of critical and high severity findings')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'Error generating report: {e}', file=sys.stderr)
        raise SystemExit(1)
