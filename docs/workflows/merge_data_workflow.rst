==============================
Merge Data from getmarc server
==============================

`Added in version 0.4`

This workflow is used to merge data in a tsv file with metadata from a getmarc
server.

Prerequisites
=============

In order to perform this workflow, the `get_marc_server_url` configuration
in galatea needs to be set.

To verify that this has been configured, use the :ref:`config command <config_command>`.

If `get_marc_server_url` is set, a value will show. If `get_marc_server_url` is not set, it can be set with ``config set`` command.

For example, ``galatea config set get_marc_server_url https://example.com/`` will configure galatea to use a getmarc
server at https://example.com/

Workflow
========

#. If not using an existing mapping toml file, generate a new one with :ref:`merge-data from-getmarc init-mapper
   command <merge-data_from-getmarc_init-mapper>`.

    .. code-block:: shell-session

        user@WORKMACHINE123 % galatea merge-data from-getmarc init-mapper myfile.tsv
        Wrote mapping file to /Users/user/mapping.toml


#. Edit the content of the created mapping toml file in a text editor.

    * Make sure the identifier_key is set to column containing the mmsid in the tsv file.

        .. code-block:: toml

            [mappings]
            identifier_key = "Bibliographic Identifier"

    * For each column expected to have data added to, edit each [[mapping]] section.

      :ref:`See Mapping Fields section for more details<Mapping Fields>`



#. Merge the data with the :ref:`merge command<merge-data_from-getmarc_merge>`

    .. code-block:: shell-session

        user@WORKMACHINE123 % galatea merge-data from-getmarc merge myfile.tsv /Users/user/mapping.toml


Mapping Fields
==============

key
---
.. list-table::
    :widths: 25 75
    :stub-columns: 1

    * - Description:
      - Column name in tsv file
    * - Example:
      - .. code-block:: toml

            key = "Uniform Title"

matching_marc_fields
--------------------

.. list-table::
    :widths: 25 75
    :stub-columns: 1

    * - Description:
      - marc fields to use from getmarc record
    * - Example:
      - .. code-block:: toml

            matching_marc_fields = ["240$a"]

delimiter
---------

.. list-table::
    :widths: 25 75
    :stub-columns: 1

    * - Description:
      - delimiter characters to use from getmarc record
    * - Example:
      - .. code-block:: toml

            delimiter = "||"

existing_data
-------------

.. list-table::
    :widths: 25 75
    :stub-columns: 1

    * - Description:
      - What to do if the column in tsv file already has a value.
    * - Valid Values:
      - * keep
        * replace
        * append
    * - Example:
      - .. code-block:: toml

            existing_data = "keep"

