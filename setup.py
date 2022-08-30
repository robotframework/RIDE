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

import os
import sys
from os.path import abspath, join, dirname
from setuptools import setup, find_packages
from setuptools.command.install import install

ROOT_DIR = dirname(abspath(__file__))
SOURCE_DIR = 'src'
REQUIREMENTS = ['PyPubSub',
                'Pygments',
                'psutil',
                'Pywin32; sys_platform=="win32"',
                'wxPython']

PACKAGE_DATA = {
    'robotide.preferences': ['settings.cfg'],
    'robotide.widgets': ['*.png', '*.gif', '*.ico'],
    'robotide.messages': ['*.html'],
    'robotide.application': ['*.html', '*.css'],
    'robotide.publish.htmlmessages': ['no_robot.html'],
    'robotide.postinstall': ['RIDE.app/Contents/PkgInfo', 'RIDE.app/Contents/Info.plist',
                             'RIDE.app/Contents/MacOS/RIDE', 'RIDE.app/Contents/Resources/*.icns']
}

LONG_DESCRIPTION = """
Robot Framework is a generic test automation framework for acceptance
level testing. RIDE is a lightweight and intuitive editor for Robot
Framework test data.
""".strip()

CLASSIFIERS = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Topic :: Software Development :: Testing
""".strip().splitlines()


# This solution is found at http://stackoverflow.com/a/26490820/5889853
class CustomInstallCommand(install):
    """Customized setuptools install command - install RIDE desktop shortcut."""
    def run(self):
        install.run(self)
        sys.stdout.write("Creating Desktop Shortcut to RIDE...\n")
        post_installer_file = join(ROOT_DIR, SOURCE_DIR, 'robotide', 'postinstall', '__main__.py')
        command = sys.executable + " " + post_installer_file + " -install"
        os.system(command)


main_ns = dict()
version_file = join(ROOT_DIR, SOURCE_DIR, 'robotide', 'version.py')
with open(version_file) as _:
    exec(_.read(), main_ns)

setup(
    name='robotframework-ride',
    version=main_ns['VERSION'],
    description='RIDE :: Robot Framework Test Data Editor',
    long_description=LONG_DESCRIPTION,
    license='Apache License 2.0',
    keywords='robotframework testing testautomation',
    platforms='any',
    classifiers=CLASSIFIERS,
    author='Robot Framework Developers',
    author_email='robotframework@gmail.com',
    url='https://github.com/robotframework/RIDE/',
    download_url='https://pypi.python.org/pypi/robotframework-ride',
    install_requires=REQUIREMENTS,
    package_dir={'': SOURCE_DIR},
    packages=find_packages(SOURCE_DIR),
    package_data=PACKAGE_DATA,
    python_requires='>=3.6',
    # Robot Framework package data is not included, but RIDE does not need it.
    # Always install everything, since we may be switching between versions
    options={'install': {'force': True}},
    scripts=['src/bin/ride.py', 'src/bin/ride_postinstall.py'],
    cmdclass={'install': CustomInstallCommand},
)
