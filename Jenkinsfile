def getStandAloneStorageServers(){
    retry(conditions: [agent()], count: 3) {
        node(){
            configFileProvider([configFile(fileId: 'deploymentStorageConfig', variable: 'CONFIG_FILE')]) {
                def config = readJSON( file: CONFIG_FILE)
                return config['publicReleases']['urls']
            }
        }
    }
}

def deployStandalone(glob, url) {
    script{
        findFiles(glob: glob).each{
            try{
                def encodedUrlFileName = new URI(null, null, it.name, null).toASCIIString()
                def putResponse = httpRequest authentication: NEXUS_CREDS, httpMode: 'PUT', uploadFile: it.path, url: "${url}/${encodedUrlFileName}", wrapAsMultipart: false
                echo "http request response: ${putResponse.content}"
                echo "Deployed ${it} -> SHA256: ${sha256(it.path)}"
            } catch(Exception e){
                echo "${e}"
                throw e;
            }
        }
    }
}

GET_VERSION_PYTHON_SCRIPT = '''#!/usr/bin/env python3
import tomllib
with open('pyproject.toml', 'rb') as f:
    print(tomllib.load(f)['project']['version'])
'''

def get_version(){
    node('linux && docker'){
        docker.image('python').inside {
            checkout scm
            return sh(
                label:'Getting package version from pyproject.toml',
                script: GET_VERSION_PYTHON_SCRIPT,
                returnStdout: true
            ).trim()
        }
    }
}

standaloneVersions = []

pipeline {
    agent none
    parameters{
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'PACKAGE_STANDALONE_WINDOWS_INSTALLER', defaultValue: false, description: 'Create a standalone Windows version that does not require a user to install python first')
        booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_X86_64', defaultValue: false, description: 'Create a standalone version for MacOS X86_64 (m1) machines')
        booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_ARM64', defaultValue: false, description: 'Create a standalone version for MacOS ARM64 (Intel) machines')
        booleanParam(name: 'DEPLOY_STANDALONE_PACKAGERS', defaultValue: false, description: 'Deploy standalone packages')
    }
    stages {
        stage('Build and Test'){
            agent {
                dockerfile {
                    filename 'ci/docker/linux/jenkins/Dockerfile'
                    label 'docker && linux'
                }
            }
            when{
                equals expected: true, actual: params.RUN_CHECKS
                beforeAgent true
            }
            stages{
                stage('Setup Testing Environment'){
                    steps{
                        sh(label: 'Create virtual environment', script: 'python3 -m venv venv && venv/bin/pip install uv')
                        sh(
                            label: 'Install dev packages',
                            script: '''. ./venv/bin/activate
                                        uv pip sync requirements-dev.txt
                                    '''
                            )
                        sh(
                            label: 'Install package in development mode',
                            script: '''. ./venv/bin/activate
                                       uv pip install -e .
                                    '''
                            )
                    }
                }
                stage('Run Tests'){
                    parallel{
                        stage('Pytest'){
                            steps{
                                sh(
                                    label: 'Run Pytest',
                                    script: '''. ./venv/bin/activate
                                            coverage run --parallel-mode --source=galatea -m pytest --junitxml=./reports/tests/pytest/pytest-junit.xml
                                            '''
                                )
                            }
                            post{
                                always{
                                    junit(allowEmptyResults: true, testResults: 'reports/tests/pytest/pytest-junit.xml')
                                }
                            }
                        }
                        stage('MyPy'){
                            steps{
                                catchError(buildResult: 'SUCCESS', message: 'MyPy found issues', stageResult: 'UNSTABLE') {
                                    tee('logs/mypy.log'){
                                        sh(label: 'Running MyPy',
                                           script: '. ./venv/bin/activate && mypy -p galatea --html-report reports/mypy/html'
                                        )
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                            }
                        }
                    }
                }
            }
            post{
                always{
                    sh(
                        label: 'Combining coverage data and generating report',
                        script: '''. ./venv/bin/activate
                                  coverage combine
                                  coverage xml -o reports/coverage.xml
                                  coverage html -d reports/coverage
                                  '''
                    )
                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                }
                cleanup{
                    cleanWs(patterns: [
                            [pattern: 'venv/', type: 'INCLUDE'],
                            [pattern: 'logs/', type: 'INCLUDE'],
                            [pattern: 'reports/', type: 'INCLUDE'],
                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                    ])
                }
            }
        }
        stage('Package'){
            stages{
                stage('Python Packages'){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'docker && linux'
                        }
                    }
                    steps{
                        sh(
                            label: 'Package',
                            script: '''python3 -m venv venv && venv/bin/pip install uv
                                       . ./venv/bin/activate
                                       uv pip sync requirements-dev.txt
                                       python -m build
                                    '''
                        )
                    }
                    post{
                        success{
                            archiveArtifacts artifacts: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', fingerprint: true
                        }
                        cleanup{
                            cleanWs(patterns: [
                                    [pattern: 'venv/', type: 'INCLUDE'],
                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                            ])
                        }
                    }
                }
                stage('Standalone'){
                    when{
                        anyOf{
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                            equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                        }
                    }
                    parallel{
                        stage('Mac Application x86_64'){
                            agent{
                                label 'mac && python3.11 && x86_64'
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                                beforeAgent true
                            }
                            steps{
                                sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'APPLE_APPLICATION_X86_64'
                                    script{
                                        standaloneVersions << 'APPLE_APPLICATION_X86_64'
                                    }
                                }
                                cleanup{
                                    cleanWs(patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ])
                                }
                            }
                        }
                        stage('Mac Application Bundle arm64'){
                            agent{
                                label 'mac && python3.11 && arm64'
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                beforeAgent true
                            }
                            steps{
                                sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'APPLE_APPLICATION_ARM64'
                                    script{
                                        standaloneVersions << 'APPLE_APPLICATION_ARM64'
                                    }
                                }
                                cleanup{
                                    cleanWs(patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ])
                                }
                            }
                        }
                        stage('Windows Application'){
                            agent{
                                docker{
                                    image 'python'
                                    label 'windows && docker && x86_64'
                                }
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                beforeAgent true
                            }
                            steps{
                                bat(script: '''set UV_INDEX_STRATEGY=unsafe-best-match
                                               contrib/create_windows_distrib.bat
                                               '''
                               )
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'WINDOWS_APPLICATION_X86_64'
                                    script{
                                        standaloneVersions << 'WINDOWS_APPLICATION_X86_64'
                                    }
                                }
                                cleanup{
                                    cleanWs(patterns: [
                                        [pattern: 'venv/', type: 'INCLUDE'],
                                        [pattern: 'dist/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                    ])
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Deploy Standalone'){
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_STANDALONE_PACKAGERS
                    anyOf{
                        equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                        equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                        equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                    }
                }
                beforeAgent true
                beforeInput true
            }
            input {
                message 'Upload to Nexus server?'
                parameters {
                    credentials credentialType: 'com.cloudbees.plugins.credentials.common.StandardCredentials', defaultValue: 'jenkins-nexus', name: 'NEXUS_CREDS', required: true
                    choice(
                        choices: getStandAloneStorageServers(),
                        description: 'Url to upload artifact.',
                        name: 'SERVER_URL'
                    )
                    string defaultValue: "galatea/${get_version()}", description: 'subdirectory to store artifact', name: 'archiveFolder'
                }
            }
            stages{
                stage('Deploy Standalone Applications'){
                    agent any
                    steps{
                        script{
                            standaloneVersions.each{
                                unstash "${it}"
                            }
                            deployStandalone("dist/*.zip", "${SERVER_URL}/${archiveFolder}")
                        }
                    }
                }
            }
        }
    }
}