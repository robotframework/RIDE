#!/usr/bin/env python
import os
import sys
try:
    from nose import run
except ImportError:
    print 'You need to have `nose` installed to run RIDE unit tests.'
    print 'Download nose from http://somethingaboutorange.com/mrl/projects/nose'
    run = None

if __name__ == '__main__':
    basedir = os.path.dirname(__file__)
    if run:
        sys.path.insert(0, os.path.join(basedir, '..', 'bundled', 'robotframework', 'src'))
        sys.argv.append('--m=^test_')
        tests_passed = run(defaultTest=basedir)
        retcode = 0 if tests_passed else 1
        sys.exit(retcode)
