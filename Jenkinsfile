pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Backend') {
            steps {
                dir('backend') {
                    bat 'npm install'
                }
            }
        }

        stage('Build Frontend') {
            steps {
                dir('frontend') {
                    bat 'npm install'
                    bat 'npm run build'
                }
            }
        }

        stage('Docker Build') {
            steps {
                bat 'set "DOCKER_HOST=tcp://localhost:2375" && set "DOCKER_CONFIG=C:\\Users\\nikhi\\.docker" && set "COMPOSE_HTTP_TIMEOUT=200" && "C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" compose build'
            }
        }

        stage('Docker Compose Up') {
            steps {
                bat 'set "DOCKER_HOST=tcp://localhost:2375" && set "DOCKER_CONFIG=C:\\Users\\nikhi\\.docker" && "C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" compose up -d'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs above.'
        }
    }
}