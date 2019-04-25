#!/usr/bin/env python
#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
from os.path import abspath, join, dirname

sys.path.append(join(dirname(__file__), 'src'))
from setuptools import setup, find_packages

ROOT_DIR = dirname(abspath(__file__))
SOURCE_DIR = 'src'
REQUIREMENTS = ['wxPython', 'PyPubSub', 'Pygments']

#Windows specific requirements
if sys.platform == 'win32':
    REQUIREMENTS.append('Pywin32')

version_file = join(ROOT_DIR, 'src', 'robotide', 'version.py')
exec(compile(open(version_file).read(), version_file, 'exec'))

package_data = {
    'robotide.preferences': ['settings.cfg'],
    'robotide.widgets': ['*.png', '*.gif', '*.ico'],
    'robotide.messages': ['*.html'],
    'robotide.publish.htmlmessages': ['no_robot.html']
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
import sys


class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        install.run(self)
        _ = sys.stderr.write("Creating Desktop Shortcut to RIDE...\n")
        postinstaller_file = join(ROOT_DIR, 'src', 'robotide', 'postinstall', '__main__.py')
        command = sys.executable + " " +postinstaller_file + " -install"
        os.system(command)

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
    install_requires = REQUIREMENTS,
    package_dir={'': SOURCE_DIR},
    packages=find_packages(SOURCE_DIR),
    package_data=package_data,
    # Robot Framework package data is not included, but RIDE does not need it.
    # Always install everything, since we may be switching between versions
    options={'install': {'force': True}},
    scripts=['src/bin/ride.py', 'src/bin/ride_postinstall.py'],
    cmdclass={'install': CustomInstallCommand},
    requires=['Pygments', 'wxPython', 'PyPubSub']
)
