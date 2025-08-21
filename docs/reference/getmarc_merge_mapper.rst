******************************
Getmarc Merge Mapper Toml File
******************************

Mapping Fields
==============

key
---
    **Description:** Column name in tsv file

    **Example:**
      .. code-block:: toml

            key = "Uniform Title"

serialize_method
----------------
    **Description:** This tells the strategy how to serialize the data from marc record. By default, it will use "verbatim".

    **Valid Values:**
        * **"verbatim"**: Make no changes to the data from getmarc record.

matching_marc_fields
--------------------

    **Description:** marc fields to use from getmarc record

    **Example:**
      .. code-block:: toml

            matching_marc_fields = ["240$a"]

delimiter
---------

    **Description:** delimiter characters to use from getmarc record

    **Example:**
      .. code-block:: toml

            delimiter = "||"

existing_data
-------------

    **Description:** What to do if the column in tsv file already has a value.

    **Valid Values:**

    .. list-table::
        :widths: 25 75
        :stub-columns: 1

        * - keep
          - Keep existing value. Ignore value found in marc record.
        * - replace
          - Replace existing value with the new value from marc record
        * - append
          - Add the new value from marc record to the existing value in tsv file, separated by the delimiter.

    **Example:**
      .. code-block:: toml

            existing_data = "keep"

Experimental Features
=====================

This section is for features that are not yet fully implemented, but are available for testing and feedback.

**In order to use these features, you must enable them!** To enable to use the `--enable-experimental-features` flag
when running the `galatea merge-data from-getmarc merge` command. If you do not enable this flag, these features will
not be available and will produce and error if you try to use them.

These features may change or be removed in future releases.

Using jinja2 template
---------------------

Added in version 0.4.1.

This allows you to use `jinja2 templates <https://jinja.palletsprojects.com/en/stable/templates/>`_ to serialize the data from getmarc record.

The variable `fields` will contain a dictionary of all the marc fields in the record, where the keys are the field tags

**Example**

    In the following example, for every 700 field in the marc record, it will combine the 'a', 'q' (if there is one), and
    'd' subfields into a single string, separated by spaces, and use '||' as the delimiter between each 700 field.

    .. code-block:: toml

        serialize_method = "jinja2template"
        jinja_template = "{% for field in fields['700'] %}{{ field['a'] }}{% if field['q'] %} {{field['q']}}{%endif%} {{ field['d'] }}{% if not loop.last %}||{% endif %}{% endfor %}"


    This will take a marc xml record like this:

    .. code-block:: xml

        <record>
            <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Smith, John</subfield>
                <subfield code="q">Jr.</subfield>
                <subfield code="d">1980-</subfield>
            </datafield>
            <datafield tag="700" ind1=" " ind2=" ">
                <subfield code="a">Doe, Jane</subfield>
                <subfield code="d">1990-</subfield>
            </datafield>
        </record>

    and produce the following output in the tsv file: "**Smith, John Jr. 1980-||Doe, Jane 1990-**"