#!/usr/bin/env python

from setuptools import setup
from codecs import open
from os import path
import vpk

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vpk',
    version=vpk.__version__,
    description='Library for reading/extracting files from VPK',
    long_description=long_description,
    url='https://github.com/ValvePython/vpk',
    author='Rossen Georgiev',
    author_email='hello@rgp.io',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='valve vpk tf2 dota2 csgo dota',
    packages=['vpk'],
    zip_safe=True,
)
