#!/usr/bin/env python

#  Copyright 2008 Nokia Siemens Networks Oyj
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
import os
from distutils.core import setup
sys.path.insert(0, os.path.join('src','robotide'))
from version import VERSION


def main():
    setup(name         = 'robotide',
          version      = VERSION,
          description  = 'Robot Framework test data editor',
          author       = 'Robot Framework Developers',
          author_email = 'robotframework-ride@googlegroups,com',
          url          = 'http://code.google.com/p/robotframework-ride/',
          package_dir  = {'' : 'src'},
          packages     = ['robotide',
                          'robotide.action',
                          'robotide.application',
                          'robotide.context',
                          'robotide.editor',
                          'robotide.controller',
                          'robotide.namespace',
                          'robotide.pluginapi',
                          'robotide.publish',
                          'robotide.run',
                          'robotide.spec',
                          'robotide.ui',
                          'robotide.utils',
                          'robotide.validators',
                          'robotide.writer',
                          ],
          package_data = {'robotide': ['spec/*.xml' , 'ui/*.png',
                                       'context/*.cfg']},
          scripts = ['src/bin/ride.py']
          )


if __name__ == "__main__":
    main()
