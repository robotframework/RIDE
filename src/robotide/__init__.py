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

"""RIDE -- Robot Framework test data editor

Usage: ride.py [--noupdatecheck] [--debugconsole] [--version] [inpath]

RIDE can be started either without any arguments or by giving a path to a test
data file or directory to be opened.

To disable update checker use --noupdatecheck.

To start debug console for RIDE problem debugging use --debugconsole option.

To see RIDE's version use --version.

RIDE's API is still evolving while the project is moving towards the 1.0
release. The most stable, and best documented, module is `robotide.pluginapi`.
"""

import sys
import os
from string import Template

wxPythonDownload = """wxPython 2.8.12.1 packages can be found from
http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/."""

errorMessageTemplate = Template("""$reason
You need to install wxPython 2.8.12.1 with unicode support to run RIDE.
{}""".format(wxPythonDownload))

try:
    import wx
except ImportError as e:
    if "no appropriate 64-bit architecture" in e.message.lower() and \
       sys.platform == 'darwin':
        print("python should be executed in 32-bit mode with wxPython on OSX.")
    else:
        print(errorMessageTemplate.substitute(reason="wxPython not found."))
    sys.exit(1)

if "ansi" in wx.PlatformInfo:
    print(errorMessageTemplate.substitute(
        reason="wxPython with ansi encoding is not supported"))
    sys.exit(1)


# Insert bundled robot to path before anything else
sys.path.append(os.path.join(os.path.dirname(__file__), 'spec'))


def main(*args):
    noupdatecheck, debug_console, inpath = _parse_args(args)
    if len(args) > 3 or '--help' in args:
        print(__doc__)
        sys.exit()
    if '--version' in args:
        try:
            from robotide import version
        except ImportError:
            print("Error getting RIDE version!")
            sys.exit(1)
        print(version.VERSION)
        sys.exit(0)
    try:
        _run(inpath, not noupdatecheck, debug_console)
    except Exception:
        import traceback
        traceback.print_exception(*sys.exc_info())
        sys.stderr.write('\n\nUse --help to get usage information.\n')


def _parse_args(args):
    if not args:
        return False, False, None
    noupdatecheck = '--noupdatecheck' in args
    debug_console = '--debugconsole' in args
    inpath = args[-1] if args[-1] not in ['--noupdatecheck',
                                          '--debugconsole'] else None
    return noupdatecheck, debug_console, inpath


def _run(inpath=None, updatecheck=True, debug_console=False):
    try:
        from robotide.application import RIDE
        from robotide.application import debugconsole
    except ImportError:
        _show_old_wxpython_warning_if_needed()
        raise
    _show_old_wxpython_warning_if_needed()
    if inpath:
        inpath = unicode(inpath, sys.getfilesystemencoding())
    ride = RIDE(inpath, updatecheck)
    if debug_console:
        debugconsole.start(ride)
    ride.MainLoop()


def _show_old_wxpython_warning_if_needed(parent=None):
    if wx.VERSION >= (2, 8, 12, 1, ''):
        if wx.VERSION > (2, 8, 12, 1, ''):
            title = "Please be aware of untested wxPython installation"
            message = """
RIDE officially supports wxPython 2.8.12.1. Your current version is {0}.

There are significant changes in newer wxPython versions. Notice that RIDE is
still under development for wxPython 3.0.2 and newer (wxPython-Phoenix).
{1}""".format(wx.VERSION_STRING, wxPythonDownload)
            style = wx.OK | wx.ICON_INFORMATION | wx.CENTER
            if not parent:
                _ = wx.App()
                parent = wx.Frame(None, size=(0, 0))
            sys.stderr.write("{0}\n{1}\n".format(title, message))
            wx.MessageDialog(parent, message=message, caption=title,
                             style=style).ShowModal()
    else:
        title = "Please upgrade your wxPython installation"
        message = """
RIDE officially supports wxPython 2.8.12.1. Your current version is %{0}.

Older wxPython versions are known to miss some features used by RIDE.
Notice also that wxPython 3.0 is considered experimental.
{1}""".format(wx.VERSION_STRING, wxPythonDownload)
        style = wx.ICON_EXCLAMATION
        if not parent:
            _ = wx.App()
            parent = wx.Frame(None, size=(0, 0))
        sys.stderr.write("{0}\n{1}\n".format(title, message))
        wx.MessageDialog(parent, message=message, caption=title,
                         style=style).ShowModal()


if __name__ == '__main__':
    main(sys.argv[1:])
