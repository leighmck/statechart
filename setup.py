#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

test_requirements = ['pytest>=3', ]

setup(
    author="Andrew Leech, Leigh McKenzie",
    author_email="andrew.leech@planetinnovation.com.au",
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    description="State charts management library with asyncio runtime.",
    install_requires=requirements,
    license="ISC license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='statechart',
    name='statechart',
    packages=find_packages(include=['statechart', 'statechart.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url="https://github.com/andrewleech/aio-statechart",
    version="0.5.0",
    zip_safe=False,
)
