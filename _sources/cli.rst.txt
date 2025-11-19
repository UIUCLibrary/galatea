======================
Using the Command Line
======================

.. _galatea_command:

Commands
========
.. toctree::
   :maxdepth: 3
   :hidden:

   commands/authorized-terms
   commands/clean-tsv
   commands/merge-data
   commands/config

Below is the hierarchy of commands that are available in Galatea.

.. parsed-literal::
    :ref:`galatea <galatea_command>`
        ├── :ref:`authorized-terms <authorized-terms>`
        │   ├── :ref:`check <authorized-terms_authorized-terms-check>`
        │   ├── :ref:`new-transformation-file <authorized-terms_new-transformation-file>`
        │   └── :ref:`resolve <authorized-terms_resolve>`
        │
        ├── :ref:`clean-tsv <clean-tsv>`
        ├── :ref:`merge-data <merge-data>`
        │   └── :ref:`from-getmarc <from-getmarc>`
        │       ├── :ref:`init-mapper <merge-data_from-getmarc_init-mapper>`
        │       └── :ref:`merge <merge-data_from-getmarc_merge>`
        │
        └── :ref:`config <config_command>`
            ├── :ref:`set <config_command>`
            └── :ref:`show <config_command>`

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

