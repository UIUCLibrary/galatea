pipeline {
    agent none
    parameters{
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
    }
}