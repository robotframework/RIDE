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

# The following import is needed for wx.select() to work properly
import robotide as _
import os
import sys
import wx

from robot.utils.normalizing import _CASE_INSENSITIVE_FILESYSTEM

from mocks import MockSerializer, FakeSuite, FakeDirectorySuite, FakeTestCase,\
    FakeUserKeyword, FakeResource, FakeApplication
from setting_utils import TestSettingsHelper

DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        'robotdata')
sys.path.append(os.path.join(DATAPATH, 'put_into_python_path'))
SUITEPATH = os.path.join(DATAPATH, 'testsuite')
COMPLEX_SUITE_PATH = os.path.join(SUITEPATH, 'everything.html')
MINIMAL_SUITE_PATH = os.path.join(SUITEPATH, 'minimal.html')
NO_RIDE_PATH = os.path.join(DATAPATH, 'no_ride', 'no_ride.html')
NO_RIDE_RESOURCE_PATH = os.path.join(DATAPATH, 'no_ride', 'no_ride_resource.html')
RESOURCE_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources', 'resource.html'))
INVALID_PATH = os.path.join(SUITEPATH, 'invalid.html')

PATH_RESOURCE_NAME = _CASE_INSENSITIVE_FILESYSTEM and 'pathresource.html' or 'PathResource.html'

PYAPP_REFERENCE = wx.PySimpleApp()
