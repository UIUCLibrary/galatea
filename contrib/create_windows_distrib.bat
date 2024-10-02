@echo off

py -m venv venv
venv\Scripts\pip install uv

REM Generates the galatea.egg-info needed for the version metadata
venv\Scripts\uv build --wheel

venv\Scripts\uv run contrib/create_standalone.py galatea ./galatea/__main__.py
