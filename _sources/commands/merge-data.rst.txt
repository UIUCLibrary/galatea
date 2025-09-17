++++++++++
merge-data
++++++++++

Merge data from another source

Usage: ``galatea merge-data <source_strategy>``

Currently, the only option is :ref:`from-getmarc<from-getmarc>`

from-getmarc
++++++++++++

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea merge-data from-getmarc --help
    usage: galatea merge-data from-getmarc [-h] {init-mapper,merge} ...

    positional arguments:
      {init-mapper,merge}
        init-mapper        create initial mapping file
        merge              merge data from get-marc server and map to tsv file

    options:
      -h, --help           show this help message and exit

.. _merge-data_from-getmarc_init-mapper:

init-mapper
***********

Generate the mapping file need to merge data from getmarc server.

Usage: ``galatea merge-data from-getmarc init-mapper <source_tsv_file>``

.. note::
    Optional arguments are:
      -h, --help            show this help message and exit
      --output_file OUTPUT_FILE
                            Write to file other than the default.

Example of `init-mapper` usages:
________________________________

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea merge-data from-getmarc init-mapper myfile.tsv
    Wrote mapping file to /Users/user/mapping.toml

.. _merge-data_from-getmarc_merge:

merge
*****

Merge data from tsv file with data from getmarc server.

Usage: ``galatea merge-data from-getmarc merge <metadata_tsv_file> <mapping_file>``

The argument, `<metadata_tsv_file>`, is the tsv file with metadata and `<mapping_file>` is the toml mapping file.

.. note::
    Optional arguments are:
      -h, --help            show this help message and exit
      --output-tsv-file OUTPUT_TSV_FILE
                            write changes to another file instead of inplace
      --getmarc-server GETMARC_SERVER
                            get-marc server url.
      --enable-experimental-features
                            enable experimental features


Example of `merge` usage:
_________________________

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea merge-data from-getmarc merge myfile.tsv /Users/user/mapping.toml
