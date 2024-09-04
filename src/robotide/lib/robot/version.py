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

import re
import sys
from os import getenv

# Version number typically updated by running `invoke set-version <version>`.
# Run `invoke --help set-version` or see tasks.py for details.
VERSION = '3.1.2'  # Original library version
ROBOT_VERSION = getenv('ROBOT_VERSION')  # Set the version from environment, like "3.1.2"
if not ROBOT_VERSION:
    try:
        from robot.version import get_version as rf_get_version
    except ImportError:
        rf_get_version = None
    if rf_get_version is not None:
        # print(f"DEBUG: lib/version.py RF Version={rf_get_version(naked=True)}")
        ROBOT_VERSION = (rf_get_version(naked=True))
    else:
        ROBOT_VERSION = (7, 0, 1)  # Define here or use environment variable. Condition library alias with AS

if not isinstance(ROBOT_VERSION, tuple):
    try:
        ROBOT_VERSION = tuple(int(x) for x in ROBOT_VERSION.replace(',', '.').strip('()').split('.')[:])
    except (TypeError, ValueError):
        ROBOT_VERSION = (7, 0, 1)

ALIAS_MARKER = 'AS' if ROBOT_VERSION >= (6, 0, 0) else 'WITH NAME'


def get_version(naked=False):
    if naked:
        return re.split('(a|b|rc|.dev)', VERSION)[0]
    return VERSION


def get_full_version(program=None, naked=False):
    version = '%s %s (%s %s on %s)' % (program or '',
                                       get_version(naked),
                                       get_interpreter(),
                                       sys.version.split()[0],
                                       sys.platform)
    return version.strip()


def get_interpreter():
    if sys.platform.startswith('java'):
        return 'Jython'
    if sys.platform == 'cli':
        return 'IronPython'
    if 'PyPy' in sys.version:
        return 'PyPy'
    return 'Python'
