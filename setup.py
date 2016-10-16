#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup_requirements = [
    'pytest-runner'
]

test_requirements = [
    'pytest',
    'pytest-catchlog'
]

setup(
    name='statechart',
    version='0.3.1',
    description="Python UML statechart framework",
    long_description=readme + '\n\n' + history,
    author="Leigh McKenzie",
    author_email='maccarav0@gmail.com',
    url='https://github.com/leighmck/statechart',
    packages=[
        'statechart',
    ],
    package_dir={'statechart':
                     'statechart'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='statechart',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    setup_requires=setup_requirements,
    tests_require=test_requirements
)
