import sys
if sys.argv[1] == '-install':
    try:
        import wxversion
    except ImportError:
        print "No wxPython installation detected!"
        print ""
        print "Please ensure that you have wxPython installed before running RIDE."
        print "You can obtain wxPython from http://wxpython.org/"
