#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name = 'libagnos-python',
    version = '1.0.0',
    description = 'Agnos Python Libraries',
    author = 'Tomer Filiba',
    author_email = 'tomerf@il.ibm.com',
    url = 'http://agnos.sourceforge.net',
    license = 'Apache License 2.0',
    packages = ['agnos'],
    package_dir = {'agnos' : 'src'},
)

