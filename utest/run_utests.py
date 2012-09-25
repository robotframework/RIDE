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
    if run:
        sys.argv.append('--m=^test')
        tests_passed = run(defaultTest=os.path.dirname(__file__))
        retcode = 0 if tests_passed else 1
        sys.exit(retcode)
