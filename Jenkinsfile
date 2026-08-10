pipeline {
	agent any 

	environment {
		APP_NAME = 'mast-maggan-app'
		DOCKER_IMAGE = 'mast-maggan-app-web:latest'
		NOTIFICATION_EMAIL = 'realaviilife@gmail.com'
	}

	stages {
		stage('1. SCM checkout' ) {
		 steps {
			echo 'pulling latest code from github.'
			checkout scm
		}
	}
	
	stage('2. Trivy Filesystem scan') {
		steps {
			echo 'Trivy scan on the source code.'
			sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest fs --severity CRITICAL,HIGH .'
		}
	}
	stage('3. build docker image')
		steps {
			echo 'building application docker image'
			sh 'docker compose build --no-cache'
		}
	}
	stage('4. Trivy container image scan') {
		steps {
			echo 'Trivy scan on built docker image'
			sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --severity CRITICAL,HIGH mast-maggan-app-web:latest'
		}
	}
	stage('5. deploy container stack') {
		steps {
			echo ' deploying FastAPI + MYSQL with docker compose'
			sh 'docker compose up -d'
		}
	}
}
post {
	always {
		echo 'Pipeline Execution completed'
	}
	success {
		echo 'Deployment Successful! 
	}
	failure {
		echo 'pipeline failed! sending failure email alert'
		mail to: "${env.NOTIFICATION_EMAIL}",
		     subject: "FAILED: job '${env.JOB_NAME}' [Build #${env.BUILD_NUMBER}]",
		     body: """
			ALERT: jenkins pipeline deployment failed! 
			

			Project: ${env.JOB_NAME}
			Build Number: #${env.BUILD_NUMBER}
			Build URL: ${env.BUILD_URL}
			

			please check the jenkins console logs to reslove the issue. 
            	    """
		}
	}
}		









