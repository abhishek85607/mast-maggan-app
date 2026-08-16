pipeline {
    agent any

    environment {
        APP_NAME = 'mast-maggan-app'
        DOCKER_IMAGE = 'mast-maggan-devsecops-pipeline-web:latest'
        ALERT_EMAIL = 'realaviilife@gmail.com'
        SONAR_HOST_URL = 'http://10.112.217.42:9000'
        SONAR_TOKEN = 'sqa_8fd383c87364feac0d834a34f936cc64daf9f79d'
    }

    stages {
        stage('1. SCM Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('2. Trivy Filesystem Scan') {
            steps {
                echo 'Running Trivy Vulnerability Scan on Source Code...'
                bat 'docker run --rm -v trivy-cache:/root/.cache/ -v //./pipe/docker_engine://./pipe/docker_engine aquasec/trivy:latest fs --timeout 15m --severity CRITICAL,HIGH . & exit 0'
            }
        }

        stage('3. SonarQube Analysis') {
            steps {
                echo 'Running SonarQube Code Quality & Security Scan...'
                bat '''
                    docker run --rm ^
                      --add-host=host.docker.internal:host-gateway ^
                      -v "%WORKSPACE%:/usr/src" ^
                      sonarsource/sonar-scanner-cli ^
                      -Dsonar.projectKey=mast-maggan-app ^
                      -Dsonar.sources=. ^
                      -Dsonar.host.url=%SONAR_HOST_URL% ^
                      -Dsonar.token=%SONAR_TOKEN% || exit 0
                '''
            }
        }
                            
        stage('4. Build Docker Image') {
            steps {
                echo 'Building Application Docker Image...'
                bat 'docker compose build'
            }
        }

        stage('5. Trivy Container Image Scan') {
            steps {
                echo 'Running Trivy Scan on Built Docker Image...'
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    bat '''
                        docker save mast-maggan-devsecops-pipeline-web:latest -o "%WORKSPACE%\\image.tar"
                        docker run --rm -v trivy-cache:/root/.cache/ -v "%WORKSPACE%:/workspace" aquasec/trivy:latest image --input /workspace/image.tar --severity CRITICAL,HIGH
                        del "%WORKSPACE%\\image.tar"
                    '''
                }
            }
        }

        stage('6. Deploy Container Stack') {
            steps {
                echo 'Deploying FastAPI + MySQL with Docker Compose...'
                bat 'docker compose up -d'
            }
        }

        stage('7. Deploy to Kubernetes Cluster') {
            steps {
                echo 'Applying Kubernetes Manifests and Restarting Deployment...'
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    bat 'kubectl --kubeconfig="C:\\Users\\abhis\\.kube\\config" apply -f k8s/ --validate=false'
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline Execution Completed.'
        }
        success {
            echo 'Deployment Successful! App is Live.'
            script {
                try {
                    mail to: "realaviilife@gmail.com",
                         subject: "SUCCESS: Job '${env.JOB_NAME}' [Build #${env.BUILD_NUMBER}]",
                         body: "Awesome! Your pipeline completed successfully and app is live! Build URL: ${env.BUILD_URL}"
                } catch (Exception e) {
                    echo "Email alert skipped: ${e.getMessage()}"
                }
            }
        }
        failure {
            echo 'Pipeline Failed! Check console logs.'
            script {
                try {
                    mail to: "realaviilife@gmail.com",
                         subject: "FAILED: Job '${env.JOB_NAME}' [Build #${env.BUILD_NUMBER}]",
                         body: "Pipeline failed. Check Jenkins logs: ${env.BUILD_URL}"
                } catch (Exception e) {
                    echo "Email alert skipped: ${e.getMessage()}"
                }
            }
        }
    }
}
