#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

Usage: ride.py [inpath] [outpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened. RIDE can also be used for 'tidying'
Robot Framework test data by giving both ``inpath`` and ``outpath`` arguments.
Tidying works for both test case and resource files, but it does not work with
test data directories. When RIDE is used like this, no GUI is opened.

RIDE's API is still evolving while the project is moving towards the 1.0
release. The most stable, and best documented, module is `robotide.pluginapi`.
"""

import sys
import os
import wxversion
wxversion.select('2.9')

# TODO: Remove when robot has been released with this patch
import robotpatch
from robotide.errors import DataError


sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))


def main(args):
    if len(args) > 2 or '--help' in args:
        print __doc__
        sys.exit()
    try:
        if len(args) < 2:
            _run(*args)
        else:
            _tidy(*args)
    except DataError, err:
        print str(err) + '\n\nUse --help to get usage information.'


def _run(inpath=None):
    from robotide.application import RIDE
    ride = RIDE(inpath)
    ride.MainLoop()


def _tidy(inpath, outpath):
    from robotide.application import ChiefController
    if not os.path.exists(inpath):
        raise DataError('Given input file does not exist.')
    if not os.path.isfile(inpath):
        raise DataError('Tidy functionality only supports single files.')
    data = ChiefController(inpath)
    if data.suite:
        item = data.suite
    else:
        item = data.resources[0]
    item.source = outpath
    item.dirty = True
    print 'Tidying %s -> %s' % (inpath, outpath)
    item.serialize()


if __name__ == '__main__':
    main(sys.argv[1:])
