#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(fname):
    return (open(os.path.join(os.path.dirname(__file__), fname), 'rb')
            .read().decode('utf-8'))


test_requirements = (
    read('requirements.txt').splitlines()
    + read('requirements_test.txt').splitlines()[1:]
)


setup(
    name = 'cityhall',
    packages = ['cityhall'], # this must be the same as the name above
    version = '0.0.6',
    description = 'A library for accessing City Hall Setting Server',
    author = 'Alex Popa',
    author_email = 'alex.popa@digitalborderlands.com',
    url = 'https://github.com/f00f-nyc/cityhall-python',
    download_url = 'https://codeload.github.com/f00f-nyc/cityhall-python/legacy.tar.gz/v0.0.6',
    install_requires=read('requirements.txt').splitlines(),
    keywords = ['cityhall', 'enterprise settings', 'settings', 'settings server', 'cityhall', 'City Hall'],
    test_suite='test',
    tests_require=test_requirements,
    classifiers = [],
)