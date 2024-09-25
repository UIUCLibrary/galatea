pipeline {
    agent none
    stages {
        stage('Build and Test'){
            agent {
                dockerfile {
                    filename 'ci/docker/linux/jenkins/Dockerfile'
                    label 'docker && linux'
                }
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
                stage('Run tests'){
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
                            [pattern: 'reports/', type: 'INCLUDE'],
                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                    ])
                }
            }
        }
        stage('Package'){
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
    }
}