======================
Using the Command Line
======================

Getting Help
============

To get help at any point you can use the `--help` flag

.. code-block:: shell-session

    user@WORKMACHINE123 galatea % galatea --help
    usage: galatea [-h] [--version] {clean-tsv,authority-check} ...

    Galatea is a tool for manipulating tsv data.

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    commands:
      valid commands

      {clean-tsv,authority-check}
        clean-tsv           clean TSV files
        authority-check     validate-authorized-names

Clean Tsv
=========

To clean TSV files use the `clean-tsv` command

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea clean-tsv /Users/user/Documents/River\ Maps\ -\ River\ Maps.tsv
    Modified tsv wrote to "/Users/user/Documents/River Maps - River Maps.tsv"
    Done.


Verify values based on Authority
================================

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