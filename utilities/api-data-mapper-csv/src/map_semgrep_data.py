import util.semgrep_api as semgrep_api
import util.semgrep_data as dutil

if __name__ == "__main__":
    findings = semgrep_api.get_findings()
    policy = semgrep_api.get_policy()
    rules = policy['config']['rules']['rules']

    mapped_findings = dutil.map_finding_fields(findings, rules)
    mapped_rules = dutil.map_rule_fields(rules)

    dutil.write_findings(mapped_findings)
    dutil.write_rules(mapped_rules)

    print("Done.")

