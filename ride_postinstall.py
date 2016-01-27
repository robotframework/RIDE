#!/usr/bin/env python
# encoding=utf-8

import sys
from os.path import exists, join

__doc__ = """
Usage: ride_postinstall.py <-install|-remove>
""".strip()
# TODO: Add -remove, to remove desktop shortcut


def verify_install():
    try:
        from wx import version
    except ImportError as err:
        print("No wxPython installation detected!")
        print("")
        print("Please ensure that you have wxPython installed before running \
RIDE.")
        print("You can obtain wxPython 2.8.12.1 from \
http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/")
        sys.exit(1)
    else:
        print("Installation successful.")


def _askyesno(title, message):
    import wx
    _ = wx.App()
    parent = wx.Frame(None, size=(0, 0))
    parent.CenterOnScreen()
    dlg = wx.MessageDialog(parent, message, title, wx.YES_NO |
                           wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result


def _askdirectory(title, initialdir):
    import wx
    _ = wx.App()
    parent = wx.Frame(None, size=(0, 0))
    dlg = wx.DirDialog(parent, title, initialdir, style=wx.DD_DIR_MUST_EXIST)
    if dlg.ShowModal() == wx.ID_OK:
        result = dlg.GetPath()
    else:
        result = None
    dlg.Destroy()
    return result


def _create_desktop_shortcut_linux():
    import os
    import subprocess
    import pwd
    DEFAULT_LANGUAGE = os.environ.get('LANG', '').split(':')
    # TODO: Add more languages
    desktop = {"de": "Desktop", "en": "Desktop", "es": "Escritorio",
               "fi": r"Työpötä", "fr": "Bureau", "it": "Scrivania",
               "pt": r"Área de Trabalho"}
    try:
        ndesktop = desktop[DEFAULT_LANGUAGE[0][:2]]
        user = subprocess.check_output(['logname']).strip()
        link = os.path.join("/home", user, ndesktop, "RIDE.desktop")
    except KeyError as kerr:
        directory = _askdirectory(title="Locate Desktop Directory",
                                  initialdir=os.path.join(os.path.expanduser(
                                                          '~')))
        if not directory:
            sys.exit("Desktop shortcut creation aborted!")
        else:
            link = join(directory, "RIDE.desktop")
    if exists(link) or _askyesno("Setup", "Create desktop shortcut?"):
        roboticon = "/usr/lib/python{0}/site-packages/robotide/widgets/robot.p\
ng".format(sys.version[:3])
        with open(link, "w+") as shortcut:
            shortcut.write("#!/usr/bin/env xdg-open\n[Desktop Entry]\nExec=\
ride.py\nComment=A Robot Framework IDE\nGenericName=RIDE\n")
            shortcut.write("Icon={0}\n".format(roboticon))
            shortcut.write("Name=RIDE\nStartupNotify=true\nTerminal=false\nTyp\
e=Application\nX-KDE-SubstituteUID=false\n")
            uid = pwd.getpwnam(user).pw_uid
            os.chown(link, uid, -1)  # groupid == -1 means keep unchanged


def _create_desktop_shortcut_mac():
    import os
    import subprocess
    import pwd
    user = subprocess.check_output(['logname']).strip()
    link = os.path.join("/Users", user, "Desktop", "RIDE")
    if exists(link) or _askyesno("Setup", "Create desktop shortcut?"):
        roboticon = "/Library/Python/{0}/site-packages/robotide/widgets/robot.p\
ng".format(sys.version[:3])  # TODO: Find a way to change shortcut icon
        with open(link, "w+") as shortcut:
            shortcut.write("#!/bin/sh\n/usr/local/bin/ride.py $* &\n")
        uid = pwd.getpwnam(user).pw_uid
        os.chown(link, uid, -1)  # groupid == -1 means keep unchanged
        os.chmod(link, 0744)


def _create_desktop_shortcut_windows():
    # Dependency of http://sourceforge.net/projects/pywin32/
    import os
    import sys
    from win32com.shell import shell, shellcon
    desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
    link = os.path.join(desktop, 'RIDE.lnk')
    icon = os.path.join(sys.prefix, 'Lib', 'site-packages', 'robotide',
                        'widgets', 'robot.ico')
    if not exists(link):
        from Tkinter import Tk
        from tkMessageBox import askyesno
        Tk().withdraw()
        if not askyesno('Setup', 'Create desktop shortcut?'):
            sys.exit("Users can create a Desktop shortcut to RIDE with:\
\nride_postinstall.py -install\n")
        import pythoncom
        shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None,
                                              pythoncom.CLSCTX_INPROC_SERVER,
                                              shell.IID_IShellLink)
        command_args = " -c \"from robotide import main; main()\""
        shortcut.SetPath("pythonw.exe")  # sys.executable
        shortcut.SetArguments(command_args)
        shortcut.SetDescription("Robot Framework testdata editor")
        shortcut.SetIconLocation(icon, 0)
        persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
        persist_file.Save(link, 0)
        if __name__ != '__main__':
            file_created(link)  # Only in Windows installer. How to detect?


def create_desktop_shortcut(platform):
    if platform.startswith("linux"):
        _create_desktop_shortcut_linux()
    elif platform.startswith("darwin"):
        _create_desktop_shortcut_mac()
    elif platform.startswith("win"):
        _create_desktop_shortcut_windows()
    else:
        sys.exit("Unknown platform {0}: Failed to create desktop shortcut.".
                 format(platform))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '-install':
        platform = sys.platform.lower()
        if not platform.startswith("win"):
            verify_install()
        create_desktop_shortcut(platform)
    else:
        print(__doc__)
        sys.exit(0)


if __name__ == '__main__':
    main()
