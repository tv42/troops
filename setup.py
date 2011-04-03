#!/usr/bin/python
from setuptools import setup, find_packages
import os

setup(
    name="troops",
    version="0.0.1",
    packages=find_packages(),

    author="Tommi Virtanen",
    author_email="tv@eagain.net",
    description="A software deployment tool",
    long_description="""

Troops is a reaction to Cfengine/BCFG2/Chef/Puppet. It is an explicit
attempt to build something different.

""".strip(),
    license="MIT",
    keywords="deploy",
    url="https://github.com/tv42/troops",

    install_requires=[
        'setuptools',
        'argparse >=1.1',
        ],

    tests_require=[
        'nose >=1.0.0',
        'fudge >=1.0.3',
        ],

    entry_points={
        'console_scripts': [
            'troops = troops.cli.main:main',
            ],

        'troops.cli': [
            'deploy = troops.cli.deploy:main',
            'merge = troops.cli.merge:main',
            ],
        },

    )
