# Developer's Guide

## Configure Development Environment on Mac and Linux

### Option 1: Using UV (Recommended)

This way is better and faster than using pip. However, you need to have 
[uv already installed](https://docs.astral.sh/uv/getting-started/installation/).

```shell
uv venv
source .venv/bin/activate
uv pip sync requirements-dev.txt
uv pip install -e .
pre-commit install
```

### Option 2: Using pip

If you don't have uv installed:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```

## Build Documentation

Galatea documentation is written in a combination of Markdown and 
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) 
and is built using [Sphinx](https://www.sphinx-doc.org/en/master/index.html). 

To build the documentation as html, use the following command within your 
development environment.

```shell
python -m sphinx docs/ dist/docs/
```