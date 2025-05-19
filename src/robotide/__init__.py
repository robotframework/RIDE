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
import os
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
# arguments = parser.parse_args()

try:
    import wx
    import wx.lib.inspection
    from wx import Colour, Size
except ModuleNotFoundError:
    print(errorMessage)
    sys.exit(1)

# Insert bundled robot to path before anything else
sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))


def main(*args):
    _replace_std_for_win()
    arguments = parser.parse_args()
    noupdatecheck = arguments.noupdatecheck
    debugconsole = arguments.debugconsole
    settingspath = arguments.settingspath
    inpath = arguments.inpath  # _parse_args(*args)
    # print(f"DEBUG: main.py {noupdatecheck=} {debugconsole=} {settingspath=} {inpath=}")
    try:
        _run(inpath, not noupdatecheck, debugconsole, settingspath=settingspath)
    except Exception:  # DEBUG
        import traceback
        traceback.print_exception(*sys.exc_info())
        sys.stderr.write('\n\nUse --help to get usage information.\n')


def _run(inpath=None, updatecheck=True, debug_console=False, settingspath=None):
    # print(f"DEBUG: ENTER _run {inpath=}, {updatecheck=}, {debug_console=}")
    try:
        from robotide.application import RIDE
        from robotide.application import debugconsole
    except ImportError:
        _show_old_wxpython_warning_if_needed()
        raise
    ride = RIDE(inpath, updatecheck, settingspath=settingspath)
    if wx.VERSION <= (4, 0, 4, '', ''):
        _show_old_wxpython_warning_if_needed(ride.frame)
    else:
        wx.CallAfter(_show_old_wxpython_warning_if_needed, ride.frame)
    if debug_console:
        wx.lib.inspection.InspectionTool().Show()
        debugconsole.start(ride)
    ride.MainLoop()


def _replace_std_for_win():

    class NullStream:
        def close(self):
            """ Override """
            pass

        def flush(self):
            """ Override """
            pass

        def write(self, line):
            """ Override """
            pass

        def writelines(self, sequence):
            """ Override """
            pass

    if sys.executable.endswith('.exe'):
        # In windows, when launching RIDE with pythonw.exe
        # sys.stderr and sys.stdout will be None
        if sys.stderr is None:
            sys.stderr = NullStream()
        if sys.stdout is None:
            sys.stdout = NullStream()


def _show_old_wxpython_warning_if_needed(parent=None):
    # print("DEBUG: ENTER _show_old_wxpython_warning_if_needed")
    if wx.VERSION <= (4, 0, 4, '', ''):
        title = "Please upgrade your wxPython installation"
        message = ("RIDE needs a newer wxPython version. Your current "
                   "version is %s."
                   "\n"
                   "At the time of this release the current wxPython version is 4.2.1. See "
                   "https://wxPython.org/ for downloads and instructions."
                   % wx.VERSION_STRING)
        style = wx.ICON_EXCLAMATION
        if not parent:
            _ = wx.App()
            parent = wx.Frame(None, size=Size(0, 0))
        sys.stderr.write("{0}\n{1}\n".format(title, message))
        dlg = wx.MessageDialog(parent, message=message, caption=title, style=style)
        dlg.ShowModal()


if __name__ == '__main__':
    main(*sys.argv[1:])
