======================
Using the Command Line
======================

Getting Help
============

To get help at any point you can use the `--help` flag

.. code-block:: shell-session

    user@WORKMACHINE123 galatea % galatea --help
    usage: galatea [-h] [--version] {clean-tsv,authority-check,authorized-terms} ...

    Galatea is a tool for manipulating tsv data.

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    commands:
      valid commands

    {clean-tsv,authority-check,authorized-terms,merge-data,config}
      clean-tsv           clean TSV files
      authority-check     validate-authorized-names
      authorized-terms    manipulate authorized terms used
      merge-data          merge data from another source to tsv file
      config              configure galatea

Commands
========


.. toctree::
   :maxdepth: 2

   commands/authorized-terms

.. toctree::
   :maxdepth: 3

   commands/merge-data


clean-tsv
---------

To clean TSV files use the `clean-tsv` command

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea clean-tsv /Users/user/Documents/River\ Maps\ -\ River\ Maps.tsv
    Modified tsv wrote to "/Users/user/Documents/River Maps - River Maps.tsv"
    Done.


.. _config_command:

config
------

Configure galatea settings.

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea config --help

    usage: galatea config [-h] {set,show} ...

    positional arguments:
      {set,show}
        set       set config
        show      show current configuration

    options:
      -h, --help  show this help message and exit


Example of using the `config` command:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set ``get_marc_server_url`` settings to the value ``https://www.example.com``

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea config set get_marc_server_url https://www.example.com

