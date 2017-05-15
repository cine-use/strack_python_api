# :coding: utf-8
# :copyright: Copyright (c) 2016 strack

import os
import re

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
RESOURCE_PATH = os.path.join(ROOT_PATH, 'res')
SOURCE_PATH = os.path.join(ROOT_PATH, 'src')
README_PATH = os.path.join(ROOT_PATH, 'README.md')


# Read version from source.
with open(
    os.path.join(SOURCE_PATH, 'strack_api', 'version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        raise SystemExit(pytest.main(self.test_args))


# Call main setup.
setup(
    name='strack-python-api',
    version=VERSION,
    description='Python API for strack.',
    long_description=open(README_PATH).read(),
    keywords='strack, python, api',
    url='https://www.strack.me',
    author='strack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'src'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 1',
        'lowdown >= 0.1.0, < 2'
    ],
    install_requires=[
        'requests >= 2, <3',
        'arrow >= 0.4.4, < 1',
        'termcolor >= 1.1.0, < 2',
        'pyparsing >= 2.0, < 3',
        'clique >= 1.2.0, < 2',
        'websocket-client == 0.12'
    ],
    tests_require=[
        'pytest >= 2.7, < 3',
        'pytest-mock >= 0.4, < 1',
        'pytest-catchlog >= 1, <=2'
    ],
    cmdclass={
        'test': PyTest
    },
    zip_safe=False
)