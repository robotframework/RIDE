#!/usr/bin/env python

import os
import sys
import shutil
from tempfile import TemporaryFile
from subprocess import call, STDOUT

ORIGDIR = 'golden'
OUTDIR = 'tmp'
TARGETDIR = os.path.join(OUTDIR, 'tests')
RIDETARGETDIR = os.path.join(OUTDIR, 'ride-tests')


def setup():
    if os.path.exists(OUTDIR):
        shutil.rmtree(OUTDIR)
    for name in [ OUTDIR, TARGETDIR, RIDETARGETDIR]:
        os.mkdir(name)
    for name in os.listdir(ORIGDIR):
        path = os.path.join(ORIGDIR, name)
        if os.path.isfile(path):
            shutil.copy(path, TARGETDIR)

def run_original_tests():
    print 'Running original tests...'
    _run_tests(['-l', 'orig.html', '-o', 'orig.xml', TARGETDIR])

def use_ride():
    for name in os.listdir(ORIGDIR):
        path = os.path.join(ORIGDIR, name)
        if os.path.isfile(path):
            newname = os.path.join(RIDETARGETDIR, name)
            if not path.endswith('.py'):
                print "Processing '%s' with IDE" % path
                ride_cmd = [ 'python', '../src/robotide/__init__.py', path, newname ]
                call(ride_cmd)
            else:
                print "Copying '%s' -> '%s'" % (path, newname)
                shutil.copy(path, newname)


def _run_tests(opt_args):
    command = [ 'pybot', '-r', 'none', '-d', OUTDIR, '-N', 'Golden_Tests',
                '-P', os.path.join('..', 'utest', 'resources', 'robotdata') ]
    ret = call(command + opt_args, shell=os.name=='nt')

def run_modified_tests():
    print 'Running processed tests...'
    _run_tests(['-l', 'ride.html', '-o', 'ride.xml', RIDETARGETDIR])

def diff():
    print 'Diffing outputs...'
    call(['python', 'robotdiff.py', '-r', os.path.join(OUTDIR, 'diff.html'), 
         os.path.join(OUTDIR, 'orig.xml'), os.path.join(OUTDIR, 'ride.xml')])


if __name__ == '__main__':
    setup()
    run_original_tests()
    use_ride()
    run_modified_tests()
    diff()

