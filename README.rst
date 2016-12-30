|pypi| |license| |master_build|

VPK is Valve's file format for storing game assets.
Pythonic access to VPK files and their contents together with a cli tool.

Tested and works on ``python2.6``, ``python2.7``, ``python3.2+``, ``pypy`` and ``pypy3``.


Install
-------

You can grab the latest release from https://pypi.python.org/pypi/vpk or via ``pip``

.. code:: bash

    pip install vpk


Quick start
-----------

The VPK instance is iterable in the standard ways and produces paths to files

.. code:: python

    import vpk

    pak1 = vpk.open("/d/Steam/steamapps/common/dota 2 beta/dota/pak01_dir.vpk")

    for filepath in pak1:
        print filepath

Reading a specifc file is done by passing the file path to ``get_file()`` method, which
returns a ``VPKFile`` instance, which acts as a regular ``file`` instance. Writting is not
possible.

.. code:: python

    pakfile = pak1.get_file("scripts/emoticons.txt")
    pakfile = pak1["scripts/emoticons.txt"]
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

Saving a file is just as easy.

.. code:: python

    pakfile.save("./emoticons.txt")


The module supports creating basic VPKs.
Multi archive paks are not yet supported.

.. code:: python

    newpak = vpk.new("./some/directory")
    newpak.save("file.vpk")

    pak = newpak.save_and_open("file.vpk")


CLI tool
--------

A command line utility is also included

.. code:: text

    usage: vpk [-h] [--version] [-l] [-la] [-x OUT_LOCATION] [-nd] [-t] [-c DIR]
               [-f WILDCARD | -re REGEX | -name WILDCARD]
               file

    Manage Valve Pak files

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    Main:
      file                  Input VPK file
      -l, --list            List file paths
      -la                   List file paths, crc, size
      -x OUT_LOCATION, --extract OUT_LOCATION
                            Exctract files to directory
      -nd, --no-directories
                            Don't create directries during extraction
      -t, --test            Verify contents
      -c DIR, --create DIR  Create VPK file from directory

    Filters:
      -f WILDCARD, --filter WILDCARD
                            Wildcard filter for file paths
      -re REGEX, --regex REGEX
                            Regular expression filter for file paths
      -name WILDCARD        Filename wildcard filter


.. |pypi| image:: https://img.shields.io/pypi/v/vpk.svg?style=flat&label=latest%20version
    :target: https://pypi.python.org/pypi/vpk
    :alt: Latest version released on PyPi

.. |license| image:: https://img.shields.io/pypi/l/vpk.svg?style=flat&label=license
    :target: https://pypi.python.org/pypi/vpk
    :alt: MIT License

.. |master_build| image:: https://img.shields.io/travis/ValvePython/vpk/master.svg?style=flat&label=master%20build
    :target: http://travis-ci.org/ValvePython/vpk
    :alt: Build status of master branch
