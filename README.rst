=================
Markus Binsteiner
=================

    :Author: Markus Binsteiner

.. contents::
1 pyclist
---------

A small framework to quickly create cli scripts for REST (or other) APIs.

1.1 Usage
~~~~~~~~~

1.1.1 Requirements for api class (at the moment -- might be changed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Constructor takes named arguments which are present in the resulting argparse namespace (it will be converted to a dict and passed to the constructor)

- methods need to start with "call\_" in order to be automatically added as a sub-command

- [some restritions as to file types maybe]

1.1.2 Example code
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # create the pyclist object
    pyclist_obj = pyclist('proj', 'A commandline client for CeR project management.')

    # add some basic options that are used for all sub-commands (optional)
    pyclist_obj.root_parser.add_argument('--url', '-u', help='API base url', default=self.config.api_url)
    pyclist_obj.root_parser.add_argument('--username', help='API username', default=self.config.api_username)
    pyclist_obj.root_parser.add_argument('--token', help='API token', default=self.config.api_token)

    # register the api class
    pyclist_obj.add_command([api_class])

    # execute the selected method (using an auto-created api object)
    result = pyclist_obj.execute
