#!/usr/bin/env python

import sys
from os.path import abspath, join, dirname

sys.path.append(join(dirname(__file__), 'src'))
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

ROOT_DIR = dirname(abspath(__file__))
SOURCE_DIR = 'src'

version_file = join(ROOT_DIR, 'src', 'robotide', 'version.py')
exec(compile(open(version_file).read(), version_file, 'exec'))

package_data = {
    'robotide.preferences': ['settings.cfg'],
    'robotide.widgets': ['*.png', '*.ico'],
    'robotide.messages': ['*.html'],
    'robotide.publish.html': ['no_robot.html']
}

long_description = """
Robot Framework is a generic test automation framework for acceptance
level testing. RIDE is a lightweight and intuitive editor for Robot
Framework test data.
""".strip()

classifiers = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
""".strip().splitlines()

# This solution is found at http://stackoverflow.com/a/26490820/5889853
from setuptools.command.install import install
import os


class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        install.run(self)
        os.system("ride_postinstall.py -install")

setup(
    name='robotframework-ride',
    version=VERSION,
    description='RIDE :: Robot Framework Test Data Editor',
    long_description=long_description,
    license='Apache License 2.0',
    keywords='robotframework testing testautomation',
    platforms='any',
    classifiers=classifiers,
    author='Robot Framework Developers',
    author_email='robotframework@gmail.com',
    url='https://github.com/robotframework/RIDE/',
    download_url='https://pypi.python.org/pypi/robotframework-ride',
    py_modules=['ez_setup'],
    package_dir={'': SOURCE_DIR},
    packages=find_packages(SOURCE_DIR),
    package_data=package_data,
    # Robot Framework package data is not included, but RIDE does not need it.
    # Always install everything, since we may be switching between versions
    options={'install': {'force': True}},
    scripts=['src/bin/ride.py', 'ride_postinstall.py'],
    cmdclass={'install': CustomInstallCommand},
    requires=['Pygments']
)
