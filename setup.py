#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

SCRIPTDIR = os.path.dirname(__file__) or '.'
PY3 = sys.version_info >= (3, 0, 0)


def read(fname):
    """ Return content of specified file """
    path = os.path.join(SCRIPTDIR, fname)
    if PY3:
        f = open(path, 'r', encoding='utf8')
    else:
        f = open(path, 'r')
    content = f.read()
    f.close()
    return content


def read_reqs(fname):
    return read(fname).strip().split('\n')


def in_scriptdir(path):
    return os.path.join(SCRIPTDIR, os.path.normpath(path))

REQPATH = in_scriptdir('requirements.txt')
DEPS = read_reqs(REQPATH)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments for py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='bottle-fdsend',
    version='0.1.1',
    author='Outernet Inc',
    author_email='branko@outernet.is',
    description='Library for constructing responses from file descriptors',
    license='GPLv3',
    keywords='file static http response bottle',
    url='https://github.com/Outernet-Project/bottle-fdsend',
    packages=find_packages(),
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 2.7',
        'Framework :: Bottle',
        'Environment :: Web Environment',
    ],
    install_requires=DEPS,
    cmdclass={
        'test': PyTest,
    },
)
