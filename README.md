# galatea
Used for cleaning up metadata used by UIUC metadata.

[Documentation](https://uiuclibrary.github.io/galatea/)

## Set up development environment on Mac and Linux

### Using UV instead of pip

This way is better and faster than using pip.

```shell
uv venv
source .venv/bin/activate
uv pip sync requirements-dev.txt
uv pip install -e .
pre-commit install
```

### Using pip

If you don't have uv installed:

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```
