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

      {clean-tsv,authority-check,authorized-terms}
        clean-tsv           clean TSV files
        authority-check     validate-authorized-names
        authorized-terms    manipulate authorized terms used



Commands
========

clean-tsv
+++++++++

To clean TSV files use the `clean-tsv` command

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea clean-tsv /Users/user/Documents/River\ Maps\ -\ River\ Maps.tsv
    Modified tsv wrote to "/Users/user/Documents/River Maps - River Maps.tsv"
    Done.


authority-check
+++++++++++++++

To validate columns that should match a Library of Congress Authority, use the `authority-check` command

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea authority-check  /Users/hborcher/PycharmProjects/UIUCLibrary/galatea/River\ Maps\ -\ River\ Maps.tsv
    validating authorized terms
    Line: 2 | Field: "260$a" | "Chicago, Ill." is not an authorized term.
    Line: 3 | Field: "260$a" | "Washington, D.C." is not an authorized term.
    Line: 4 | Field: "260$a" | "Fort Belvoir, Va." is not an authorized term.
    Line: 7 | Field: "264$a" | "Fayetteville, Arkansas" is not an authorized term.
    Line: 8 | Field: "264$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 9 | Field: "260$a" | "Memphis, Tenn." is not an authorized term.
    Line: 11 | Field: "260$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 12 | Field: "264$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 12 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 13 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 14 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 15 | Field: "264$a" | "Vicksburg, Mississippi" is not an authorized term.
    Line: 15 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 16 | Field: "264$a" | "St. Louis, Mo." is not an authorized term.
    Line: 17 | Field: "264$a" | "New Orleans" is not an authorized term.
    Line: 17 | Field: "264$a" | "New York" is not an authorized term.
    Line: 17 | Field: "264$a" | "Chicago" is not an authorized term.
    Line: 18 | Field: "264$a" | "Vicksburg, Mississippi" is not an authorized term.
    Line: 18 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 19 | Field: "264$a" | "Philadelphia, Penn." is not an authorized term.
    hborcher@LIBLAPPRE18 homebrew-uiucprescon %


authorized-terms
++++++++++++++++

This contains functionality to verify, and resolve Library of Congress Authority authorized terms.

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea authorized-terms --help
    usage: galatea authorized-terms [-h] {check,new-transformation-file,resolve} ...

    positional arguments:
      {check,new-transformation-file,resolve}
        check               Check authorized terms are used in tsv file
        new-transformation-file
                            create a new transformation tsv file
        resolve             resolve unauthorized terms to authorized terms in found tsv file

    options:
      -h, --help            show this help message and exit

.. _authorized-terms_authorized-terms-check:

check
+++++

To validate columns that should match a Library of Congress Authority, use the `check` after `authorized-terms`

Usage: ``galatea authorized-terms check <source_tsv>``

The argument, `<source_tsv>`, is the tsv file that you want to check for unauthorized terms.

.. note::
    Optional arguments are:

    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity


Example of using the `check` command:
_____________________________________

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea authorized-terms check  /Users/hborcher/PycharmProjects/UIUCLibrary/galatea/River\ Maps\ -\ River\ Maps.tsv
    validating authorized terms
    Line: 2 | Field: "260$a" | "Chicago, Ill." is not an authorized term.
    Line: 3 | Field: "260$a" | "Washington, D.C." is not an authorized term.
    Line: 4 | Field: "260$a" | "Fort Belvoir, Va." is not an authorized term.
    Line: 7 | Field: "264$a" | "Fayetteville, Arkansas" is not an authorized term.
    Line: 8 | Field: "264$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 9 | Field: "260$a" | "Memphis, Tenn." is not an authorized term.
    Line: 11 | Field: "260$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 12 | Field: "264$a" | "Vicksburg, Miss." is not an authorized term.
    Line: 12 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 13 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 14 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 15 | Field: "264$a" | "Vicksburg, Mississippi" is not an authorized term.
    Line: 15 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 16 | Field: "264$a" | "St. Louis, Mo." is not an authorized term.
    Line: 17 | Field: "264$a" | "New Orleans" is not an authorized term.
    Line: 17 | Field: "264$a" | "New York" is not an authorized term.
    Line: 17 | Field: "264$a" | "Chicago" is not an authorized term.
    Line: 18 | Field: "264$a" | "Vicksburg, Mississippi" is not an authorized term.
    Line: 18 | Field: "264$a" | "Washington, D.C." is not an authorized term.
    Line: 19 | Field: "264$a" | "Philadelphia, Penn." is not an authorized term.


.. _authorized-terms_new-transformation-file:

new-transformation-file
+++++++++++++++++++++++

To create a new transformation file, use the `new-transformation-file` after `authorized-terms`

Usage: ``galatea authorized-terms new-transformation-file``


.. note::
    Optional arguments are:

      -h, --help       show this help message and exit
      --output OUTPUT  Output tsv file
      -v, --verbose    increase output verbosity


Example of using the `new-transformation-file` command:
_______________________________________________________

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea authorized-terms new-transformation-file
    Wrote new transformation tsv file to: /Users/user/authorized_terms_transformation.tsv


.. _authorized-terms_resolve:

resolve
+++++++

To resolve unauthorized terms to authorized terms in found tsv file use the `resolve` after `authorized-terms`

usage: ``galatea authorized-terms resolve <transformation_file> <source_tsv>``

The first argument, `<transformation_file>`, is the file generated by the ``new-transformation-file`` command. It
informs the ``resolve`` command how to resolve the unauthorized terms into authorized terms.

The second argument, `<source_tsv>`, is the tsv file that is the tsv file containing the marc data you want to have
unauthorized terms resolved.

.. note::
    Optional arguments are:

      -h, --help            show this help message and exit
      --output OUTPUT_TSV   Output tsv file
      -v, --verbose         increase output verbosity


Example of using the `resolve` command:
_______________________________________

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea % python -m galatea authorized-terms resolve authorized_terms_transformation.tsv "River Maps - River Maps.tsv"
    Wrote to River Maps - River Maps.tsv
