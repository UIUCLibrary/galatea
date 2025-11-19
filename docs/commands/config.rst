.. _config_command:

++++++
config
++++++

Configure galatea settings.

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea config --help

    usage: galatea config [-h] {set,show} ...

    positional arguments:
      {set,show}
        set       set config
        show      show current configuration

    options:
      -h, --help  show this help message and exit


Example of using the `config` command:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set ``get_marc_server_url`` settings to the value ``https://www.example.com``

.. code-block:: shell-session

    user@WORKMACHINE123 % galatea config set get_marc_server_url https://www.example.com

