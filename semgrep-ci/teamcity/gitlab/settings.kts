package _Self.buildTypes

import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildFeatures.pullRequests
import jetbrains.buildServer.configs.kotlin.buildSteps.ScriptBuildStep
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.triggers.schedule
import jetbrains.buildServer.configs.kotlin.triggers.vcs

object Security : BuildType({
    name = "Security"

    params {
        password("env.SEMGREP_APP_TOKEN", "", display = ParameterDisplay.HIDDEN)
        param("env.SEMGREP_REPO_URL", "%vcsroot.url%")
        param("env.SEMGREP_REPO_NAME", "stuartcmehrens1/js-app-gitlab")
        password("env.GITLAB_TOKEN", "", display = ParameterDisplay.HIDDEN)
    }

    vcs {
        root(HttpsGitlabComStuartcmehrens1jsAppGitlabGitRefsHeadsMain)
    }

    steps {
        script {
            name = "semgrep-diff-scan"
            id = "semgrep"
            executionMode = BuildStep.ExecutionMode.ALWAYS

            conditions {
                exists("teamcity.pullRequest.number")
            }
            scriptContent = "semgrep ci"
            dockerImage = "semgrep/semgrep"
            dockerImagePlatform = ScriptBuildStep.ImagePlatform.Linux
            dockerPull = true
        }
        script {
            name = "semgrep-full-scan"
            id = "semgrep_full_scan"
            executionMode = BuildStep.ExecutionMode.ALWAYS

            conditions {
                doesNotExist("teamcity.pullRequest.number")
            }
            scriptContent = "semgrep ci"
            dockerImage = "semgrep/semgrep"
            dockerImagePlatform = ScriptBuildStep.ImagePlatform.Linux
            dockerPull = true
        }
    }

    triggers {
        vcs {

            buildParams {
                param("env.SEMGREP_BASELINE_REF", "origin/%teamcity.pullRequest.target.branch%")
                param("env.SEMGREP_BRANCH", "%teamcity.pullRequest.source.branch%")
                param("env.SEMGREP_PR_ID", "%teamcity.pullRequest.number%")
                param("teamcity.git.fetchAllHeads", "true")
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
        pullRequests {
            vcsRootExtId = "${HttpsGitlabComStuartcmehrens1jsAppGitlabGitRefsHeadsMain.id}"
            provider = gitlab {
                authType = vcsRoot()
            }
        }
    }

    requirements {
        matches("teamcity.agent.jvm.os.family", "Linux")
    }
})
