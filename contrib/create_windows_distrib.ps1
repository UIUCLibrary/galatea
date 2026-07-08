param (
    [Parameter(mandatory=$true)]
    [string]$Wheel,
    [string]$uvExec,
    [string]$PythonVersion,
    [string]$BuildPath = $(Join-Path -Path $PWD -ChildPath "build")

)
$ErrorActionPreference = 'Stop'

function Get-UV() {
    [CmdletBinding()]
    param (
        [Parameter(mandatory=$true)]
        [string]$buildPath
    )
    $uvExec = (Get-Command uv -ErrorAction SilentlyContinue)
    if($uvExec){
        return $uvExec.Source
    }

    Write-Host $buildPath
    py -m venv $buildPath\venv --clear
    & "$buildPath\venv\Scripts\pip.exe" --disable-pip-version-check install uv | Out-Null
    return Join-Path "$buildPath" -ChildPath "venv\Scripts\uv.exe"

}

function Build-Standalone{
    [CmdletBinding()]
    param (
        [Parameter(mandatory=$true)]
        [string]$Uv,
        [Parameter(mandatory=$true)]
        [string]$Wheel,
        [string]$PythonVersion,
        [Parameter(mandatory=$true)]
        [string]$BuildPath
    )
    Write-Host "Build-Standalone"
    $fullPath = Join-Path -Path $BuildPath -ChildPath "package"

    if (-not (Test-Path -Path $fullPath -PathType Container)) {
        New-Item -ItemType Directory -Path $fullPath -Force  | Out-Null
    }
    & "$Uv" export --python="$PythonVersion" --frozen --no-dev --no-emit-project --no-annotate --no-header --group freeze --format pylock.toml --extra gui --output-file "${fullPath}\pylock.toml"  | Out-Null
    &{
        # Prepend the PATH variable with location of the uv executable so that --package-manager=uv is accessible.
        # The reason for this is that the "uv" option for --package-manager in create_standalone.py is only valid if uv
        # in on the PATH environment variable.
        $env:PATH = "$((Get-ChildItem -Path (Resolve-Path "$Uv").Path).DirectoryName);$env:PATH"
        $local:process = Start-Process -FilePath "$Uv" -ArgumentList "run", "--python=$PythonVersion","contrib\create_standalone.py","--package-manager=uv","--include-tab-completions","--requirements", "`"${fullPath}\pylock.toml`"", "`"${Wheel}`"", "galatea", "--cli-entrypoint=./contrib/bootstrap_standalone_cli.py",  "--gui-entrypoint=./contrib/bootstrap_standalone_gui.py", "--build","`"$fullPath`"" -Wait -NoNewWindow -PassThru
        if ($process.ExitCode -ne 0) {
            Write-Host "Failed to build standalone"
            exit $process.ExitCode
        }
    }
}

# ====== Main starting =============

$buildpath = Join-Path -Path $BuildPath -ChildPath "galatea_build"
if (-not (Test-Path -Path $buildpath -PathType Container)) {
    New-Item -ItemType Directory -Path $buildpath | Out-Null
}
if (-not $uvExec){
    $uvExec = Get-UV $buildpath
}
Build-Standalone -Uv "$uvExec" -Wheel "$Wheel" -PythonVersion "$PythonVersion" -BuildPath "$buildpath"
