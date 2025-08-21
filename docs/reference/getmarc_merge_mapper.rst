******************************
Getmarc Merge Mapper Toml File
******************************

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

