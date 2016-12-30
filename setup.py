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
    description='Library for working with Valve Pak files',
    long_description=long_description,
    url='https://github.com/ValvePython/vpk',
    author='Rossen Georgiev',
    author_email='hello@rgp.io',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='valve pak vpk tf2 dota2 csgo dota',
    packages=['vpk'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'vpk = vpk.cli:main',
            ],
    },
)
