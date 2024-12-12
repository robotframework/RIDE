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

from .desktopshortcut import ShortcutPlugin

import sys
try:
    import wx
    from wx import Colour
except ImportError:
    sys.stderr.write("No wxPython installation detected!"
                     "\n"
                     "Please ensure that you have wxPython installed "
                     "before running RIDE. "
                     "You can obtain wxPython from "
                     "https://wxpython.org/pages/downloads/\n"
                     "or pip install wxPython")
    exit(-1)

from os import environ, getlogin
from os.path import exists, join
from robotide.widgets import RIDEDialog

__doc__ = """
Usage: python ride_postinstall.py [options] <-install|-remove>
    or python -m robotide.postinstall [options] <-install|-remove>
                -install - Installs a Desktop Shortcut to RIDE.
                -remove  - [TODO] Removes a Desktop Shortcut to RIDE.
       options: -q    - Quiet, don't ask user for confirmation.
                -f    - Force action.
                -help - This help.
""".strip()
# DEBUG: Add -remove, to remove desktop shortcut

ROBOT_ICO = "robot.ico"
DEFAULT_LANGUAGE = environ.get('LANG', '').split(':')


def verify_install():
    try:
        from wx import version
    except ImportError:
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


class MessageDialog(RIDEDialog):
    def __init__(self, parent, message, title, ttl=10, no_default=False):
        RIDEDialog.__init__(self, title=title, parent=parent, size=(300, 200))

        self.CenterOnScreen(wx.BOTH)
        self.timeToLive = ttl
        st_msg = []
        for msg in message.split('\n'):
            st_msg.append(wx.StaticText(self, -1, msg))
        self.settimetolivemsg = wx.StaticText(self, -1, 'Closing this dialog box in %ds...' % self.timeToLive)
        vbox = wx.BoxSizer(wx.VERTICAL)
        for sp_msg in st_msg:
            vbox.Add(sp_msg, 0, wx.ALIGN_LEFT | wx.TOP, 10)
        vbox.Add(self.settimetolivemsg, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        self.SetSizer(vbox)
        self.SetAffirmativeId(wx.ID_OK)
        self._create_buttons(None, no_default)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self.timer = wx.Timer(self)
        self.timer.Start(1000)  # Generate a timer event every second
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.on_no, id=wx.ID_NO)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_pressed)

    def on_key_pressed(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_NO)
        event.Skip()

    def on_cancel(self, evt):
        _ = evt
        self.EndModal(wx.ID_NO)

    def on_close(self, evt):
        self.on_cancel(evt)

    def on_no(self, evt):
        self.on_cancel(evt)

    def on_timer(self, evt):
        _ = evt
        self.timeToLive -= 1
        self.settimetolivemsg.SetLabel('Closing this dialog box in %ds...' % self.timeToLive)

        if self.timeToLive == 0:
            self.timer.Stop()
            self.EndModal(wx.ID_NO)

    def _create_buttons(self, sizer, no_default=False):
        flags = wx.OK | wx.CANCEL
        if no_default:
            flags |= wx.NO_DEFAULT
        buttons = self.CreateStdDialogButtonSizer(flags)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        for item in self.GetChildren():
            if isinstance(item, (wx.Button, wx.BitmapButton)):
                item.SetBackgroundColour(Colour(self.color_secondary_background))
                # item.SetOwnBackgroundColour(Colour(self.color_secondary_background))
                item.SetForegroundColour(Colour(self.color_secondary_foreground))
                # item.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        self.Sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)


def _askyesno(title, message, frame=None,  no_default=False):
    if frame is None:
        _ = wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = MessageDialog(parent, message, title, ttl=8, no_default=no_default)
    dlg.Fit()
    result = dlg.ShowModal() in [wx.ID_YES, wx.ID_OK]
    print("Result %s" % result)
    if dlg:
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
    from os.path import expanduser
    from os import chmod, chown
    from stat import S_IRWXU
    import subprocess
    import pwd
    import sysconfig
    # DEBUG: Add more languages
    desktop = {"de": "Desktop", "en": "Desktop", "es": "Escritorio",
               "fi": r"Työpöytä", "fr": "Bureau", "it": "Scrivania",
               "pt": r"Área de Trabalho", "zh": "Desktop"}
    user = getlogin()
    try:
        ndesktop = desktop[DEFAULT_LANGUAGE[0][:2]]
        directory = join("/home", user, ndesktop)
        defaultdir = join("/home", user, "Desktop")
        if not exists(directory):
            if exists(defaultdir):
                directory = defaultdir
            else:
                if not option_q:
                    directory = _askdirectory(title="Locate Desktop Directory",
                                              initialdir=join(expanduser('~')),
                                              frame=frame)
                else:
                    directory = None
    except KeyError:
        if not option_q:
            directory = _askdirectory(title="Locate Desktop Directory",
                                      initialdir=join(expanduser('~')),
                                      frame=frame)
        else:
            directory = None
    if directory is None:
        sys.stderr.write("Desktop shortcut creation aborted!\n")
        return False
    try:
        link = join(directory, "RIDE.desktop")
    except UnicodeError:
        link = join(directory.encode('utf-8'), "RIDE.desktop")
    if not exists(link) or option_f:
        if not option_q and not option_f:
            if not _askyesno("Setup", "Create desktop shortcut?", frame):
                return False
        roboticon = join(sysconfig.get_paths()["purelib"], "robotide", "widgets", ROBOT_ICO)
        if not exists(roboticon):
            try:
                import robotide as _
                roboticon = join(_.__path__[0], "widgets", ROBOT_ICO)
            except ImportError:
                _ = None
            if not exists(roboticon):
                roboticon = join("FIXME: find correct path to: .../site-packages/", "robotide", "widgets", ROBOT_ICO)
        with open(link, "w+") as shortcut:
            shortcut.write(f"#!/usr/bin/env xdg-open\n[Desktop Entry]\n"
                           f"Exec={sys.executable} -m robotide.__init__\n"
                           f"Comment=A Robot Framework IDE\nGenericName=RIDE\n"
                           f"Icon={roboticon}\n"
                           f"Name=RIDE\nStartupNotify=true\nTerminal=false\n"
                           "Type=Application\nX-KDE-SubstituteUID=false\n")
            uid = pwd.getpwnam(user).pw_uid
            chown(link, uid, -1)  # groupid == -1 means keep unchanged
            chmod(link, S_IRWXU)


def _create_desktop_shortcut_mac(frame=None):
    import os
    import shutil
    import subprocess
    ride_app_name = 'RIDE.app'
    application_path = '/Applications'
    ride_app_pc_path = os.path.join(application_path, ride_app_name)
    ride_app_module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ride_app_name)

    if not exists(ride_app_pc_path) or option_f:
        if not option_q and not option_f and not _askyesno("Setup", "Create application shortcut?", frame):
            return False
        app_script = os.path.join(ride_app_module_path, 'Contents', 'MacOS', 'RIDE')
        with open(app_script, 'w+') as shortcut:
            shortcut.write("#!/bin/sh\nPAL=$PATH\nfor i in `cat /etc/paths`\n    do\n        PAL=\"$PAL:$i\"\n"
                           "    done\nPATH=$PAL\nexport $PATH\n{} -m robotide.__init__ $* 2>"
                           " /dev/null &\n".format(sys.executable))
        if exists(ride_app_pc_path):
            shutil.rmtree(ride_app_pc_path, True)
        shutil.copytree(ride_app_module_path, ride_app_pc_path)
        user = getlogin()
        user_desktop_link = '/Users/' + user + '/Desktop/' + ride_app_name
        if exists(user_desktop_link):
            os.remove(user_desktop_link)
        try:
            os.symlink(ride_app_pc_path, user_desktop_link)
        except Exception as e:
            print(e)


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
    public_link = os.path.join(os.getenv('PUBLIC'), 'Desktop', 'RIDE.lnk')
    icon = os.path.join(sys.prefix, 'Lib', 'site-packages', 'robotide',
                        'widgets', 'robot.ico')
    if not (exists(public_link) or exists(link)) or option_f:
        if not option_q and not option_f:
            if not _askyesno("Setup", "Create desktop shortcut?", frame):
                sys.stderr.write("Users can create a Desktop shortcut to RIDE "
                                 "with:\n%s -m robotide.postinstall -install\n"
                                 % sys.executable)
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
        from pywintypes import com_error
        try:
            persist_file.Save(public_link, 0)
            sys.stderr.write("Desktop shortcut created for all users.")
        except com_error:
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


def main(*args):
    myargs = list(args[:])
    # Options
    global option_q
    global option_f
    option_q = option_f = None
    option_q = next((x for x in myargs if x == "-q"), None)
    if option_q is not None:
        del myargs[myargs.index(option_q)]
        option_q = True
    option_f = next((x for x in myargs if x == "-f"), None)
    if option_f is not None:
        del myargs[myargs.index(option_f)]
        option_f = True
    arg = myargs[-1] if len(myargs) == 1 and myargs[-1] in ['-install', '-remove',
                                                      '-help'] else None
    if arg == '-install':
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
    main(*sys.argv[1:])
