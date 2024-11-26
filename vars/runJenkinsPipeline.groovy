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

def getToxEnvs(){
    node('docker && windows'){
        docker.image('python').inside('--mount source=python-tmp-galatea,target=C:\\Users\\ContainerUser\\Documents'){
            try{
                checkout scm
                bat(script: 'python -m venv venv && venv\\Scripts\\pip install uv')
                return bat(
                    label: 'Get tox environments',
                    script: '@.\\venv\\Scripts\\uvx --quiet --with tox-uv tox list -d --no-desc',
                    returnStdout: true,
                ).trim().split('\r\n')
            } finally{
                cleanWs(
                    patterns: [
                        [pattern: 'venv/', type: 'INCLUDE'],
                        [pattern: '.tox', type: 'INCLUDE'],
                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                    ]
                )
            }
        }
    }
}

def get_version(){
    node(){
        checkout scm
        return readTOML( file: 'pyproject.toml')['project'].version
    }
}

standaloneVersions = []
def start(){
}
def shouldRun(params){
    script{
        return params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]
    }
}
def call(){
    pipeline {
        agent none
        parameters{
            booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
            booleanParam(name: 'USE_SONARQUBE', defaultValue: true, description: 'Send data test data to SonarQube')
            credentials(name: 'SONARCLOUD_TOKEN', credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl', defaultValue: 'sonarcloud_token', required: false)
            booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
            booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
            booleanParam(name: 'TEST_PACKAGES', defaultValue: false, description: 'Test packages')
            booleanParam(name: 'INCLUDE_LINUX-X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
            booleanParam(name: 'INCLUDE_LINUX-ARM64', defaultValue: false, description: 'Include ARM architecture for Linux')
            booleanParam(name: 'INCLUDE_MACOS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
            booleanParam(name: 'INCLUDE_MACOS-ARM64', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
            booleanParam(name: 'INCLUDE_WINDOWS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Windows')
            booleanParam(name: 'PACKAGE_STANDALONE_WINDOWS_INSTALLER', defaultValue: false, description: 'Create a standalone Windows version that does not require a user to install python first')
            booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_X86_64', defaultValue: false, description: 'Create a standalone version for MacOS X86_64 (m1) machines')
            booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_ARM64', defaultValue: false, description: 'Create a standalone version for MacOS ARM64 (Intel) machines')
            booleanParam(name: 'DEPLOY_STANDALONE_PACKAGERS', defaultValue: false, description: 'Deploy standalone packages')
        }
        stages {
            stage('Testing'){
                stages{
                    stage('Build and Test'){
                        environment{
                            PIP_CACHE_DIR='/tmp/pipcache'
                            UV_INDEX_STRATEGY='unsafe-best-match'
                            UV_TOOL_DIR='/tmp/uvtools'
                            UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                            UV_CACHE_DIR='/tmp/uvcache'
                        }
                        agent {
                            docker{
                                image 'python'
                                label 'docker && linux'
                                args '--mount source=python-tmp-galatea,target=/tmp'
                            }
                        }
                        when{
                            equals expected: true, actual: params.RUN_CHECKS
                            beforeAgent true
                        }
                        stages{
                            stage('Setup Testing Environment'){
                                steps{
                                    sh(
                                        label: 'Create virtual environment',
                                        script: '''python3 -m venv bootstrap_uv
                                                   bootstrap_uv/bin/pip install uv
                                                   bootstrap_uv/bin/uv venv --python 3.11  venv
                                                   . ./venv/bin/activate
                                                   bootstrap_uv/bin/uv pip install uv
                                                   rm -rf bootstrap_uv
                                                   uv pip install -r requirements-dev.txt
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
                                    stage('Ruff') {
                                        steps{
                                            catchError(buildResult: 'SUCCESS', message: 'Ruff found issues', stageResult: 'UNSTABLE') {
                                                sh(
                                                 label: 'Running Ruff',
                                                 script: '''. ./venv/bin/activate
                                                            ruff check --config=pyproject.toml -o reports/ruffoutput.txt --output-format pylint --exit-zero
                                                            ruff check --config=pyproject.toml -o reports/ruffoutput.json --output-format json
                                                        '''
                                                 )
                                            }
                                        }
                                        post{
                                            always{
                                                recordIssues(tools: [pyLint(pattern: 'reports/ruffoutput.txt', name: 'Ruff')])
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
                                }
                            }
                            stage('Submit results to SonarQube'){
                                options{
                                    lock('galatea-sonarscanner')
                                }
                                environment{
                                    VERSION="${readTOML( file: 'pyproject.toml')['project'].version}"
                                }
                                when{
                                    allOf{
                                        equals expected: true, actual: params.USE_SONARQUBE
                                        expression{
                                            try{
                                                withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: 'dddd')]) {
                                                    echo 'Found credentials for sonarqube'
                                                }
                                            } catch(e){
                                                return false
                                            }
                                            return true
                                        }
                                    }
                                }
                                steps{
                                    withSonarQubeEnv(installationName: 'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                        script{
                                            def sourceInstruction
                                            if (env.CHANGE_ID){
                                                sourceInstruction = "-Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.BRANCH_NAME}"
                                            } else{
                                                sourceInstruction = "-Dsonar.branch.name=${env.BRANCH_NAME}"
                                            }
                                            sh(
                                                label: 'Running Sonar Scanner',
                                                script: """. ./venv/bin/activate
                                                            uvx pysonar-scanner -Dsonar.projectVersion=${env.VERSION} -Dsonar.python.xunit.reportPath=./reports/tests/pytest/pytest-junit.xml -Dsonar.python.coverage.reportPaths=./reports/coverage.xml -Dsonar.python.ruff.reportPaths=./reports/ruffoutput.json -Dsonar.python.mypy.reportPaths=./logs/mypy.log ${sourceInstruction}
                                                        """
                                            )
                                        }
                                    }
                                }
                            }
                        }
                        post{
                            cleanup{
                                cleanWs(patterns: [
                                        [pattern: 'uv/', type: 'INCLUDE'],
                                        [pattern: 'venv/', type: 'INCLUDE'],
                                        [pattern: 'logs/', type: 'INCLUDE'],
                                        [pattern: 'reports/', type: 'INCLUDE'],
                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                ])
                            }
                        }
                    }
                    stage('Tox'){
                        when {
                           equals expected: true, actual: params.TEST_RUN_TOX
                        }
                        parallel{
                            stage('Linux'){
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    UV_TOOL_DIR='/tmp/uvtools'
                                    UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && linux'){
                                            docker.image('python').inside('--mount source=python-tmp-galatea,target=/tmp'){
                                                try{
                                                    checkout scm
                                                    sh(script: 'python3 -m venv venv && venv/bin/pip install uv')
                                                    envs = sh(
                                                        label: 'Get tox environments',
                                                        script: './venv/bin/uvx --quiet --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\n')
                                                } finally{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && linux'){
                                                            docker.image('python').inside('--mount source=python-tmp-galatea,target=/tmp'){
                                                                checkout scm
                                                                try{
                                                                    sh( label: 'Running Tox',
                                                                        script: """python3 -m venv venv && venv/bin/pip install uv
                                                                                   . ./venv/bin/activate
                                                                                   uv python install cpython-${version}
                                                                                   uvx -p ${version} --with tox-uv tox run -e ${toxEnv}
                                                                                """
                                                                        )
                                                                } catch(e) {
                                                                    sh(script: '''. ./venv/bin/activate
                                                                          uv python list
                                                                          '''
                                                                            )
                                                                    throw e
                                                                } finally{
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ]
                                                                    )
                                                                }
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        )
                                    }
                                }
                            }
                            stage('Windows'){
                                when{
                                    expression {return nodesByLabel('windows && docker && x86').size() > 0}
                                }
                                environment{
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\pipcache'
                                    UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\uvtools'
                                    UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                                    UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\uvcache'
                                }
                                steps{
                                    script{
    //                                    def envs = getToxEnvs()
                                        def envs = []
                                        node('docker && windows'){
                                            docker.image('python').inside('--mount source=python-tmp-galatea,target=C:\\Users\\ContainerUser\\Documents'){
                                                try{
                                                    checkout scm
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uvx --quiet --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\r\n')
                                                } finally{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && windows'){
                                                            docker.image('python').inside('--mount source=python-tmp-galatea,target=C:\\Users\\ContainerUser\\Documents'){
                                                                checkout scm
                                                                try{
                                                                    bat(label: 'Install uv',
                                                                        script: 'python -m venv venv && venv\\Scripts\\pip install uv'
                                                                    )
                                                                    retry(3){
                                                                        bat(label: 'Running Tox',
                                                                            script: """call venv\\Scripts\\activate.bat
                                                                                   uv python install cpython-${version}
                                                                                   uvx -p ${version} --with tox-uv tox run -e ${toxEnv}
                                                                                """
                                                                        )
                                                                    }
                                                                } finally{
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ]
                                                                    )
                                                                }
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
            stage('Package'){
                stages{
                    stage('Python Packages'){
                        when{
                            equals expected: true, actual: params.BUILD_PACKAGES
                        }
                        stages{
                            stage('Create Python Packages'){
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                agent {
                                    docker {
                                        image 'python'
                                        label 'docker && linux'
                                        args '--mount source=python-tmp-galatea,target=/tmp'
                                    }
                                }
                                steps{
                                    sh(
                                        label: 'Package',
                                        script: '''python3 -m venv venv && venv/bin/pip install uv
                                                   . ./venv/bin/activate
                                                   uv build
                                                '''
                                    )
                                }
                                post{
                                    success{
                                        archiveArtifacts artifacts: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', fingerprint: true
                                        stash includes: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', name: 'PYTHON_PACKAGES'
                                    }
                                    cleanup{
                                        cleanWs(patterns: [
                                                [pattern: 'venv/', type: 'INCLUDE'],
                                                [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ])
                                    }
                                }
                            }
                            stage('Testing packages'){
                                when{
                                    equals expected: true, actual: params.TEST_PACKAGES
                                }
                                matrix {
                                    axes {
                                        axis {
                                            name 'PYTHON_VERSION'
                                            values '3.10','3.11','3.12','3.13'
                                        }
                                        axis {
                                            name 'OS'
                                            values 'linux','macos','windows'
                                        }
                                        axis {
                                            name 'ARCHITECTURE'
                                            values 'x86_64', 'arm64'
                                        }
                                        axis {
                                            name 'PACKAGE_TYPE'
                                            values 'wheel', 'sdist'
                                        }
                                    }
                                    excludes {
                                        exclude {
                                            axis {
                                                name 'OS'
                                                values 'windows'
                                            }
                                            axis {
                                                name 'ARCHITECTURE'
                                                values 'arm64'
                                            }
                                        }
                                    }
                                    when{
                                        equals expected: true, actual: params.TEST_PACKAGES
    //                                    expression{
    //                                        shouldRun(params)
    //                                    }
    //                                    beforeAgent true
                                    }
                                    stages {
                                        stage('Test Package in container') {
                                            when{
                                                expression{['linux', 'windows'].contains(OS) && shouldRun(params)}
                                                beforeAgent true
                                            }
                                            agent {
                                                docker {
                                                    image 'python'
                                                    label "${OS} && ${ARCHITECTURE} && docker"
                                                    args "--mount source=python-tmp-galatea,target=${['linux'].contains(OS) ? '/tmp' : 'C:\\Users\\ContainerUser\\Documents'}"
                                                }
                                            }
                                            environment{
                                                PIP_CACHE_DIR="${isUnix() ? '/tmp/pipcache': 'C:\\Users\\ContainerUser\\Documents\\pipcache'}"
                                                UV_INDEX_STRATEGY='unsafe-best-match'
                                                UV_TOOL_DIR="${isUnix() ? '/tmp/uvtools': 'C:\\Users\\ContainerUser\\Documents\\uvtools'}"
                                                UV_PYTHON_INSTALL_DIR="${isUnix() ? '/tmp/uvpython': 'C:\\Users\\ContainerUser\\Documents\\uvpython'}"
                                                UV_CACHE_DIR="${isUnix() ? '/tmp/uvcache': 'C:\\Users\\ContainerUser\\Documents\\uvcache'}"
                                            }
                                            steps {
                                                unstash 'PYTHON_PACKAGES'
                                                script{
                                                    if(isUnix()){
                                                        sh(
                                                            label: 'Testing with tox',
                                                            script: """python3 -m venv venv
                                                                       . ./venv/bin/activate
                                                                       pip install uv
                                                                       UV_INDEX_STRATEGY=unsafe-best-match uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                    } else {
                                                        bat(
                                                            label: 'Testing with tox',
                                                            script: """python -m venv venv
                                                                       .\\venv\\scripts\\activate.bat
                                                                       pip install uv
                                                                       UV_INDEX_STRATEGY=unsafe-best-match uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                    }
                                                }
                                            }
                                            post{
                                                cleanup{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                            ]
                                                    )
                                                }
                                            }
                                        }
                                        stage('Test Package directly on agent') {
                                            when{
                                                expression{['macos'].contains(OS) && shouldRun(params)}
                                                beforeAgent true
                                            }
                                            agent {
                                                label "${OS} && ${ARCHITECTURE}"
                                            }
                                            steps {
                                                script{
                                                        unstash 'PYTHON_PACKAGES'
                                                        sh(
                                                            label: 'Testing with tox',
                                                            script: """python3 -m venv venv
                                                                       . ./venv/bin/activate
                                                                       pip install uv
                                                                       UV_INDEX_STRATEGY=unsafe-best-match uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                }
                                            }
                                            post{
                                                cleanup{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                            ]
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
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
                                deployStandalone('dist/*.zip', "${SERVER_URL}/${archiveFolder}")
                            }
                        }
                    }
                }
            }
        }
    }
}
