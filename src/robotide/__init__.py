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

Usage: ride.py [--noupdatecheck] [--debugconsole] [inpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened.

To disable update checker use --noupdatecheck.

To start debug console for RIDE problem debugging use --debugconsole option.

RIDE's API is still evolving while the project is moving towards the 1.0
release. The most stable, and best documented, module is `robotide.pluginapi`.
"""

import sys
import os
from string import Template
import traceback
import threading

errorMessageTemplate = Template("""$reason
You need to install wxPython $versions toolkit with unicode support to run RIDE.
wxPython 2.8.12.1 can be downloaded from http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/""")
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
except ImportError as e:
    if "no appropriate 64-bit architecture" in e.message.lower() and sys.platform == 'darwin':
        print "python should be executed in 32-bit mode to support wxPython on mac. Check BUILD.rest for details"
    else:
        print errorMessageTemplate.substitute(reason="wxPython not found.", versions=" or ".join(supported_versions))
    sys.exit(1)
except VersionError:
    print errorMessageTemplate.substitute(reason="Wrong wxPython version.", versions=" or ".join(supported_versions))
    sys.exit(1)

# Insert bundled robot to path before anything else
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from robot.errors import DataError


sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))


def main(*args):
    noupdatecheck, debug_console, inpath = _parse_args(args)
    if len(args) > 3 or '--help' in args:
        print __doc__
        sys.exit()
    try:
        _run(inpath, not noupdatecheck, debug_console)
    except DataError, err:
        print str(err) + '\n\nUse --help to get usage information.'

def _parse_args(args):
    if not args:
        return False, False, None
    noupdatecheck = '--noupdatecheck' in args
    debug_console = '--debugconsole' in args
    inpath = args[-1] if args[-1] not in ['--noupdatecheck', '--debugconsole'] else None
    return noupdatecheck, debug_console, inpath

def _run(inpath=None, updatecheck=True, debug_console=False):
    try:
        from robotide.application import RIDE
    except ImportError:
        _show_old_wxpython_warning_if_needed()
        raise
    if inpath:
        inpath = unicode(inpath, sys.getfilesystemencoding())
    ride = RIDE(inpath, updatecheck)
    _show_old_wxpython_warning_if_needed(ride.frame)
    if debug_console:
        _start_debug_console(ride)
    ride.MainLoop()

def _show_old_wxpython_warning_if_needed(parent=None):
    if wx.VERSION >= (2, 8, 12, 1):
        return
    title = 'Please upgrade your wxPython installation'
    message = ('RIDE officially supports wxPython 2.8.12.1. '
               'Your current version is %s.\n\n'
               'Older wxPython versions are known to miss some features used by RIDE. '
               'Notice also that wxPython 3.0 is not yet supported.\n\n'
               'wxPython 2.8.12.1 packages can be found from\n'
               'http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/.'
               % wx.VERSION_STRING)
    style = wx.ICON_EXCLAMATION
    if not parent:
        app = wx.PySimpleApp()
        parent = wx.Frame(None, size=(0,0))
    wx.MessageDialog(parent, message, title, style).ShowModal()

def _print_stacks():
    id2name = dict((th.ident, th.name) for th in threading.enumerate())
    for threadId, stack in sys._current_frames().items():
        print(id2name[threadId])
        traceback.print_stack(f=stack)

def _start_debug_console(ride):
    import code
    help_string = """\
RIDE - access to the running application
print_stacks() - print current stack traces
"""
    console = code.InteractiveConsole(locals={'RIDE':ride, 'print_stacks':_print_stacks})
    thread = threading.Thread(target=lambda: console.interact(help_string))
    thread.start()

if __name__ == '__main__':
    main(sys.argv[1:])
