#!/usr/bin/env python

import os
import sys
from subprocess import call

src = os.path.join(os.path.dirname(__file__), 'src')
ride = os.path.join(src, 'bin', 'ride.py')
os.environ['PYTHONPATH'] = src
try:
    call(['python', ride] + sys.argv[1:], shell=os.name=='nt')
except KeyboardInterrupt:
    pass
