import sys
from os.path import exists, join
from Tkinter import Tk
from tkMessageBox import askyesno


def verify_install():
    try:
        import wxversion
    except ImportError:
        print "No wxPython installation detected!"
        print ""
        print "Please ensure that you have wxPython installed before running RIDE."
        print "You can obtain wxPython 2.8.12.1 from http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/"
    else:
        print "Installation successful."


def create_desktop_shortcut():
    Tk().withdraw()
    link = join(get_special_folder_path("CSIDL_DESKTOPDIRECTORY"), 'RIDE.lnk')
    icon = join(sys.prefix, 'Lib', 'site-packages', 'robotide', 'widgets', 'robot.ico')
    if exists(link) or askyesno('Setup', 'Create desktop shortcut?'):
        create_shortcut('pythonw', "Robot Framework testdata editor", link,
                        '-c "from robotide import main; main()"', '', icon)
        file_created(link)


if sys.argv[1] == '-install':
    verify_install()
    create_desktop_shortcut()
