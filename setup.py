#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name = 'cityhall',
    packages = ['cityhall'], # this must be the same as the name above
    version = '0.0.10',
    description = 'A library for accessing City Hall Setting Server',
    license = 'AGPL',
    author = 'Alex Popa',
    author_email = 'alex.popa@digitalborderlands.com',
    url = 'https://github.com/f00f-nyc/cityhall-python',
    download_url = 'https://codeload.github.com/f00f-nyc/cityhall-python/legacy.tar.gz/v0.0.10',
    install_requires=['requests==2.7.0','six==1.9.0'],
    keywords = ['cityhall', 'enterprise settings', 'settings', 'settings server', 'cityhall', 'City Hall'],
    test_suite='test',
    tests_require=['requests==2.7.0','six==1.9.0','mock==1.0.1'],
    classifiers = [],
)