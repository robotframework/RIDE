#!/usr/bin/env python
# encoding=utf-8
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


import sys
from os.path import exists, join
from robotide.utils import PY2

__doc__ = """
Usage: python ride_postinstall.py [options] <-install|-remove>
    or python -m robotide.postinstall [options] <-install|-remove>
                -install - Installs a Desktop Shortcut to RIDE.
                -remove  - [TODO] Removes a Desktop Shortcut to RIDE.
       options: -q    - Quiet, don't ask user for confirmation.
                -f    - Force action.
                -help - This help.
""".strip()
# TODO: Add -remove, to remove desktop shortcut


def verify_install():
    try:
        from wx import version
    except ImportError as err:
        sys.stderr.write("No wxPython installation detected!"
                         "\n"
                         "Please ensure that you have wxPython installed "
                         "before running RIDE. "
                         "You can obtain wxPython from "
                         "https://wxpython.org/pages/downloads/\n"
                         "or pip install wxPython")
        return False
    else:
        sys.stderr.write("wxPython is installed.\n%s\n" % version())
        return True


def _askyesno(title, message, frame=None):
    import wx
    if frame is None:
        _ = wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = wx.MessageDialog(parent, message, title, wx.YES_NO |
                           wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    parent.Destroy()
    return result


def _askdirectory(title, initialdir, frame=None):
    import wx
    if frame is None:
        _ = wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = wx.DirDialog(parent, title, initialdir, style=wx.DD_DIR_MUST_EXIST)
    if dlg.ShowModal() == wx.ID_OK:
        result = dlg.GetPath()
    else:
        result = None
    dlg.Destroy()
    parent.Destroy()
    return result


def _create_desktop_shortcut_linux(frame=None):
    import os
    import subprocess
    import pwd
    DEFAULT_LANGUAGE = os.environ.get('LANG', '').split(':')
    # TODO: Add more languages
    desktop = {"de": "Desktop", "en": "Desktop", "es": "Escritorio",
               "fi": r"Työpöytä", "fr": "Bureau", "it": "Scrivania",
               "pt": r"Área de Trabalho"}
    if PY2:
        user = unicode(subprocess.check_output(['logname']).strip())
    else:
        user = str(subprocess.check_output(['logname']).strip(),
                   encoding='utf-8')
    # print("DEBUG: user is %s value %s" % (type(user), user))
    try:
        ndesktop = desktop[DEFAULT_LANGUAGE[0][:2]]
        if PY2:
            ndesktop = ndesktop.decode('utf-8')
        # print("DEBUG: ndesktop is %s" % type(ndesktop))
        directory = os.path.join("/home", user, ndesktop)
        defaultdir = os.path.join("/home", user, "Desktop")
        if not exists(directory):
            if exists(defaultdir):
                directory = defaultdir
            else:
                if not option_q:
                    directory = _askdirectory(title="Locate Desktop Directory",
                                              initialdir=os.path.join(
                                                  os.path.expanduser('~')),
                                              frame=frame)
                else:
                    directory = None
    except KeyError as kerr:
        if not option_q:
            directory = _askdirectory(title="Locate Desktop Directory",
                                      initialdir=os.path.join(
                                          os.path.expanduser('~')),
                                      frame=frame)
        else:
            directory = None
    if directory is None:
        sys.stderr.write("Desktop shortcut creation aborted!\n")
        return False
    try:
        if PY2:
            directory.decode('utf-8')
        # print("DEBUG: directory is %s" % directory)
        link = join(directory, "RIDE.desktop")
    except UnicodeError:
        link = join(directory.encode('utf-8'), "RIDE.desktop")
    if not exists(link) or option_f:
        if not option_q and not option_f:
            if not _askyesno("Setup", "Create desktop shortcut?", frame):
                return False
        roboticon = os.path.dirname(os.path.realpath(__file__)).\
            replace("postinstall", "widgets/robot.ico")
        with open(link, "w+") as shortcut:
            shortcut.write("#!/usr/bin/env xdg-open\n[Desktop Entry]\nExec="
                           "%s -m robotide.__init__\nComment=A Robot Framework"
                           " IDE\nGenericName=RIDE\n" % sys.executable)
            shortcut.write("Icon={0}\n".format(roboticon))
            shortcut.write("Name=RIDE\nStartupNotify=true\nTerminal=false\n"
                           "Type=Application\nX-KDE-SubstituteUID=false\n")
            uid = pwd.getpwnam(user).pw_uid
            os.chown(link, uid, -1)  # groupid == -1 means keep unchanged
            os.chmod(link, 0o744)


def _create_desktop_shortcut_mac(frame=None):
    import os
    import subprocess
    import pwd
    if PY2:
        user = unicode(subprocess.check_output(['logname']).strip())
    else:
        user = str(subprocess.check_output(['logname']).strip(),
                   encoding='utf-8')
    link = os.path.join("/Users", user, "Desktop", "RIDE.command")
    if not exists(link) or option_f:
        if not option_q and not option_f:
            if not _askyesno("Setup", "Create desktop shortcut?", frame):
                return False
        roboticon = "/Library/Python/{0}/site-packages/robotide/widgets/robot."
        "png".format(sys.version[:3])  # TODO: Find a way to change shortcut icon
        with open(link, "w+") as shortcut:
            shortcut.write("#!/bin/sh\n%s -m robotide.__init__ $* &\n" %
                           sys.executable)
        uid = pwd.getpwnam(user).pw_uid
        os.chown(link, uid, -1)  # groupid == -1 means keep unchanged
        os.chmod(link, 0o744)


def _create_desktop_shortcut_windows(frame=None):
    # Dependency of http://sourceforge.net/projects/pywin32/
    import os
    import sys
    try:
        from win32com.shell import shell, shellcon
    except ImportError:
        sys.stderr.write("Cannot create desktop shortcut.\nPlease install"
                         " pywin32 from https://github.com/mhammond/pywin32\n"
                         "or pip install pywin32")
        return False
    desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
    link = os.path.join(desktop, 'RIDE.lnk')
    icon = os.path.join(sys.prefix, 'Lib', 'site-packages', 'robotide',
                        'widgets', 'robot.ico')
    if not exists(link) or option_f:
        if not option_q and not option_f:
            if not _askyesno("Setup", "Create desktop shortcut?", frame):
                sys.stderr.write("Users can create a Desktop shortcut to RIDE "
                                 "with:\n%s -m robotide.postinstall -install\n"
                                 % sys.executable.replace('python.exe', 'pythonw.exe'))
                return False
        import pythoncom
        shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                              pythoncom.CLSCTX_INPROC_SERVER,
                                              shell.IID_IShellLink)
        command_args = " -c \"from robotide import main; main()\""
        shortcut.SetPath(sys.executable.replace('python.exe', 'pythonw.exe'))
        shortcut.SetArguments(command_args)
        shortcut.SetDescription("Robot Framework testdata editor")
        shortcut.SetIconLocation(icon, 0)
        persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
        persist_file.Save(link, 0)


def create_desktop_shortcut(platform, frame=None):
    if platform.startswith("linux"):
        return _create_desktop_shortcut_linux(frame)
    elif platform.startswith("darwin"):
        return _create_desktop_shortcut_mac(frame)
    elif platform.startswith("win"):
        return _create_desktop_shortcut_windows(frame)
    else:
        sys.stderr.write("Unknown platform {0}: Failed to create desktop short"
                         "cut.".format(platform))
        return False


def caller(frame, platform):
    # Options
    global option_q
    global option_f
    option_q = None
    option_f = frame is not None
    # We don't verify install because called from RIDE
    return create_desktop_shortcut(platform, frame)


def main(args):
    # Options
    global option_q
    global option_f
    option_q = option_f = None
    option_q = next((x for x in args if x == "-q"), None)
    if option_q is not None:
        del args[args.index(option_q)]
        option_q = True
    option_f = next((x for x in args if x == "-f"), None)
    if option_f is not None:
        del args[args.index(option_f)]
        option_f = True
    arg = args[-1] if len(args) == 1 and args[-1] in ['-install', '-remove',
                                                      '-help'] else None
    if arg == '-install':
        doit = True
        platform = sys.platform.lower()
        doit = verify_install()
        if doit:
            create_desktop_shortcut(platform)
    elif arg == '-remove':
        sys.stderr.write("Sorry, -remove is not implemented yet.\n")
    else:
        sys.stderr.write(__doc__)
        sys.stderr.write("\n")


if __name__ == '__main__':
    main(sys.argv[1:])
