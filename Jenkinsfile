// CI/CD pipeline for the Smart Public Transportation app (declarative pipeline).
//
// One-time Jenkins setup (see README.md, section 4):
//   - Tools on the agent: git, python3 + python3-venv, docker, trivy
//   - Plugins: Pipeline, SonarQube Scanner, SSH Agent
//   - Global Tool Configuration: SonarQube Scanner installation named "sonar-scanner"
//   - Manage Jenkins > System: SonarQube server named "sonarqube" (URL + token)
//   - Credentials: "dockerhub-creds" (username/password), "ec2-ssh-key" (SSH private key)
//   - Edit IMAGE_REPO below to your Docker Hub repository
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    parameters {
        string(name: 'EC2_HOST', defaultValue: '',
               description: 'Public IP/DNS of the Terraform-created EC2 instance. Leave empty to deploy locally on port 8081.')
        booleanParam(name: 'ENFORCE_GATES', defaultValue: false,
                     description: 'Fail the build on SonarQube quality gate failure or HIGH/CRITICAL Trivy findings.')
    }

    environment {
        IMAGE_REPO = 'your-dockerhub-username/smart-transit'   // <-- change me
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        TRIVY_EXIT = "${params.ENFORCE_GATES ? '1' : '0'}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -r requirements-dev.txt
                    pytest --cov=app --cov-report=xml --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            when { expression { params.ENFORCE_GATES } }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Trivy: dependencies & Terraform') {
            steps {
                sh '''
                    set +e
                    trivy fs --scanners vuln,secret --severity HIGH,CRITICAL \
                        --exit-code "$TRIVY_EXIT" --output trivy-fs-report.txt .
                    rc1=$?
                    trivy config --severity HIGH,CRITICAL --exit-code "$TRIVY_EXIT" \
                        --output trivy-terraform-report.txt terraform
                    rc2=$?
                    cat trivy-fs-report.txt trivy-terraform-report.txt
                    [ "$rc1" -eq 0 ] && [ "$rc2" -eq 0 ]
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t "$IMAGE_REPO:$IMAGE_TAG" -t "$IMAGE_REPO:latest" .'
            }
        }

        stage('Trivy: image') {
            steps {
                sh '''
                    set +e
                    trivy image --severity HIGH,CRITICAL --exit-code "$TRIVY_EXIT" \
                        --output trivy-image-report.txt "$IMAGE_REPO:$IMAGE_TAG"
                    rc=$?
                    cat trivy-image-report.txt
                    exit $rc
                '''
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push "$IMAGE_REPO:$IMAGE_TAG"
                        docker push "$IMAGE_REPO:latest"
                    '''
                }
            }
            post {
                always {
                    sh 'docker logout || true'
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    def host = params.EC2_HOST?.trim()
                    if (host) {
                        // Only allow a plain hostname or IP so the parameter cannot inject shell commands
                        if (!(host ==~ /^[A-Za-z0-9.\-]+$/)) {
                            error 'EC2_HOST must be a hostname or IP address.'
                        }
                        def remote = "docker pull ${IMAGE_REPO}:${IMAGE_TAG} && (docker rm -f smart-transit || true) && " +
                                     "docker run -d --name smart-transit --restart unless-stopped -p 80:8000 ${IMAGE_REPO}:${IMAGE_TAG}"
                        sshagent(credentials: ['ec2-ssh-key']) {
                            sh "ssh -o StrictHostKeyChecking=accept-new ec2-user@${host} '${remote}'"
                        }
                        echo "Deployed to http://${host}"
                    } else {
                        sh '''
                            docker rm -f smart-transit || true
                            docker run -d --name smart-transit --restart unless-stopped -p 8081:8000 "$IMAGE_REPO:$IMAGE_TAG"
                        '''
                        echo 'Deployed locally at http://localhost:8081'
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'trivy-*.txt, coverage.xml', allowEmptyArchive: true
        }
        success {
            echo 'Pipeline finished: tested, scanned, built and deployed.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs and the archived Trivy reports.'
        }
    }
}
