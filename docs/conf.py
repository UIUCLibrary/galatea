import sys
import os

if sys.version_info < (3, 11):
    from tomli import load as load_toml
else:
    from tomllib import load as load_toml


project_file = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "pyproject.toml"
    )
)

with open(project_file, "rb") as f:
    metadata = load_toml(f)['project']

project = metadata['name'].title()

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

copyright = f'2025, {project}'
author = metadata['authors'][0]['name']

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.autosectionlabel',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_logo = '_static/full_mark_horz_bw.gif'