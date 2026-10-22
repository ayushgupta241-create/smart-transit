# TransitScrum: Smart Public Transportation (DevSecOps micro-project)

A small Flask website for public transport: journey search, arrival boards, live vehicle tracking and a Scrum board page. Live data is simulated from the clock. The repo also holds the DevSecOps pipeline around it: Docker, Jenkins, Terraform on AWS, SonarQube and Trivy.

## Repository layout

| Path | Purpose |
|---|---|
| `app/`, `wsgi.py` | Flask application (templates, static files, transit logic, Scrum backlog data) |
| `tests/` | Unit tests (`unittest` style, run by pytest in Jenkins) |
| `Dockerfile`, `.dockerignore` | Slim, non-root container image with a health check |
| `Jenkinsfile` | Pipeline: test, SonarQube, Trivy, build, push, deploy |
| `terraform/` | AWS VPC, subnet, security group and EC2 server that runs the container |
| `sonar-project.properties` | SonarQube scanner settings |
| `docs/diagrams/` | draw.io source and PNG for the architecture and CI/CD diagrams |

## Quick start on Windows (recommended)

1. Extract the ZIP file completely.
2. Open the `smart-transit` folder.
3. Double-click `RUN_SMART_TRANSIT.bat`.
4. The first run installs Python packages, checks `/health`, starts the server and opens the browser.
5. Keep the black terminal window open while using the site. Press `Ctrl+C` in that window to stop it.

You need Python 3.12+ installed and an internet connection for the first package installation. If the browser does not open, wait until the terminal says the server is running, then visit `http://127.0.0.1:8000/`. If setup fails, send the full terminal error.

## 1. Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=xml        # all tests should pass
python wsgi.py                           # http://127.0.0.1:8000
```

Useful URLs: `/`, `/routes`, `/track`, `/scrum`, `/about`, `/stops/S1`, `/api/vehicles`, `/health`.

## 2. Docker

```bash
docker build -t smart-transit:local .
docker run -d --name smart-transit -p 8000:8000 smart-transit:local
curl http://localhost:8000/health         # {"status":"ok",...}
docker ps                                 # STATUS should become "healthy"
```

## 3. Push to GitHub

```bash
git init && git add . && git commit -m "Initial commit: TransitScrum"
git branch -M main
git remote add origin https://github.com/<you>/smart-transit.git
git push -u origin main
```

Commit in small steps from here on (one commit per fix or feature) so the history shows your workflow.

## 4. Jenkins

Install on the Jenkins machine: `git`, `python3`, `python3-venv`, `docker` (add the `jenkins` user to the `docker` group), and `trivy`.

In Jenkins:

1. Plugins: Pipeline, SonarQube Scanner, SSH Agent.
2. Manage Jenkins > Tools: add a **SonarQube Scanner** named `sonar-scanner`.
3. Manage Jenkins > System: add a **SonarQube server** named `sonarqube` (server URL plus an authentication token created in SonarQube under My Account > Security).
4. Credentials: `dockerhub-creds` (Username with password; use a Docker Hub access token, not your password) and `ec2-ssh-key` (SSH username with private key, user `ec2-user`).
5. Edit `IMAGE_REPO` at the top of the `Jenkinsfile` to your Docker Hub repo.
6. New Item > Pipeline > "Pipeline script from SCM" > your GitHub repo, branch `main`.
7. Run **Build with Parameters**. Leave `EC2_HOST` empty for a local deploy on port 8081, or paste the Terraform output IP for AWS.

`ENFORCE_GATES` is off by default so findings are reported without stopping the build. Turn it on to make HIGH/CRITICAL findings and a failed quality gate fail the pipeline.

## 5. SonarQube and Trivy

SonarQube (Docker is the quickest way to run it):

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

Open http://localhost:9000 (first login `admin` / `admin`, then change the password), create a token, and add it to Jenkins as above. The project key is `smart-transit`.

Trivy, run by hand for screenshots:

```bash
trivy fs --scanners vuln,secret .                       # dependencies and secrets
trivy config terraform                                  # Terraform misconfigurations
trivy image smart-transit:local                         # the Docker image
```

Screenshot the SonarQube project dashboard and each Trivy result. Copy real findings into the vulnerability report; if a scan is clean, report its scope and the clean result.

## 6. Terraform on AWS

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # fill in key_name, admin_cidr, docker_image
terraform init
terraform validate
terraform plan
terraform apply
```

Prerequisites: AWS CLI configured (`aws configure`) with an IAM user that can manage EC2/VPC, an existing EC2 key pair in the chosen region, and the Docker image already pushed (run the Jenkins pipeline once first). `admin_cidr` is your public IP as `x.x.x.x/32`.

The `website_url` output is your live site. When you are done recording, run `terraform destroy` so the instance stops costing money.

Never commit `terraform.tfvars`, `*.tfstate`, `.pem` files or access keys; `.gitignore` already excludes them.

## 7. JIRA

Create a Scrum project, add the user stories from `app/backlog.py` (US-01 to US-11) as issues, group them into three sprints and move them across the board as you finish. Screenshot the board and the sprint report. Keep `status` in `app/backlog.py` in step with JIRA.

## 8. Evidence checklist

- [ ] GitHub repo with source, `Dockerfile`, `Jenkinsfile`, `terraform/`
- [ ] `docker ps` showing the healthy container and the site in a browser
- [ ] Jenkins pipeline stage view (all stages) and one console log
- [ ] SonarQube dashboard and Trivy scan screenshots (fs, config, image)
- [ ] `terraform apply` output and the AWS console showing the instance
- [ ] Live site at the Terraform `website_url`
- [ ] JIRA board and sprint report
- [ ] Demo video with no passwords, tokens or access keys visible

Jenkins SCM polling verification.

Automatic Jenkins polling test.
