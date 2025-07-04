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

def createChocolateyConfigFile(configJsonFile, installerPackage, url){
    def deployJsonMetadata = [
        "PackageVersion": readTOML( file: 'pyproject.toml')['project'].version,
        "DownloadUrl": url,
        "PackageFile": installerPackage.name,
        "Sha256": sha256(installerPackage.path),
        "TabCompletionPowershellModule": "${installerPackage.name.take(installerPackage.name.lastIndexOf('.'))}\\extras\\cli_completion\\powershell\\GalateaArgumentCompleter.psm1"

    ]
    writeJSON( json: deployJsonMetadata, file: configJsonFile, pretty: 2)
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

def deploySingleStandalone(file, url, authentication) {
    script{
        try{
            def encodedUrlFileName = new URI(null, null, file.name, null).toASCIIString()
            def newUrl = "${url}/${encodedUrlFileName}"
            def putResponse = httpRequest authentication: authentication, httpMode: 'PUT', uploadFile: file.path, url: "${newUrl}", wrapAsMultipart: false
            return newUrl
        } catch(Exception e){
            echo "${e}"
            throw e;
        }
    }
}

def getToxEnvs(){
    node('docker && windows'){
        docker.image('python').inside("--mount type=volume,source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR}"){
            try{
                checkout scm
                bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                return bat(
                    label: 'Get tox environments',
                    script: '@.\\venv\\Scripts\\uvx --constraint=requirements-dev.txt --quiet --with tox-uv tox list -d --no-desc',
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


def start(){
}
def shouldRun(params){
    script{
        return params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]
    }
}
def call(){
    library(
        identifier: 'JenkinsPythonHelperLibrary@2024.12.0',
        retriever: modernSCM(
            [
                $class: 'GitSCMSource',
                remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git'
            ]
        )
    )
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
                                label 'docker && linux && x86_64'
                                args '--mount source=python-tmp-galatea,target=/tmp'
                            }
                        }
                        stages{
                            stage('Setup ci Environment'){
                                steps{
                                    sh(
                                        label: 'Create virtual environment',
                                        script: '''python3 -m venv bootstrap_uv
                                                   bootstrap_uv/bin/pip install --disable-pip-version-check uv
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
                            stage('Build Documentation'){
                                steps{
                                    catchError(buildResult: 'UNSTABLE', message: 'Sphinx has warnings', stageResult: 'UNSTABLE') {
                                        sh '''. ./venv/bin/activate
                                              python -m sphinx --builder=html -W --keep-going -w logs/build_sphinx_html.log -d build/docs/.doctrees docs dist/docs/html
                                           '''
                                   }
                                }
                                post{
                                    success{
                                        publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'dist/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                                        script{
                                            def props = readTOML( file: 'pyproject.toml')['project']
                                            zip archive: true, dir: 'dist/docs/html', glob: '', zipFile: "dist/${props.name}-${props.version}.doc.zip"
                                        }
                                    }
                                    always{
                                        recordIssues(tools: [sphinxBuild(pattern: 'logs/build_sphinx_html.log')])
                                    }
                                }
                            }
                            stage('Test Code'){
                                when{
                                    equals expected: true, actual: params.RUN_CHECKS
                                    beforeAgent true
                                }
                                stages{
                                    stage('Run Tests'){
                                        parallel{
                                            stage('Documentation linkcheck'){
                                                steps {
                                                    catchError(buildResult: 'SUCCESS', message: 'Sphinx docs linkcheck', stageResult: 'UNSTABLE') {
                                                        sh(
                                                            label: 'Running Sphinx docs linkcheck',
                                                            script: '''. ./venv/bin/activate
                                                                       python -m sphinx -b doctest docs/ build/docs -d build/docs/doctrees --no-color --builder=linkcheck --fail-on-warning
                                                                       '''
                                                            )
                                                    }
                                                }
                                            }
                                            stage('Documentation Doctest'){
                                                steps {
                                                    sh(
                                                        label: 'Running Doctest Tests',
                                                        script: '''. ./venv/bin/activate
                                                                   coverage run --parallel-mode --source=src -m sphinx -b doctest docs/ dist/docs/html -d build/docs/doctrees --no-color -w logs/doctest.txt
                                                                '''
                                                        )
                                                }
                                                post{
                                                    always {
                                                        recordIssues(tools: [sphinxBuild(id: 'doctest', name: 'Doctest', pattern: 'logs/doctest.txt')])
                                                    }
                                                }
                                            }
                                            stage('Pytest'){
                                                steps{
                                                    sh(
                                                        label: 'Run Pytest',
                                                        script: '''. ./venv/bin/activate
                                                                coverage run --parallel-mode --source=src -m pytest --junitxml=./reports/tests/pytest/pytest-junit.xml
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
                                            milestone ordinal: 1, label: 'sonarcloud'
                                            withSonarQubeEnv(installationName: 'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                                sh(
                                                    label: 'Running Sonar Scanner',
                                                    script: "./venv/bin/uvx pysonar-scanner -Dsonar.projectVersion=${env.VERSION} -Dsonar.python.xunit.reportPath=./reports/tests/pytest/pytest-junit.xml -Dsonar.python.coverage.reportPaths=./reports/coverage.xml -Dsonar.python.ruff.reportPaths=./reports/ruffoutput.json -Dsonar.python.mypy.reportPaths=./logs/mypy.log ${env.CHANGE_ID ? '-Dsonar.pullrequest.key=$CHANGE_ID -Dsonar.pullrequest.base=$BRANCH_NAME' : '-Dsonar.branch.name=$BRANCH_NAME' }",
                                                )
                                            }
                                            script{
                                                timeout(time: 1, unit: 'HOURS') {
                                                    def sonarqubeResult = waitForQualityGate(abortPipeline: false, credentialsId: params.SONARCLOUD_TOKEN)
                                                    if (sonarqubeResult.status != 'OK') {
                                                       unstable "SonarQube quality gate: ${sonarqubeResult.status}"
                                                   }
                                                }
                                            }
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
                                            try{
                                                checkout scm
                                                docker.image('python').inside('--mount source=python-tmp-galatea,target=/tmp'){
                                                    sh(script: 'python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv')
                                                    envs = sh(
                                                        label: 'Get tox environments',
                                                        script: './venv/bin/uvx --quiet --constraint=requirements-dev.txt --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\n')
                                                }
                                            } finally{
                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && linux'){
                                                            try{
                                                                checkout scm
                                                                docker.image('python').inside('--mount source=python-tmp-galatea,target=/tmp'){
                                                                    try{
                                                                        retry(3){
                                                                            sh( label: 'Running Tox',
                                                                                script: """python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                                                           . ./venv/bin/activate
                                                                                           uv python install cpython-${version}
                                                                                           uvx -p ${version} --constraint=requirements-dev.txt --with tox-uv tox run -e ${toxEnv}
                                                                                        """
                                                                                )
                                                                        }
                                                                    } catch(e) {
                                                                        if (fileExists('./venv/bin/activate')) {
                                                                            sh(script: '''. ./venv/bin/activate
                                                                                  uv python list
                                                                                  '''
                                                                                    )
                                                                        }
                                                                        throw e
                                                                    }
                                                                }
                                                            } finally{
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
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
                                    PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\pipcache'
                                    UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvtools'
                                    UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvpython'
                                    UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                }
                                steps{
                                    script{
                                        def envs = []
                                        node('docker && windows'){
                                            try{
                                                checkout scm
                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                    .inside("\
                                                        --mount type=volume,source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} \
                                                        --mount type=volume,source=pipcache,target=${env.PIP_CACHE_DIR} \
                                                        --mount type=volume,source=uv_cache_dir,target=${env.UV_CACHE_DIR}\
                                                        "
                                                    ){
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uvx --quiet --constraint=requirements-dev.txt --with tox-uv tox list -d --no-desc',
                                                        returnStdout: true,
                                                    ).trim().split('\r\n')
                                                }
                                            } finally{
                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                            }
                                        }
                                        parallel(
                                            envs.collectEntries{toxEnv ->
                                                def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                                [
                                                    "Tox Environment: ${toxEnv}",
                                                    {
                                                        node('docker && windows'){
                                                            checkout scm
                                                            try{
                                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                                    .inside("\
                                                                        --mount type=volume,source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} \
                                                                        --mount type=volume,source=pipcache,target=${env.PIP_CACHE_DIR} \
                                                                        --mount type=volume,source=uv_cache_dir,target=${env.UV_CACHE_DIR} \
                                                                        "
                                                                    ){
                                                                    bat(label: 'Install uv',
                                                                        script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv'
                                                                    )
                                                                    retry(3){
                                                                        bat(label: 'Running Tox',
                                                                            script: """venv\\Scripts\\uv python install cpython-${version}
                                                                                       venv\\Scripts\\uvx -p ${version} --constraint=requirements-dev.txt --with tox-uv tox run -e ${toxEnv}
                                                                                    """
                                                                        )
                                                                    }
                                                                }
                                                            } finally{
                                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
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
                                        script: '''python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                   . ./venv/bin/activate
                                                   uv build --build-constraints requirements-dev.txt
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
                            stage('Testing Packages'){
                                when{
                                    equals expected: true, actual: params.TEST_PACKAGES
                                }
                                environment{
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                }
                                steps{
                                    customMatrix(
                                        axes: [
                                            [
                                                name: 'PYTHON_VERSION',
                                                values: ['3.10', '3.11', '3.12','3.13']
                                            ],
                                            [
                                                name: 'OS',
                                                values: ['linux','macos','windows']
                                            ],
                                            [
                                                name: 'ARCHITECTURE',
                                                values: ['x86_64', 'arm64']
                                            ],
                                            [
                                                name: 'PACKAGE_TYPE',
                                                values: ['wheel', 'sdist'],
                                            ]
                                        ],
                                        excludes: [
                                            [
                                                [
                                                    name: 'OS',
                                                    values: 'windows'
                                                ],
                                                [
                                                    name: 'ARCHITECTURE',
                                                    values: 'arm64',
                                                ]
                                            ]
                                        ],
                                        when: {entry -> "INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase() && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]},
                                        stages: [
                                            { entry ->
                                                stage('Test Package') {
                                                    node("${entry.OS} && ${entry.ARCHITECTURE} ${['linux', 'windows'].contains(entry.OS) ? '&& docker': ''}"){
                                                        try{
                                                            checkout scm
                                                            unstash 'PYTHON_PACKAGES'
                                                            if(['linux', 'windows'].contains(entry.OS) && params.containsKey("INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]){
                                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                                    .inside(
                                                                        isUnix() ?
                                                                        '--mount source=python-tmp-galatea,target=/tmp' :
                                                                        '--mount type=volume,source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython \
                                                                         --mount type=volume,source=pipcache,target=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache \
                                                                         --mount type=volume,source=uv_cache_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                                                    ){
                                                                     if(isUnix()){
                                                                        withEnv([
                                                                            'PIP_CACHE_DIR=/tmp/pipcache',
                                                                            'UV_TOOL_DIR=/tmp/uvtools',
                                                                            'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                                            'UV_CACHE_DIR=/tmp/uvcache',
                                                                        ]){
                                                                             sh(
                                                                                label: 'Testing with tox',
                                                                                script: """python3 -m venv venv
                                                                                           ./venv/bin/pip install --disable-pip-version-check uv
                                                                                           ./venv/bin/uv python install cpython-${entry.PYTHON_VERSION}
                                                                                           ./venv/bin/uvx --constraint=requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                        """
                                                                            )
                                                                        }
                                                                     } else {
                                                                        withEnv([
                                                                            'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                                                                            'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvtools',
                                                                            'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                                                                            'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                                                                        ]){
                                                                            bat(
                                                                                label: 'Testing with tox',
                                                                                script: """python -m venv venv
                                                                                           .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                           .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                           .\\venv\\Scripts\\uvx --constraint=requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                        """
                                                                            )
                                                                        }
                                                                     }
                                                                }
                                                            } else {
                                                                if(isUnix()){
                                                                    sh(
                                                                        label: 'Testing with tox',
                                                                        script: """python3 -m venv venv
                                                                                   ./venv/bin/pip install --disable-pip-version-check uv
                                                                                   ./venv/bin/uvx --constraint=requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                """
                                                                    )
                                                                } else {
                                                                    bat(
                                                                        label: 'Testing with tox',
                                                                        script: """python -m venv venv
                                                                                   .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                   .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                   .\\venv\\Scripts\\uvx --constraint=requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                """
                                                                    )
                                                                }
                                                            }
                                                        } finally{
                                                            if(isUnix()){
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            } else {
                                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    )
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
                                when{
                                    equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                                    beforeAgent true
                                }
                                stages{
                                    stage('Package'){
                                        agent{
                                            label 'mac && python3.11 && x86_64'
                                        }
                                        steps{
                                            sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                                        }
                                        post{
                                            success{
                                                archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
                                                stash includes: 'dist/*.tar.gz', name: 'APPLE_APPLICATION_X86_64'
                                            }
                                            cleanup{
                                                cleanWs(patterns: [
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                ])
                                            }
                                        }
                                    }
                                    stage('Test'){
                                        agent{
                                            label 'mac && x86_64'
                                        }
                                        options {
                                            skipDefaultCheckout true
                                        }
                                        steps{
                                            unstash 'APPLE_APPLICATION_X86_64'
                                            untar(file: "${findFiles(glob: 'dist/*.tar.gz')[0]}", dir: 'dist/out')
                                            sh "${findFiles(glob: 'dist/out/**/galatea')[0].path} --version"
                                        }
                                        post{
                                            cleanup{
                                               cleanWs(
                                                     deleteDirs: true,
                                                     patterns: [
                                                         [pattern: 'dist/', type: 'INCLUDE'],
                                                     ]
                                                 )
                                            }
                                        }
                                    }
                                }
                            }
                            stage('Mac Application arm64'){
                                when{
                                    equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                    beforeAgent true
                                }
                                stages{
                                    stage('Package'){
                                        agent{
                                            label 'mac && python3.11 && arm64'
                                        }
                                        steps{
                                            sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                                        }
                                        post{
                                            success{
                                                archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
                                                stash includes: 'dist/*.tar.gz', name: 'APPLE_APPLICATION_ARM64'
                                            }
                                            cleanup{
                                                cleanWs(patterns: [
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                ])
                                            }
                                        }
                                    }
                                    stage('Test'){
                                        agent{
                                            label 'mac && arm64'
                                        }
                                        options {
                                            skipDefaultCheckout true
                                        }
                                        steps{
                                            unstash 'APPLE_APPLICATION_ARM64'
                                            untar(file: "${findFiles(glob: 'dist/*.tar.gz')[0]}", dir: 'dist/out')
                                            sh "${findFiles(glob: 'dist/out/**/galatea')[0].path} --version"
                                        }
                                        post{
                                            cleanup{
                                               cleanWs(
                                                     deleteDirs: true,
                                                     patterns: [
                                                         [pattern: 'dist/', type: 'INCLUDE'],
                                                     ]
                                                 )
                                            }
                                        }
                                    }
                                }
                            }
                            stage('Windows Application'){
                                when{
                                    equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                    beforeAgent true
                                }
                                stages{
                                    stage('Package'){
                                        agent{
                                            docker{
                                                image 'python'
                                                label 'windows && docker && x86_64'
                                            }
                                        }
                                        environment{
                                            UV_INDEX_STRATEGY='unsafe-best-match'
                                        }
                                        steps{
                                            tee('reports/windows_cpack.log'){
                                                bat(script: 'contrib/create_windows_distrib.bat')
                                            }
                                            archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                            stash includes: 'dist/*.zip', name: 'WINDOWS_APPLICATION_X86_64'
                                        }
                                        post{
                                            always{
                                                recordIssues(
                                                        sourceCodeRetention: 'LAST_BUILD',
                                                        tools: [
                                                            cmake(
                                                                name: 'CMake warnings when packaging standalone for Windows',
                                                                pattern: 'reports/windows_cpack.log'
                                                            )
                                                        ]
                                                    )
                                            }
                                            cleanup{
                                                cleanWs(patterns: [
                                                    [pattern: 'reports/', type: 'INCLUDE'],
                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                ])
                                            }
                                        }
                                    }
                                    stage('Test package'){
                                        agent {
                                            docker {
                                                image 'mcr.microsoft.com/windows/servercore:ltsc2025'
                                                label 'windows && docker && x86_64'
                                            }
                                        }
                                        options {
                                            skipDefaultCheckout true
                                        }
                                        steps{
                                            unstash 'WINDOWS_APPLICATION_X86_64'
                                            unzip(zipFile: "${findFiles(glob: 'dist/*.zip')[0]}", dir: 'dist/galatea')
                                            bat "${findFiles(glob: 'dist/galatea/**/galatea.exe')[0]} --version"
                                        }
                                        post{
                                            cleanup{
                                                cleanWs(
                                                    deleteDirs: true,
                                                    patterns: [
                                                        [pattern: 'dist/', type: 'INCLUDE'],
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
                parallel{
                    stage('Deploy Standalone Applications: Windows x86_64'){
                        agent any
                        when{
                            equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                            beforeAgent true
                        }
                        environment{
                            GENERATED_CHOCOLATEY_CONFIG_FILE='dist/chocolatey/config.json'
                        }
                        steps{
                            script{
                                unstash 'WINDOWS_APPLICATION_X86_64'
                                def deploymentFile = findFiles(glob: 'dist/*.zip')[0]
                                def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                createChocolateyConfigFile(env.GENERATED_CHOCOLATEY_CONFIG_FILE, deploymentFile, deployedUrl)
                                archiveArtifacts artifacts: env.GENERATED_CHOCOLATEY_CONFIG_FILE
                                echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                            }
                        }
                        post{
                            success{
                                echo "Use ${env.GENERATED_CHOCOLATEY_CONFIG_FILE} for deploying to Chocolatey with https://github.com/UIUCLibrary/chocolatey-hosted-public.git. Found in the artifacts for this build."
                                echo "${readFile(env.GENERATED_CHOCOLATEY_CONFIG_FILE)}"
                            }
                        }
                    }
                    stage('Deploy Standalone Applications: MacOS ARM64'){
                        agent any
                        when{
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                            beforeAgent true
                        }
                        steps{
                            script{
                                unstash 'APPLE_APPLICATION_ARM64'
                                def deploymentFile = findFiles(glob: 'dist/*.tar.gz')[0]
                                def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                            }
                        }
                    }
                    stage('Deploy Standalone Applications: MacOS X86_64'){
                        agent any
                        when{
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                            beforeAgent true
                        }
                        steps{
                            script{
                                unstash 'APPLE_APPLICATION_X86_64'
                                def deploymentFile = findFiles(glob: 'dist/*.tar.gz')[0]
                                def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                            }
                        }
                    }
                }
            }
        }
    }
}
