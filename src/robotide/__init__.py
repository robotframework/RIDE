#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

Usage: ride.py [inpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened.

RIDE's API is still evolving while the project is moving towards the 1.0
release. The most stable, and best documented, module is `robotide.pluginapi`.
"""

import sys
import os
try:
    import wxversion
    from wxversion import VersionError
    wxversion.select('2.8')
except ImportError:
    print """wxPython not found.
You need to install wxPython 2.8 toolkit with unicode support to run RIDE.
See http://wxpython.org for more information."""
    sys.exit(1)
except VersionError:
    print """Wrong wxPython version.
You need to install wxPython 2.8 toolkit with unicode support to run RIDE.
See http://wxpython.org for more information."""
    sys.exit(1)

# Insert bundled robot to path before anything else
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from robotide.errors import DataError


sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))


def main(args):
    if len(args) > 1 or '--help' in args:
        print __doc__
        sys.exit()
    try:
        _run(*args)
    except DataError, err:
        print str(err) + '\n\nUse --help to get usage information.'


def _run(inpath=None):
    from robotide.application import RIDE
    if inpath:
        inpath = unicode(inpath, sys.getfilesystemencoding())
    ride = RIDE(inpath)
    ride.MainLoop()


if __name__ == '__main__':
    main(sys.argv[1:])
