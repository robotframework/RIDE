#!/usr/bin/env python

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

import argparse
import sys

try:
    from robotide import version
except ImportError:
    print("Error getting RIDE version!")
    sys.exit(1)

errorMessage = """wxPython not found.\n
RIDE depends on wx (wxPython). Known versions for Python3 are: 4.0.7.post2, 4.1.1 and 4.2.3.\
At the time of this release the current wxPython version is 4.2.3.\
You can install with 'pip install wxPython' on most operating systems, or find the \
the download link from https://wxPython.org/"""

if __name__ == '__main__' and 'robotide' not in sys.modules:
    from pathlib import Path
    robotide_dir = Path(__file__).absolute().parent  # zipsafe
    sys.path = [str(robotide_dir.parent)] + [p for p in sys.path if Path(p) != robotide_dir]

parser = argparse.ArgumentParser(prog='ride', description='RIDE is an IDE for Robot Framework test cases and tasks.',
                    epilog='See information about Robot Framework ecosystem at https://robotframewok.org/',
                    add_help=False)
parser.add_argument('inpath', nargs='?', help='Path to a test data file or'
                                         ' directory to be opened.')
parser.add_argument('-n', '--noupdatecheck', action='store_true', help='To disable update check.')
parser.add_argument('-d', '--debugconsole', action='store_true',
                    help='To start debug console for RIDE problem debugging, and wxPython inspection tool.')
parser.add_argument('-s', '--settingspath', default=None, help='<full path|settings filename>\n'
                                                 'To use different settings use the option --settingspath followed by'
                                                 ' the path to the settings file or file name.')
parser.add_argument('-v', '--version', action='version', version=f'{version.VERSION}',
                    help='To see RIDE\'s version.')
parser.add_argument('-h', '--help', action='help', help='RIDE can be started either without any '
                                         'arguments or by giving a path to a test data file or'
                                         ' directory to be opened.')
arguments = parser.parse_args()

def _parse_args(args):
    if not args:
        return False, False, None, None
    print(f"{args.noupdatecheck=} {args.debugconsole=} {args.settingspath=} {args.inpath=}")

    #return noupdatecheck, debug_console, settings_path, inpath
    return (args.noupdatecheck, args.debugconsole, args.settingspath, args.inpath)

"""
Usage: ride.py [--noupdatecheck] [--debugconsole] [--settingspath <full path|settings filename>] [--version] [inpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened.

To disable update checker use --noupdatecheck.

To start debug console for RIDE problem debugging use --debugconsole option.

To use different settings use the option --settingspath followed by the path to the settings file or file name.

To see RIDE's version use --version.
"""

parsed_args = _parse_args(arguments)
try:
    import wx
    import wx.lib.inspection
    from wx import Colour, Size
except ModuleNotFoundError:
    print(errorMessage)
    sys.exit(1)

from robotide import mainrun

mainrun(parsed_args)
