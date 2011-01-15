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
      package_dir  = {'' : 'src'},
      packages     = ['robotide',
                      'robotide.action',
                      'robotide.application',
                      'robotide.context',
                      'robotide.contrib',
                      'robotide.editor',
                      'robotide.controller',
                      'robotide.log',
                      'robotide.namespace',
                      'robotide.pluginapi',
                      'robotide.publish',
                      'robotide.recentfiles',
                      'robotide.run',
                      'robotide.spec',
                      'robotide.ui',
                      'robotide.usages',
                      'robotide.utils',
                      'robotide.validators',
                      'robotide.widgets',
                      'robotide.writer',
                      ],
      package_data = {'robotide': ['widgets/*.png', 'context/*.cfg']},
      scripts = ['src/bin/ride.py']
      )
