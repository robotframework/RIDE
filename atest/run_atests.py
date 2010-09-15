#!/usr/bin/env python

"""A script for running RIDE's acceptance tests.

Usage:  run_atests.py [options] datasource(s)

Data sources are paths to directories or files under 'robot' folder.

Available options are the same that can be used with Robot Framework.
See its help (e.g. 'pybot --help') for more information.

Examples:
$ atest/run_atests.py atest/robot
"""

import os.path
import shutil
import signal
import subprocess
import sys


CURDIR = os.path.dirname(os.path.abspath(__file__))
RESULTDIR = os.path.join(CURDIR, 'results')

ARGUMENTS = ' '.join('''
--doc RIDESPacceptanceSPtests
--reporttitle RIDESPTestSPReport
--logtitle RIDESPTestSPLog
--pythonpath %(PYTHONPATH)s
--outputdir %(OUTPUTDIR)s
--output output.xml
--report report.html
--log log.html
--escape space:SP
--SplitOutputs 2
--SuiteStatLevel 3
'''.strip().splitlines())


def atests(interpreter, *params):
    if os.path.isdir(RESULTDIR):
        shutil.rmtree(RESULTDIR)
    args = ARGUMENTS % {
        'PYTHONPATH' : os.path.join(CURDIR, 'resources'),
        'OUTPUTDIR' : RESULTDIR,
        }
    print params
    command = 'pybot.bat %s %s' % (args, ' '.join(params))
    print 'Running command:\n%s\n' % command
    sys.stdout.flush()
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    return subprocess.call(command.split())


if __name__ == '__main__':
    if len(sys.argv) == 1 or '--help' in sys.argv:
        print __doc__
        rc = 251
    else:
        rc = atests(*sys.argv[0:])
    sys.exit(rc)
