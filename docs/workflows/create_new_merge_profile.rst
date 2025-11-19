=============================
Create New Merge Data Profile
=============================

This is for creating a new merge data profile for use with the `galatea merge-data` command.

#. Generate a new initialized mapping toml one with :ref:`merge-data from-getmarc init-mapper
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

