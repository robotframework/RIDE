import sys
from os.path import join


def verify_install():
    try:
        import wxversion
    except ImportError:
        print "No wxPython installation detected!"
        print ""
        print "Please ensure that you have wxPython installed before running RIDE."
        print "You can obtain wxPython from http://wxpython.org/"
    else:
        print "Installation successful."


def create_desktop_shortcut():
    link = join(get_special_folder_path("CSIDL_DESKTOPDIRECTORY"), 'RIDE.lnk')
    icon = join(sys.prefix, 'Lib', 'site-packages', 'robotide', 'widgets', 'robot.ico')
    create_shortcut('pythonw', "Robot Framework testdata editor", link,
                    '-c "from robotide import main; main()"', '', icon)


if sys.argv[1] == '-install':
    verify_install()
    create_desktop_shortcut()
