#  Copyright 2008-2015 Nokia Solutions and Networks
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
import re
import sys
import subprocess

from robotide.context import SYSLOG, LIBRARY_XML_DIRECTORY


def find_installed_robot_libraries(previous_rf_version):
    """Discover installed Robot Framework and it's test libraries.

    Create library spec files for RF the test libraries if they do not exist or
    if the RF version has changed.

    Returns the version of the found RF or `None`.
    """
    output = _run_python_command(
        ['import robot; print robot.__file__ + ", " + robot.__version__'])
    robot_found = 'ImportError' not in output
    if robot_found:
        rf_file, rf_version = output.strip().split(', ')
        SYSLOG("Found Robot Framework version {0} from '{1}'.".format(
            rf_version, os.path.dirname(rf_file)))
        _create_standard_library_spec_files(rf_version, previous_rf_version)
        return rf_version
    else:
        SYSLOG('Robot Framework installation not found on the system.')
        return None


def _create_standard_library_spec_files(rf_version, previous_rf_version):
    stdlib_names = _get_standard_library_names(rf_version)
    for name in [n for n in stdlib_names if n not in ('Remote', 'Reserved')]:
        outpath = os.path.join(LIBRARY_XML_DIRECTORY, '{0}.xml'.format(name))
        if not os.path.exists(outpath) or rf_version != previous_rf_version:
            _run_python_command(['robot.libdoc', name, outpath], mode='m')
            SYSLOG("Created library spec file: '{0}'.".format(outpath))


def _get_standard_library_names(rf_version):
    def stdlib_command():
        major_minor = re.split('(a|b|rc|.dev)', rf_version)[0].split('.')[:2]
        if [int(i) for i in major_minor] >= [2, 9]:
            return "from robot.libraries import STDLIBS; " \
                   "print ','.join(STDLIBS)"
        else:
            return "from robot.running.namespace import STDLIB_NAMES; " \
                   "print ','.join(STDLIB_NAMES)"
    output = _run_python_command([stdlib_command()])
    if 'ImportError' not in output:
        return output.strip().split(',')
    else:
        SYSLOG('Resolving RF standard library names failed: {0}.'
               .format(output))
        return []


def _run_python_command(command, mode='c'):
    cmd = [sys.executable, '-{0}'.format(mode)] + command
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    return output
