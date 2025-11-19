+++++++++
clean-tsv
+++++++++

To clean TSV files use the `clean-tsv` command

Usage
-----

Usage format: ``galatea clean-tsv [options] <source_tsv>``

.. note::
    Optional arguments are:
      -h, --help            show this help message and exit
      -v, --verbose         increase output verbosity
      --output OUTPUT_TSV   Output tsv file

Example of using the `clean-tsv` command:
-----------------------------------------

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea clean-tsv /Users/user/Documents/River\ Maps\ -\ River\ Maps.tsv
    Modified tsv wrote to "/Users/user/Documents/River Maps - River Maps.tsv"
    Done.

