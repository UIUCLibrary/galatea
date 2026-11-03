def testMacStandalonePackage(Map args = [:]) {
    def tarball = args.tarball
    if(!tarball){
        error "tarball is required"
    }
    try{
        sh "contrib/test-apple-package.sh ${tarball}"
    } finally{
        if(fileExists('.git')){
            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
        } else {
            cleanWs(
                patterns: [
                    [pattern: 'dist/', type: 'INCLUDE'],
                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                ],
                notFailBuild: true
            )
        }
    }
}
return this