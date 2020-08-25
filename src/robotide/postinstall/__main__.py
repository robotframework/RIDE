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
try:
    import wx
except ImportError:
    sys.stderr.write("No wxPython installation detected!"
                     "\n"
                     "Please ensure that you have wxPython installed "
                     "before running RIDE. "
                     "You can obtain wxPython from "
                     "https://wxpython.org/pages/downloads/\n"
                     "or pip install wxPython")
    exit(-1)

from os.path import exists, join

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


class MessageDialog(wx.Dialog):
    def __init__(self, message, title, ttl=10):
        wx.Dialog.__init__(self, None, -1, title, size=(300, 200))
        self.CenterOnScreen(wx.BOTH)
        self.timeToLive = ttl

        std_btn_sizer = self.CreateStdDialogButtonSizer(wx.YES_NO)
        st_msg = wx.StaticText(self, -1, message)
        self.settimetolivemsg = wx.StaticText(self, -1, 'Closing this dialog box in %ds...' % self.timeToLive)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(st_msg, 0, wx.ALIGN_CENTER | wx.TOP, 40)
        vbox.Add(self.settimetolivemsg, 0, wx.ALIGN_CENTER | wx.TOP, 10)
        vbox.Add(std_btn_sizer, 1, wx.ALIGN_CENTER | wx.TOP, 10)
        self.SetSizer(vbox)
        self.SetAffirmativeId(wx.ID_YES)

        self.timer = wx.Timer(self)
        self.timer.Start(1000)  # Generate a timer event every second
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnNo, id=wx.ID_NO)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPressed)

    def OnKeyPressed(self, event):
        key_code = event.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_NO)
        event.Skip()

    def OnCancel(self, evt):
        self.EndModal(wx.ID_NO)

    def OnClose(self, evt):
        self.EndModal(wx.ID_NO)

    def OnNo(self, evt):
        self.EndModal(wx.ID_NO)

    def onTimer(self, evt):
        self.timeToLive -= 1
        self.settimetolivemsg.SetLabel('Closing this dialog box in %ds...' % self.timeToLive)

        if self.timeToLive == 0:
            self.timer.Stop()
            self.EndModal(wx.ID_NO)


def _askyesno(title, message, frame=None):
    if frame is None:
        _ = wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = MessageDialog(message, title, ttl=8)
    result = dlg.ShowModal() == wx.ID_YES
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
    from os import environ, chmod, chown
    import subprocess
    import pwd
    import sysconfig
    DEFAULT_LANGUAGE = environ.get('LANG', '').split(':')
    # TODO: Add more languages
    desktop = {"de": "Desktop", "en": "Desktop", "es": "Escritorio",
               "fi": r"Työpöytä", "fr": "Bureau", "it": "Scrivania",
               "pt": r"Área de Trabalho"}
    user = str(subprocess.check_output(['logname']).strip(), encoding='utf-8')
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
        roboticon = join(sysconfig.get_paths()["purelib"], "robotide", "widgets", "robot.ico")
        if not exists(roboticon):
            try:
                import robotide as _
                roboticon = join(_.__path__[0], "widgets", "robot.ico")
            except ImportError:
                pass
            if not exists(roboticon):
                roboticon = join("FIXME: find correct path to: .../site-packages/", "robotide", "widgets", "robot.ico")
        with open(link, "w+") as shortcut:
            shortcut.write(f"#!/usr/bin/env xdg-open\n[Desktop Entry]\n"
                           f"Exec={sys.executable} -m robotide.__init__\n"
                           f"Comment=A Robot Framework IDE\nGenericName=RIDE\n"
                           f"Icon={roboticon}\n"
                           f"Name=RIDE\nStartupNotify=true\nTerminal=false\n"
                           "Type=Application\nX-KDE-SubstituteUID=false\n")
            uid = pwd.getpwnam(user).pw_uid
            chown(link, uid, -1)  # groupid == -1 means keep unchanged
            chmod(link, 0o744)


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
        user = str(subprocess.check_output(['logname']).strip(), encoding='utf-8')
        user_desktop_link = '/Users/' + user + '/Desktop/' + ride_app_name
        if exists(user_desktop_link):
            os.remove(user_desktop_link)
        try:
            os.symlink(ride_app_pc_path, user_desktop_link)
        except Exception:
            pass


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
            sys.stderr.write(f"Desktop shortcut created for all users.")
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
