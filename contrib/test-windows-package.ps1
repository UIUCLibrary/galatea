param (
    [Parameter(mandatory=$true)]
    [string]$packageZip,
    [string]$ExpectedVersion
)

$global:TESTS_SUCCESSFUL=0
$global:TESTS_PERFORMED=0
$global:TESTS_SKIPPED=0
$global:TESTS_FAILED=0

function InstallGalatea(){
    [CmdletBinding()]
    param (
        [Parameter(mandatory=$true)]
        [string]$ZipPackage,
        [Parameter(mandatory=$true)]
        [string]$TestPath
    )
    Expand-Archive -Path "$ZipPackage" -DestinationPath $TestPath -Force
    $TopLevelFolder = Get-ChildItem -Path $TestPath -Directory | Select-Object -First 1
    return Join-Path -Path $TestPath -ChildPath $TopLevelFolder.Name
}

function Run-Tests(){
    [CmdletBinding()]
    param (
        [Parameter(mandatory = $true)]
        [string]$InstallPath,
        [string]$ExpectedVersion
    )
    $pythonExec = (Get-Command python -ErrorAction SilentlyContinue).Source

    Write-Host 'TEST: Galatea cli has a version'
    $global:TESTS_PERFORMED++
    if(! (Test-CanRunVersion -Application $InstallPath\galatea\galatea.exe)){
        $global:TESTS_FAILED++
        Write-Host 'TEST: Galatea cli has a version - failed'

        $global:TESTS_SKIPPED++
        Write-Warning "Skipping version comparison test. Reason: unable to get version information from $InstallPath\galatea\galatea.exe"
    } else {
        $global:TESTS_SUCCESSFUL++
        Write-Host 'TEST: Galatea cli has a version - success'

        if($pythonExec -or $ExpectedVersion){
            Write-Host 'TEST: Galatea cli matched expected version'
            if(! $ExpectedVersion){
                $ExpectedVersion = & $pythonExec -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
            }
            $global:TESTS_PERFORMED++
            if(Test-VersionMatchExpected -Application $InstallPath\galatea\galatea.exe -ExpectedVersion "galatea.exe $ExpectedVersion"){
                $global:TESTS_SUCCESSFUL++
                Write-Host 'TEST: Galatea cli matched expected version - success'
            }else {
                $global:TESTS_FAILED++
                Write-Host 'TEST: Galatea cli matched expected version - failed'
            }
        } else {
            $global:TESTS_SKIPPED++
            Write-Warning "Skipping version comparison test. Reason: python.exe not found"
        }
    }
    Write-Host 'TEST: Galatea gui has a version'
    $global:TESTS_PERFORMED++
    if(! (Test-CanRunVersion -Application $InstallPath\galatea\galatea-gui.exe)){
        $global:TESTS_FAILED++
        Write-Host 'TEST: TEST: Galatea gui has a version - failed'

        $global:TESTS_SKIPPED++
        Write-Warning "Skipping version comparison test. Reason: unable to get version information from $InstallPath\galatea\galatea-gui.exe"
    } else {
        $global:TESTS_SUCCESSFUL++
        Write-Host 'TEST: Galatea gui has a version - success'

        if($pythonExec -or $ExpectedVersion){
            Write-Host 'TEST: Galatea gui matched expected version'
            if(! $ExpectedVersion){
                $ExpectedVersion = & $pythonExec -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
            }
            $global:TESTS_PERFORMED++
            if(Test-VersionMatchExpected -Application $InstallPath\galatea\galatea-gui.exe -ExpectedVersion "galatea-gui.exe $ExpectedVersion"){
                $global:TESTS_SUCCESSFUL++
                Write-Host 'TEST: Galatea gui matched expected version - success'
            }else {
                $global:TESTS_FAILED++
                Write-Host 'TEST: Galatea gui matched expected version - failed'
            }
        } else {
            $global:TESTS_SKIPPED++
            Write-Warning "Skipping version comparison test. Reason: python.exe not found"
        }
    }
}

function Test-VersionMatchExpected(){
    [CmdletBinding()]
    param (
        [Parameter(mandatory = $true)]
        [string]$Application,
        [Parameter(mandatory = $true)]
        [string]$ExpectedVersion
    )
    $local:TestDirectory = Join-Path $env:TEMP ([Guid]::NewGuid().Guid)
    $local:GalateaStdoutFile = Join-Path $local:TestDirectory "galatea_stdout.log"
    $local:GalateaStdErrFile = Join-Path $local:TestDirectory "galatea_stderr.log"

    try{
        $nul = New-Item -ItemType Directory -Path $TestDirectory
        $local:process = Start-Process -FilePath "$Application" -ArgumentList "--version" -Wait -NoNewWindow -PassThru -RedirectStandardOutput "$local:GalateaStdoutFile" -RedirectStandardError "$local:GalateaStdErrFile"
        if ($process.ExitCode -ne 0) {
            $errorText = Get-Content -Path "$local:GalateaStdErrFile" -Raw
            Write-Debug -Message $errorText
            Write-Error "Failed to get version information. $errorText"
            return $false
        }
        $output = Get-Content -Path "$local:GalateaStdoutFile"
        if ($output -like "*$ExpectedVersion*"){
            return $true
        } else {
            Write-Host "Error: version mismatch. ${Application}: `"$output`" (expected: `"${ExpectedVersion}`")"
            return $false
        }
        return $true
    } finally {
        if (Test-Path $local:TestDirectory) {
            Remove-Item -Path $TestDirectory -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    return $false

}

function Test-CanRunVersion(){
    [CmdletBinding()]
    param (
        [Parameter(mandatory = $true)]
        [string]$Application
    )
    $local:TestDirectory = Join-Path $env:TEMP ([Guid]::NewGuid().Guid)
    $nul = New-Item -ItemType Directory -Path $TestDirectory

    $local:GalateaStdoutFile = Join-Path $local:TestDirectory "galatea_stdout.log"
    $local:GalateaStdErrFile = Join-Path $local:TestDirectory "galatea_stderr.log"
    try{
        $local:process = Start-Process -FilePath "$Application" -ArgumentList "--version" -Wait -NoNewWindow -PassThru -RedirectStandardOutput "$local:GalateaStdoutFile" -RedirectStandardError "$local:GalateaStdErrFile"
        if ($process.ExitCode -ne 0) {
            $errorText = Get-Content -Path "$local:GalateaStdErrFile" -Raw
            Write-Debug -Message $errorText
            Write-Error "Failed to get version information. $errorText"
            return $false
        }
        return $true
    } catch {
     return $false
    } finally {
        if (Test-Path $local:TestDirectory) {
            Remove-Item -Path $TestDirectory -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function TestZipPackage(){
    [CmdletBinding()]
    param (
        [Parameter(mandatory=$true)]
        [string]$ZipPackage,
        [Parameter(mandatory=$true)]
        [string]$TestPath,
        [string]$ExpectedVersion
    )
    Write-Host "Installing ${ZipPackage}"
    $installPath = InstallGalatea -ZipPackage $ZipPackage -TestPath $TestPath
    Write-Host "Installed at $installPath"
    Write-Host "Testing ${ZipPackage}"
    Run-Tests -InstallPath $installPath -ExpectedVersion $ExpectedVersion

    Write-Host ""
    Write-Host "Number of tests performed: $TESTS_PERFORMED"
    Write-Host "Number of tests succeed:   $TESTS_SUCCESSFUL"
    Write-Host "Number of tests failed:    $TESTS_FAILED"
    Write-Host "Number of tests skipped:   $TESTS_SKIPPED"
}

Write-Host "Testing $packageZip"

$TestDirectory = Join-Path $env:TEMP ([Guid]::NewGuid().Guid)
try{
    # Install galatea into a temp directory that is cleaned up at end
    $null = New-Item -ItemType Directory -Path $TestDirectory
    TestZipPackage -ZipPackage $packageZip -TestPath $TestDirectory -ExpectedVersion $ExpectedVersion
} finally {
    if (Test-Path $TestDirectory) {
        Write-Host "Cleaning up galatea installation"
        Remove-Item -Path $TestDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
if ($TESTS_FAILED) {
    Write-Host "Some tests failed."
    exit 1
}
Write-Host "Success."
exit 0