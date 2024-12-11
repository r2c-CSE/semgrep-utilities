import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildFeatures.pullRequests
import jetbrains.buildServer.configs.kotlin.buildFeatures.perfmon
import jetbrains.buildServer.configs.kotlin.buildSteps.ScriptBuildStep
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.triggers.schedule
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.buildSteps.python

version = "2024.03"

project {
    buildType(SemgrepFullScans)
    buildType(SemgrepDiffScans)
}

object SemgrepFullScans : BuildType({

    name = "Semgrep-Full-Scans"

    vcs {
        root(DslContext.settingsRoot)
    }

    steps {
        script {
            name = "semgrep-full-scan"
            id = "semgrep_full_scan"
            executionMode = BuildStep.ExecutionMode.ALWAYS

            conditions {
                doesNotExist("teamcity.pullRequest.number")
                equals("teamcity.build.branch.is_default", "true") 
            }
            scriptContent = "semgrep ci"
        }
    }

    triggers {

        vcs {
            buildParams {
                password("env.SEMGREP_APP_TOKEN", "", display = ParameterDisplay.HIDDEN)
                param("env.SEMGREP_REPO_URL", "%vcsroot.url%")
                param("env.SEMGREP_REPO_NAME", "%teamcity.project.id%") // teamcity.project.id should retrieve the repository name, please, change it if you needed
            }
        }
        
        schedule {
            schedulingPolicy = daily {
                hour = 0
            }
            branchFilter = "+:refs/heads/main"
            triggerBuild = always()
            withPendingChangesOnly = false
            enableQueueOptimization = false
        }
    }

    features {
        perfmon {
        }
    }
})

object SemgrepDiffScans : BuildType({
    
    name = "Semgrep-Diff-Scans"

    vcs {
        root(DslContext.settingsRoot)
    }

    steps {
        script {
            name = "semgrep-diff-scan"
            id = "semgrep_diff_scan"
            executionMode = BuildStep.ExecutionMode.ALWAYS

            conditions {
                exists("teamcity.pullRequest.number")
                equals("teamcity.build.branch.is_default", "false") 
            }
            scriptContent = "semgrep ci"
        }
    }

    triggers {
        vcs {
            buildParams {
                password("env.SEMGREP_APP_TOKEN", "", display = ParameterDisplay.HIDDEN)
                param("env.SEMGREP_REPO_URL", "%vcsroot.url%")
                param("env.SEMGREP_REPO_NAME", "%teamcity.project.id%")
                param("env.SEMGREP_BASELINE_REF", "%vcsroot.branch%")
                param("env.SEMGREP_BRANCH", "%teamcity.pullRequest.source.branch%")
                param("env.SEMGREP_PR_ID", "%teamcity.pullRequest.number%")
                param("teamcity.git.fetchAllHeads", "true")
            }
        }
    }

    features {

        pullRequests {
            vcsRootExtId = "${DslContext.settingsRoot.id}"
            provider = gitlab {
                authType = vcsRoot()
            }
        }

        perfmon {
        }
    }
})
