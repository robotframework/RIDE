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
from .mocks import FakeSettings, FakeApplication, MessageRecordingLoadObserver, FakeEditor, UIUnitTestBase
from .setting_utils import TestSettingsHelper

if os.sep == '\\':
    CIF = True
else:
    try:
        CIF = os.listdir('/tmp') == os.listdir('/TMP')
    except OSError:
        CIF = False

DATAPATH = os.path.join(
    os.path.abspath(os.path.split(__file__)[0]), 'robotdata')
sys.path.append(os.path.join(DATAPATH, 'put_into_python_path'))
SUITEPATH = os.path.join(DATAPATH, 'testsuite')
COMPLEX_SUITE_PATH = os.path.join(SUITEPATH, 'everything.robot')
MINIMAL_SUITE_PATH = os.path.join(SUITEPATH, 'minimal.robot')
NO_RIDE_PATH = os.path.join(DATAPATH, 'no_ride', 'no_ride.html')
NO_RIDE_RESOURCE_PATH = os.path.join(
    DATAPATH, 'no_ride', 'no_ride_resource.robot')
_RESOURCE_DIR = os.path.join(DATAPATH, 'resources')
RELATIVE_PATH_TO_RESOURCE_FILE = os.path.join('resources', 'resource.resource')
RESOURCE_PATH = os.path.normpath(
    os.path.join(DATAPATH, RELATIVE_PATH_TO_RESOURCE_FILE))
RESOURCE_PATH2 = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource2.robot'))
RESOURCE_PATH3 = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource3.robot'))
RESOURCE_PATH_TXT = os.path.normpath(
    os.path.join(_RESOURCE_DIR, 'resource.robot'))
INVALID_PATH = os.path.join(SUITEPATH, 'invalid.robot')
EXTERNAL_RES_UNSORTED_PATH = os.path.join(
    DATAPATH, 'external_resources_unsorted', 'suite')

PATH_RESOURCE_NAME = 'pathresource.robot' if CIF else 'PathResource.robot'
