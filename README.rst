|pypi| |license| |master_build|

VPK is Valve's file format for storing game assets.
This module is able to read the index and individual files.


Install
-------

You can grab the latest release from https://pypi.python.org/pypi/vpk or via ``pip``

.. code:: bash

    pip install vpk


Example usage
-------------

The VPK instance is iterable in the standard ways and produces paths to files

.. code:: python

    import vpk

    pak1 = vpk.VPK("/d/Steam/steamapps/common/dota 2 beta/dota/pak01_dir.vpk")

    for filepath in pak1:
        print filepath

.. code:: text

    -------------------------------------------------
    sound/half_sec_qd.wav
    sound/items/guardian_greaves.wav
    sound/items/urn_of_shadows.wav
    sound/items/rune_bounty.wav
    sound/items/refresher.wav
    sound/items/item_mael_lightning_04.wav
    sound/items/greevil_whistle.wav
    ...


Reading a specifc file is done by passing the file path to ``get_file()`` method, which
returns a ``VPKFile`` instance, which acts as a regular ``file`` instance. Writting is not
possible.

.. code:: python

    pakfile = pak1.get_file("scripts/emoticons.txt")
    print pakfile.read().decode('utf-16le')

.. code:: text

    -------------------------------------------------
    "emoticons"
    {
        // An ID of zero is invalid

        "1"
        {
            "image_name" "wink.png"
            "ms_per_frame" "100"
    ...

Or if you need to extract a file.

.. code:: python

    pakfile.save("./emoticons.txt")


.. |pypi| image:: https://img.shields.io/pypi/v/vpk.svg?style=flat&label=latest%20version
    :target: https://pypi.python.org/pypi/vpk
    :alt: Latest version released on PyPi

.. |license| image:: https://img.shields.io/pypi/l/vpk.svg?style=flat&label=license
    :target: https://pypi.python.org/pypi/vpk
    :alt: MIT License

.. |master_build| image:: https://img.shields.io/travis/ValvePython/vpk/master.svg?style=flat&label=master%20build
    :target: http://travis-ci.org/ValvePython/vpk
    :alt: Build status of master branch
