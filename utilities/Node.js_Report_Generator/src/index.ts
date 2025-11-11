import * as path from 'path';
import { ConfigurationManager, SemgrepApiClient, ScoringEngine } from './services';
import { BasicPdfGenerator } from './pdf/BasicPdfGenerator';
import { SemgrepProject } from './models';
import { Logger, CLIOutput } from './utils';

async function main() {
  try {
    CLIOutput.section('Starting Semgrep Security Reporter (Node.js Version)');

    // Get configuration file path from command line arguments or use default
    const configPath = process.argv[2] || 'config/sample-config.json';
    
    CLIOutput.progress(`Loading configuration from: ${configPath}`);
    const configManager = new ConfigurationManager(configPath);
    const config = configManager.getConfiguration();
    
    console.log(`📊 Processing report for: ${config.customer.name}`);
    console.log(`🏢 Organization: ${configManager.getOrganizationName()}`);
    console.log(`🔑 API Token: ${configManager.getApiToken() ? 'Provided' : 'Using dummy data'}\n`);

    // Initialize API client
    const apiClient = new SemgrepApiClient(
      configManager.getOrganizationName(),
      configManager.getApiToken()
    );

    // Fetch project data
    const projects: SemgrepProject[] = [];
    const projectConfigs = configManager.getProjects();
    
    // Check if this is a consolidated org report or auto-discover all projects
    const isConsolidatedReport = projectConfigs.length === 1 && 
      projectConfigs[0].semgrepProjectId === 'consolidated-org-report';
    const isAutoDiscoverAll = projectConfigs.length === 1 && 
      projectConfigs[0].semgrepProjectId === 'auto-discover-all';
    
    if (isConsolidatedReport) {
      console.log(`🔍 Fetching individual projects for consolidated organizational report:`);
      
      // Get the repository mapping to filter active projects
      const repositoryMapping = configManager.getRepositoryReferenceMapping();
      
      // Use the new method to get all individual projects (filtered by active scope)
      const individualProjects = await apiClient.fetchAllProjects(repositoryMapping);
      
      if (individualProjects.length > 0) {
        projects.push(...individualProjects);
        console.log(`    ✓ Found ${individualProjects.length} individual repositories`);
        
        for (const project of individualProjects) {
          console.log(`    - ${project.name}: ${project.findings.length} findings (${project.findings.filter(f => f.status === 'Open').length} open)`);
        }
      } else {
        // Fallback to the old consolidated approach if individual projects fail
        console.log(`    ! Failed to fetch individual projects, falling back to consolidated approach`);
        const project = await apiClient.fetchProjectFindings('consolidated-org-report');
        projects.push(project);
        console.log(`    ✓ Found ${project.findings.length} findings (${project.findings.filter(f => f.status === 'Open').length} open)`);
      }
    } else if (isAutoDiscoverAll) {
      console.log(`🔍 Auto-discovering all projects for individual project reports:`);
      
      // Use fetchAllProjects to get individual projects, then treat them as separate projects
      const individualProjects = await apiClient.fetchAllProjects();
      
      if (individualProjects.length > 0) {
        projects.push(...individualProjects);
        console.log(`    ✓ Auto-discovered ${individualProjects.length} individual repositories`);
        
        for (const project of individualProjects) {
          console.log(`    - ${project.name}: ${project.findings.length} findings (${project.findings.filter(f => f.status === 'Open').length} open)`);
        }
      } else {
        console.log(`    ! No projects found during auto-discovery`);
      }
    } else {
      console.log(`🔍 Fetching data for ${projectConfigs.length} project(s):`);
      
      for (const projectConfig of projectConfigs) {
        console.log(`  - Processing project: ${projectConfig.semgrepProjectId}`);
        const project = await apiClient.fetchProjectFindings(projectConfig.semgrepProjectId);
        projects.push(project);
        
        console.log(`    ✓ Found ${project.findings.length} findings (${project.findings.filter(f => f.status === 'Open').length} open)`);
      }
    }

    // Calculate overall statistics
    const totalFindings = projects.reduce((sum, project) => sum + project.findings.length, 0);
    const openFindings = projects.reduce((sum, project) => 
      sum + project.findings.filter(f => f.status === 'Open').length, 0);
    
    console.log(`\n📈 Overall Statistics:`);
    console.log(`  - Total Findings: ${totalFindings}`);
    console.log(`  - Open Findings: ${openFindings}`);
    console.log(`  - Fixed/Ignored: ${totalFindings - openFindings}`);

    // Calculate security levels for each project
    const scoringEngine = new ScoringEngine();
    console.log(`\n🎯 Security Levels:`);
    for (const project of projects) {
      const level = scoringEngine.calculateSemgrepLevel(project);
      const score = scoringEngine.calculateSecurityScore(project.findings);
      console.log(`  - ${project.name}: SL${level} (Score: ${score})`);
    }

    // Generate PDF report
    console.log(`\n📄 Generating PDF report...`);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const outputPath = path.join('output', `semgrep-report-${config.customer.name.toLowerCase().replace(/\s+/g, '-')}-${timestamp}.pdf`);
    
    const pdfGenerator = new BasicPdfGenerator();
    const generatedPath = await pdfGenerator.generateReport(projects, config, outputPath);
    
    console.log(`\n✅ Report generation complete!`);
    console.log(`📁 Report saved to: ${generatedPath}`);
    console.log(`\n🔗 Next steps:`);
    console.log(`  - Review the generated PDF report`);
    console.log(`  - Share with stakeholders`);
    console.log(`  - Begin remediation of critical and high severity findings`);
    
  } catch (error) {
    console.error('❌ Error generating report:', error);
    process.exit(1);
  }
}

// Run the application
main().catch(console.error);