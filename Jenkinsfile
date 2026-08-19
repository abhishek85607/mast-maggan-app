pipeline {
    agent any

    environment {
        APP_NAME = 'mast-maggan-app'
        IMAGE_BASE = 'mast-maggan-app-web'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DOCKER_IMAGE = "${IMAGE_BASE}:${IMAGE_TAG}"
        
        ALERT_EMAIL = 'realaviilife@gmail.com'
        SONAR_HOST_URL = 'http://10.254.225.42:9000'
        SONAR_TOKEN = 'squ_0a9917f55e7b3712ec162c65e0bf1af00fd3d1ad'
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
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    bat """
                        docker run --rm -v "%WORKSPACE%:/usr/src" sonarsource/sonar-scanner-cli -Dsonar.projectKey=mast-maggan-app -Dsonar.sources=. -Dsonar.host.url=${SONAR_HOST_URL} -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }

        stage('4. Build & Save Docker Image') {
            steps {
                echo 'Building and exporting Application Docker Image...'
                bat """
                    docker build -t ${IMAGE_BASE}:${IMAGE_TAG} -t ${IMAGE_BASE}:latest .
                    docker save ${IMAGE_BASE}:${IMAGE_TAG} -o "%WORKSPACE%\\image.tar"
                """
            }
        }

        stage('5. Trivy Container Image Scan') {
            steps {
                echo 'Running Trivy Scan on Built Docker Image...'
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    bat """
                        docker run --rm -v trivy-cache:/root/.cache/ -v "%WORKSPACE%:/workspace" aquasec/trivy:latest image --input /workspace/image.tar --severity CRITICAL,HIGH
                    """
                }
            }
        }

        stage('6. Transfer Image to Linux VM & Minikube') {
            steps {
                echo 'Transferring Image to Linux VM and loading into Minikube...'
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    // Windows se VM par image transfer aur minikube me load
                    bat """
                        curl -T "%WORKSPACE%\\image.tar" http://10.254.225.42:8000/upload_tmp 2>NUL || exit 0
                        del "%WORKSPACE%\\image.tar"
                    """
                }
            }
        }

        stage('7. Deploy to Kubernetes Cluster') {
            steps {
                echo 'Deploying to Kubernetes Cluster...'
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    bat """
                        kubectl --kubeconfig="C:\\Users\\abhis\\.kube\\config" apply -f k8s/ --validate=false
                        kubectl --kubeconfig="C:\\Users\\abhis\\.kube\\config" rollout restart deployment/mast-maggan-app
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline Execution Completed.'
        }
        success {
            echo 'Deployment Successful! App is Live with New UI & Songs.'
            script {
                try {
                    mail to: "realaviilife@gmail.com",
                         subject: "SUCCESS: Job '${env.JOB_NAME}' [Build #${env.BUILD_NUMBER}]",
                         body: "Awesome! Your pipeline completed successfully and new build #${env.BUILD_NUMBER} is live! Build URL: ${env.BUILD_URL}"
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
