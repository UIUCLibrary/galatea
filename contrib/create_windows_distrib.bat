@echo off
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

set TEMP_DIR=%TEMP%\galatea_build
if not exist "%TEMP_DIR%" (
    mkdir "%TEMP_DIR%"
)

set REQUIREMENTS_FILE=%TEMP_DIR%\requirements.txt
set DEV_REQUIREMENTS_FILE=%TEMP_DIR%\requirements-dev.txt


py -m venv venv
venv\Scripts\pip install uv --disable-pip-version-check

venv\Scripts\uv export --frozen --only-group dev --no-hashes --format requirements.txt --no-emit-project --no-annotate > %DEV_REQUIREMENTS_FILE%
REM Generates the galatea.egg-info needed for the version metadata
venv\Scripts\uv build --build-constraints %DEV_REQUIREMENTS_FILE% --wheel

venv\Scripts\uv export --frozen --format requirements.txt --no-dev --no-emit-project --no-annotate > %REQUIREMENTS_FILE%
venv\Scripts\uv run --with-requirements %REQUIREMENTS_FILE% %SCRIPT_DIR%\create_standalone.py --include-tab-completions galatea ./contrib/bootstrap_standalone.py
