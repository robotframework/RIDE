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
        run(defaultTest=os.path.dirname(__file__))
