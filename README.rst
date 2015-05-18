|pypi| |license|

VPK is Valve's file format for storing game assets.
This module is able to read the index and individual files.


Install
-------

You can grab the latest release from https://pypi.python.org/pypi/vpk or via ``pip``

.. code:: bash

    pip install vpk


Example usage
-------------

.. code:: python

    import vpk

    pak1 = vpk.VPK("/d/Steam/steamapps/common/dota 2 beta/dota/pak01_dir.vpk")
    contents = pak1.read_file("resource/flash3/images/avatars/default_184.png")
    number_of_files = len(pak1.files)


.. |pypi| image:: https://img.shields.io/pypi/v/vpk.svg?style=flat&label=latest%20version
    :target: https://pypi.python.org/pypi/vpk
    :alt: Latest version released on PyPi

.. |license| image:: https://img.shields.io/pypi/l/vpk.svg?style=flat&label=license
    :target: https://pypi.python.org/pypi/vpk
    :alt: MIT License

