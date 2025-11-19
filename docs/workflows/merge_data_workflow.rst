==============================
Merge Data from getmarc server
==============================

`Added in version 0.4`

This workflow is used to merge data in a tsv file with metadata from a getmarc
server.

Prerequisites
=============

* Setup a getmarc server.

    In order to perform this workflow, the `get_marc_server_url` configuration
    in galatea needs to be set.

    To verify that this has been configured, use the :ref:`config command <config_command>`.

    If `get_marc_server_url` is set, a value will show. If `get_marc_server_url` is not set, it can be set with ``config set`` command.

    For example, ``galatea config set get_marc_server_url https://example.com/`` will configure galatea to use a getmarc
    server at `https://example.com/`.

* Have a profile toml file that maps the columns in the tsv file to the MARC fields.

    See :ref:`Create New Merge Data Profile<Create New Merge Data Profile>` for more information on how to create
    this file.

Workflow
========



Merge the data with the :ref:`merge command<merge-data_from-getmarc_merge>`

    .. code-block:: shell-session

        user@WORKMACHINE123 % galatea merge-data from-getmarc merge myfile.tsv /Users/user/mapping.toml


For information on the mapping file, see the :ref:`Getmarc Merge Mapper Toml File<Getmarc Merge Mapper Toml File>` documentation.