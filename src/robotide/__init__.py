#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

"""RIDE -- Robot Framework test data editor

Usage: ride.py [--noupdatecheck] [inpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened.

To disable update checker use --noupdatecheck.

RIDE's API is still evolving while the project is moving towards the 1.0
release. The most stable, and best documented, module is `robotide.pluginapi`.
"""

import sys
import os
from string import Template

errorMessageTemplate = Template("""$reason
You need to install wxPython $versions toolkit with unicode support to run RIDE.
See http://wxpython.org for more information.""")
supported_versions = ["2.8"]

try:
    import wxversion
    from wxversion import VersionError
    if sys.platform == 'darwin': # CAN NOT IMPORT IS_MAC AS THERE IS A wx IMPORT
        supported_versions.append("2.9")
    wxversion.select(supported_versions)
    import wx
    if "ansi" in wx.PlatformInfo:
        print errorMessageTemplate.substitute(reason="wxPython with ansi encoding is not supported", versions=" or ".join(supported_versions))
        sys.exit(1)
except ImportError:
    print errorMessageTemplate.substitute(reason="wxPython not found.", versions=supported_versions)
    sys.exit(1)
except VersionError:
    print errorMessageTemplate.substitute(reason="Wrong wxPython version.", versions=supported_versions)
    sys.exit(1)

# Insert bundled robot to path before anything else
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from robot.errors import DataError


sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))


def main(args):
    noupdatecheck, inpath = _parse_args(args)
    if len(args) > 2 or '--help' in args:
        print __doc__
        sys.exit()
    try:
        _run(inpath, not noupdatecheck)
    except DataError, err:
        print str(err) + '\n\nUse --help to get usage information.'

def _parse_args(args):
    if not args:
        return False, None
    noupdatecheck = (args[0] == '--noupdatecheck')
    inpath = args[-1] if not noupdatecheck or len(args) > 1 else None
    return noupdatecheck, inpath

def _run(inpath=None, updatecheck=True):
    from robotide.application import RIDE
    if inpath:
        inpath = unicode(inpath, sys.getfilesystemencoding())
    ride = RIDE(inpath, updatecheck)
    ride.MainLoop()


if __name__ == '__main__':
    main(sys.argv[1:])
