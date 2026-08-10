pipeline {
    agent any

    environment {
        APP_NAME = 'mast-maggan-app'
        DOCKER_IMAGE = 'mast-maggan-devsecops-pipeline-web:latest'
        ALERT_EMAIL = 'realaviilife@gmail.com'
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
                bat 'docker run --rm -v //./pipe/docker_engine://./pipe/docker_engine aquasec/trivy:latest fs --timeout 15m --severity CRITICAL,HIGH .'
            }
        }

        stage('3. Build Docker Image') {
            steps {
                echo 'Building Application Docker Image...'
                bat 'docker compose build --no-cache'
            }
        }

        stage('4. Trivy Container Image Scan') {
            steps {
                echo 'Running Trivy Scan on Built Docker Image...'
                bat 'docker run --rm -v //./pipe/docker_engine://./pipe/docker_engine aquasec/trivy:latest image --timeout 15m --severity CRITICAL,HIGH mast-maggan-devsecops-pipeline-web:latest'
            }
            }
        }

        stage('5. Deploy Container Stack') {
            steps {
                echo 'Deploying FastAPI + MySQL with Docker Compose...'
                bat 'docker compose up -d'
            }
 	}
    }


    post {
        always {
            echo 'Pipeline Execution Completed.'
        }
        success {
            echo 'Deployment Successful! App is Live.'
        }
        failure {
            echo 'Pipeline Failed! Attempting to send notification...'
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

    
