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
                bat 'set "PATH=C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;%PATH%" && set "DOCKER_HOST=tcp://localhost:2375" && set "DOCKER_CONFIG=C:\\Users\\nikhi\\.docker" && set "COMPOSE_HTTP_TIMEOUT=200" && "C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" compose build'
            }
        }

        stage('Docker Compose Up') {
    steps {
        withCredentials([
            string(credentialsId: 'mongo-uri', variable: 'MONGO_URI'),
            string(credentialsId: 'JWT_SECRET', variable: 'JWT_SECRET'),
            string(credentialsId: 'PINECONE_API_KEY', variable: 'PINECONE_API_KEY'),
            string(credentialsId: 'GROQ_API_KEY', variable: 'GROQ_API_KEY')
        ]) {
            bat 'set "PATH=C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;%PATH%" && set "DOCKER_HOST=tcp://localhost:2375" && set "DOCKER_CONFIG=C:\\Users\\nikhi\\.docker" && "C:\\Users\\nikhi\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" compose up -d'
        }
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