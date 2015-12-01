#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    "argcomplete",
    "parinx",
    "argparse",
    "restkit",
    "booby"
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pyclist',
    version='0.2.4',
    description="Makes creating cli wrappers for rest services easier.",
    long_description=readme + '\n\n' + history,
    author="Markus Binsteiner",
    author_email='makkus@gmail.com',

    url='https://github.com/makkus/pyclist',
    packages=[
        'pyclist',
    ],
    package_dir={'pyclist':
                 'pyclist'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='pyclist',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
	'console_scripts': [
		'pyclist = pyclist.example:run'
	],
    }
)
