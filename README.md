# Semgrep utilities

It is a non-official but helpful repository with Semgrep utilities such as API examples, integration, scripts to speed up the onboarding process, and standard configuration.
If you have something valuable to share, feel free to collaborate!

## CI utilities
It is the category for ci utilities.

### Utility to speed up onboarding for Azure classic pipelines 

This utility helps to set up Semgrep Scans in Azure classic pipelines.

Requirements:
* Create your system's environment variable `ADO_TOKEN` with a valid Azure DevOps API Token.
```
export ADO_TOKEN=xxxxxx
```
* Follow steps from the [Azure Classic pipelines presentation:](https://docs.google.com/presentation/d/1PIjNss8Zy9413v99-5udNxycJFEoCz3JFRMbf1OY344/edit?usp=sharing)
    * Create a Semgrep task group at the project level. It must be named as Semgrep-Task-Group
    * Create Semgrep variables at the project level. It must be named as Semgrep_Variables.
    * Modify script `semgrep-ci/azure/update_pipeline_with_semgrep_task.py` by adding org (organisation name) and project (project name)—constants section.
    * Get Task Group ID and add it to the Python script too.
* run script:
```
python3 semgrep-ci/azure/update_pipeline_with_semgrep_task.py
```
### Utility to speed up onboarding for Bitbucket pipelines (coming soon)

## Integration utilities
It is the category for integration utilities.

### Utility to integrate Semgrep results in DefectDojo

[DefectDojo](https://www.defectdojo.com/) is a well-known tool for managing security vulnerabilities.
This utility dumps security findings detected by semgrep to DefectDojo.

Steps:
* In your system, declare environment variable `DEFECT_DOJO_API_TOKEN`
```
export DEFECT_DOJO_API_TOKEN=xxxxxx
```
* In DefectDojo:
    * Create your product (a product is DefectDojo's concept for a project).
    * For that DefectDojo product, create an engagement called `semgrep`.
* Run a semgrep scan with flags `--json --output report.json` to generate a json report.
* Run script
```
python3 integrations/defectdojo/import_semgrep_to_defect_dojo.py --host DOJO_URL --product PRODUCT_NAME --engagement ENGAGEMENT_NAME --report REPORT_FILE 
```
Where:
* `DOJO_URL` is the URL where DefectDojo is installed.
* `REPORT_FILE` is the Semgrep report path

## General utilities
It is the category for general utilities.

### Semgrep API with Python
 
How to run:
* Edit file: utilities/api/python_client_semgrep_api.py adding a valid Semgrep token.
* Execute:

```
python3 utilities/api/python_client_semgrep_api.py 
```
The script does the following:
* Get your current deployment
* Get your projects
* Dump a Json report for each project filtering by High Severity and High-Medium Confidence.
  
**_NOTE:_** Take into account the `SEMGREP_APP_TOKEN` must have API permissions.

### Kubernetes pod example
It is a Kubernetes pod that can launch semgrep scans.
As requirements:
* Install minikube
* Start minikube:
```
minikube start
```

* Add a valid Semgrep token in the pod configuration: `./utilities/kubernetes/semgrep-pod.yml`

* Deploy the pod (run the semgrep scan):
```
kubectl apply -f ./utilities/kubernetes/semgrep-pod.yml
```
* To see the execution, write:
```
kubectl logs semgrep
```

### json-csv timing converter
Utility to convert Semgrep JSON output (`--json --time --output timing.json`) to CSV. Useful to verify time consumption per file and rule.

Steps:
* Generate a json report when running semgrep, adding the following flags: `--json --time --output timing.json`
* Copy timing.json report to folder utilities/input
* Run script:
```
python3 utilities/convert_timing_output_json_to_csv/convert_timing_output_json_to_csv.py
```
**_NOTE:_** The input to the script (the semgrep output) should be named timing.json, or you can change it in the Python script.

Example input (semgrep output):
```
{"errors": [], "paths": {"_comment": "<add --verbose for a list of skipped paths>", "scanned": ["CertSelect.cs", "Program.cs"]}, "results": [{"check_id": "csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "end": {"col": 50, "line": 19, "offset": 913}, "extra": {"engine_kind": "OSS", "fingerprint": "7a6e7960165835af7619883000cf1ccca597050e467fe8c37c226e5a4addf85f04ecfe1cf912fc8aac4726717f2c96bcac2bf129d06685df51cdf39923349876_0", "is_ignored": false, "lines": "                Console.WriteLine(x509.PrivateKey);", "message": "X509Certificate2.PrivateKey is obsolete. Use a method such as GetRSAPrivateKey() or GetECDsaPrivateKey(). Alternatively, use the CopyWithPrivateKey() method to create a new instance with a private key. Further, if you set X509Certificate2.PrivateKey to `null` or set it to another key without deleting it first, the private key will be left on disk. ", "metadata": {"category": "security", "confidence": "LOW", "cwe": ["CWE-310: CWE CATEGORY: Cryptographic Issues"], "impact": "LOW", "license": "Commons Clause License Condition v1.0[LGPL-2.1-only]", "likelihood": "LOW", "owasp": ["A02:2021 - Cryptographic Failures"], "references": ["https://docs.microsoft.com/en-us/dotnet/api/system.security.cryptography.x509certificates.x509certificate2.privatekey"], "semgrep.dev": {"rule": {"origin": "community", "rule_id": "QrUk26", "url": "https://semgrep.dev/playground/r/qkT9Jv/csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "version_id": "qkT9Jv"}}, "shortlink": "https://sg.run/jDeN", "source": "https://semgrep.dev/r/csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "subcategory": ["audit"], "technology": [".net"]}, "metavars": {"$CERT": {"abstract_content": "x509", "end": {"col": 39, "line": 19, "offset": 902}, "start": {"col": 35, "line": 19, "offset": 898}}, "$COLLECTION": {"abstract_content": "collection", "end": {"col": 46, "line": 10, "offset": 273}, "start": {"col": 36, "line": 10, "offset": 263}}}, "severity": "WARNING"}, "path": "CertSelect.cs", "start": {"col": 35, "line": 19, "offset": 898}}, {"check_id": "csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "end": {"col": 38, "line": 30, "offset": 1269}, "extra": {"engine_kind": "OSS", "fingerprint": "661d7c5624d22c4c022261fb39c393ca0bdfedfaa8dff9c912d7984fb60096f04a6f4dab328db3d3c4fb1ff14eebaf520e866f1f464e460d2ff44551c1f40419_0", "is_ignored": false, "lines": "        var privkey = cert.PrivateKey;", "message": "X509Certificate2.PrivateKey is obsolete. Use a method such as GetRSAPrivateKey() or GetECDsaPrivateKey(). Alternatively, use the CopyWithPrivateKey() method to create a new instance with a private key. Further, if you set X509Certificate2.PrivateKey to `null` or set it to another key without deleting it first, the private key will be left on disk. ", "metadata": {"category": "security", "confidence": "LOW", "cwe": ["CWE-310: CWE CATEGORY: Cryptographic Issues"], "impact": "LOW", "license": "Commons Clause License Condition v1.0[LGPL-2.1-only]", "likelihood": "LOW", "owasp": ["A02:2021 - Cryptographic Failures"], "references": ["https://docs.microsoft.com/en-us/dotnet/api/system.security.cryptography.x509certificates.x509certificate2.privatekey"], "semgrep.dev": {"rule": {"origin": "community", "rule_id": "QrUk26", "url": "https://semgrep.dev/playground/r/qkT9Jv/csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "version_id": "qkT9Jv"}}, "shortlink": "https://sg.run/jDeN", "source": "https://semgrep.dev/r/csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey", "subcategory": ["audit"], "technology": [".net"]}, "metavars": {"$CERT": {"abstract_content": "cert", "end": {"col": 27, "line": 30, "offset": 1258}, "start": {"col": 23, "line": 30, "offset": 1254}}, "$COLLECTION": {"abstract_content": "collection", "end": {"col": 46, "line": 10, "offset": 273}, "start": {"col": 36, "line": 10, "offset": 263}}}, "severity": "WARNING"}, "path": "CertSelect.cs", "start": {"col": 23, "line": 30, "offset": 1254}}], "time": {"max_memory_bytes": 56000512, "profiling_times": {"config_time": 0.47869086265563965, "core_time": 0.10312008857727051, "ignores_time": 0.0008003711700439453, "total_time": 0.5835583209991455}, "rules": [{"id": "csharp.lang.security.cryptography.x509certificate2-privkey.X509Certificate2-privkey"}], "rules_parse_time": 0.0016241073608398438, "targets": [{"match_times": [0.0003120899200439453], "num_bytes": 1279, "parse_times": [0.00807499885559082], "path": "CertSelect.cs", "run_time": 0.011127948760986328}, {"match_times": [0.0], "num_bytes": 1137, "parse_times": [0.0], "path": "Program.cs", "run_time": 0.001001119613647461}], "total_bytes": 2416}, "version": "1.14.0"}% 
```

Example outputs:
```
path,run_time
CertSelect.cs,0.011127948760986328
Program.cs,0.001001119613647461
````

```
rule,rule_time
bash.curl.security.curl-eval.curl-eval,0.045
bash.curl.security.curl-pipe-bash.curl-pipe-bash,0.033
bash.lang.security.ifs-tampering.ifs-tampering,0.044
````



