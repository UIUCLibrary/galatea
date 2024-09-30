@echo off

py -m venv venv
venv\Scripts\pip install uv

venv\Scripts\uv run contrib/create_standalone.py galatea ./galatea/__main__.py
