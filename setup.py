#!/usr/bin/env python

import os
from distutils.core import setup


# Get VERSION
execfile(os.path.join('src','robotide','version.py'))

# Maximum width in Windows installer seems to be 70 characters ------|
DESCRIPTION = """
Robot Framework is a generic test automation framework for acceptance
level testing. RIDE is a lightweight and intuitive editor for Robot
Framework test data.
"""[1:-1]
CLASSIFIERS = """
Development Status :: 4 - Beta
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
"""[1:-1]

PACKAGE_DIR = 'src'

def with_subpackages(parent_package):
    packages = ['.'.join(parent_package)]
    for item in os.listdir(os.path.join(PACKAGE_DIR, *parent_package)):
        items_package = parent_package+[item]
        if _is_package(PACKAGE_DIR, *items_package):
            packages += with_subpackages(items_package)
    return packages

def _is_package(*path_parts):
    return os.path.isdir(os.path.join(*path_parts)) and os.path.isfile(os.path.join(*(path_parts+('__init__.py',))))

setup(name         = 'robotframework-ride',
      version      = VERSION,
      description  = 'RIDE :: Robot Framework Test Data Editor',
      long_description = DESCRIPTION,
      license      = 'Apache License 2.0',
      keywords     = 'robotframework testing testautomation',
      platforms    = 'any',
      classifiers  = CLASSIFIERS.splitlines(),
      author       = 'Robot Framework Developers',
      author_email = 'robotframework-devel@googlegroups,com',
      url          = 'http://code.google.com/p/robotframework-ride',
      package_dir  = {'' : PACKAGE_DIR},
      packages     = with_subpackages(['robotide']),
      package_data = {'robotide': ['widgets/*.png',
                                   'widgets/*.ico',
                                   'context/*.cfg',
                                   'bundled/robot/*.py',
                                   'bundled/robot/*/*.py',
                                   'bundled/robot/webcontent/*.html',
                                   'bundled/robot/webcontent/*.css',
                                   'bundled/robot/webcontent/*.js',
                                   'bundled/robot/webcontent/lib/*.js']},
      scripts = ['src/bin/ride.py']
      )
