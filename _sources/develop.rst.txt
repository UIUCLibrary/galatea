===============================================
Set up development environment on Mac and Linux
===============================================

-----------------------
Development environment
-----------------------

Set up development environment on Mac and Linux

This project uses `uv <https://docs.astral.sh/uv/>`_ for project development. This is not a runtime requirements but it
is the primary development configuration so you will need to have
`uv installed <https://docs.astral.sh/uv/getting-started/installation/>`_ to get the
`dependency locks <https://docs.astral.sh/uv/concepts/projects/sync/>`_.

.. code-block:: shell-session

    user@DEVMACHINE123 % uv sync --group dev
    user@DEVMACHINE123 % source .venv/bin/activate
    (venv) user@DEVMACHINE123 % pre-commit install


-------------
Running tests
-------------

To run test, you need to have pytest installed. If you are using the development environment, it should already be
installed. Tests are run by executing the pytest command.

.. code-block:: shell-session

    (venv) user@DEVMACHINE123 galatea % pytest
    ========================= test session starts ==========================
    platform darwin -- Python 3.11.10, pytest-8.4.1, pluggy-1.6.0
    rootdir: /Users/user/PycharmProjects/UIUCLibrary/galatea
    configfile: pyproject.toml
    plugins: pyfakefs-5.9.2
    collected 150 items

    tests/test_clean_tsv.py .............                            [  8%]
    tests/test_cli.py ...........                                    [ 16%]
    tests/test_config.py .........                                   [ 22%]
    tests/test_merge_data.py ....................................... [ 48%]
    ..........                                                       [ 54%]
    tests/test_modifiers.py ........................                 [ 70%]
    tests/test_resolve_authorized_terms.py .................         [ 82%]
    tests/test_tsv.py ............                                   [ 90%]
    tests/test_validate_authorized_terms.py ...............          [100%]

    ========================= 150 passed in 0.32s =========================

-------------------
Build Documentation
-------------------

The documentation for galatea contains both user and developer documentation. It is written in
`restructuredText format <https://en.wikipedia.org/wiki/ReStructuredText>`_ and built with
the `Sphinx <https://www.sphinx-doc.org/en/master/>`_ tool.

1. Make sure that either the virtual environment is configure with the "dev" or "docs" dependency group

    Either run uv sync with the full development dependencies group:

    .. code-block:: shell-session

        user@DEVMACHINE123 % uv sync --group dev
        Using CPython 3.11.10
        Creating virtual environment at: .venv
        Resolved 82 packages in 12ms
        Prepared 53 packages in 3.97s
        Installed 53 packages in 260ms
         + alabaster==1.0.0
         + argcomplete==3.6.2
         + babel==2.17.0
         + cachetools==6.2.0
         + certifi==2025.8.3
         + cfgv==3.4.0
         + chardet==5.2.0
         + charset-normalizer==3.4.3
        ...


    or run uv sync with only the dependencies needed to build the documentation:

    .. code-block:: shell-session

        user@DEVMACHINE123 % uv sync --no-dev --group docs
        Using CPython 3.11.10
        Creating virtual environment at: .venv
        Resolved 82 packages in 13ms
        Prepared 27 packages in 4.35s
        Installed 27 packages in 348ms
         + alabaster==1.0.0
         + argcomplete==3.6.2
         + babel==2.17.0
         + certifi==2025.8.3
         + charset-normalizer==3.4.3
         + docutils==0.21.2
         + idna==3.10
         + imagesize==1.4.1
         + jinja2==3.1.6
        ...

2. With your virtual environment active, run sphinx-build with the first argument being "docs" and the second argument
   being the location where to build to.


    .. code-block:: shell-session

        (.venv) user@DEVMACHINE123 % sphinx-build docs build/docs
        Running Sphinx v8.2.3
        loading translations [en]... done
        loading pickled environment... done
        building [mo]: targets for 0 po files that are out of date
        writing output...
        building [html]: targets for 3 source files that are out of date
        updating environment: [new config] 3 added, 0 changed, 0 removed
        reading sources... [100%] development
        looking for now-outdated files... none found
        pickling environment... done
        checking consistency... done
        preparing documents... done
        copying assets...
        copying static files...
        Writing evaluated template result to /Users/user/PythonProjects/UIUCLibrary/galatea/build/docs/_static/basic.css
        Writing evaluated template result to /Users/user/PythonProjects/UIUCLibrary/galatea/build/docs/_static/language_data.js
        Writing evaluated template result to /Users/user/PythonProjects/UIUCLibrary/galatea/build/docs/_static/documentation_options.js
        Writing evaluated template result to /Users/user/PythonProjects/UIUCLibrary/galatea/build/docs/_static/alabaster.css
        copying static files: done
        copying extra files...
        copying extra files: done
        copying assets: done
        writing output... [100%] index
        generating indices... genindex done
        writing additional pages... search done
        dumping search index in English (code: en)... done
        dumping object inventory... done
        build succeeded.

        The HTML pages are in build/docs.
