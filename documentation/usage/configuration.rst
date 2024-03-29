.. configuration:

Configuration
=============

Per-user settings may be defined by in the file .tkp.cfg in your home
directory. This file follows the standard Python ConfigParser syntax.

You will need to configure a database unless you can rely upon the default.

    [database]
    enabled = True
    host = ldb001
    name = tkp
    user = tkp
    password = tkp
    port = 50000

A default configuration file may be generated as follows::

  import tkp.config
  tkp.config.write_config()


Note that this will overwrite any existing configuration file: use with care!

.. Warning::

  We are working on moving all tkp.config settings to configuration and parset
  files inside a pipeline project folder, this will be removed in the future.

