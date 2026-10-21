# Security scan evidence

Scans run locally on 19/10/2026 with Trivy v0.76.0 (built-in checks only; the vulnerability database could not be downloaded there).

| File | Command | Result |
| --- | --- | --- |
| trivy-config-scan.txt | `trivy config .` | Dockerfile: 0 misconfigurations. Terraform: 3 findings (AWS-0104 x2 CRITICAL, AWS-0178 MEDIUM) |
| trivy-secret-scan.txt | `trivy fs --scanners secret .` | No secrets detected |

Not run there: the SonarQube analysis, the Trivy dependency (CVE) scan and the Trivy image scan. They need the SonarQube
server and the Trivy vulnerability database, so they run in the Jenkins pipeline (see Jenkinsfile) and their results go in the report.
