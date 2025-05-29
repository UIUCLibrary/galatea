@echo off
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set REQUIREMENTS_FILE=%SCRIPT_DIR%\..\requirements.txt
set DEV_REQUIREMENTS_FILE=%SCRIPT_DIR%\..\requirements-dev.txt

py -m venv venv
venv\Scripts\pip install uv --disable-pip-version-check

REM Generates the galatea.egg-info needed for the version metadata
venv\Scripts\uv build --build-constraints %DEV_REQUIREMENTS_FILE% --wheel

venv\Scripts\uv run --with-requirements %REQUIREMENTS_FILE% %SCRIPT_DIR%\create_standalone.py --include-tab-completions galatea ./contrib/bootstrap_standalone.py
