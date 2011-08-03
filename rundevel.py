#!/usr/bin/env python

import os
import sys

ROOT = os.path.dirname(__file__)
src = os.path.join(ROOT, 'src')
sys.path.insert(0, src)
bundled_robot = os.path.join(ROOT, 'bundled', 'robotframework', 'src')
sys.path.insert(0, bundled_robot)

from robotide import main

try:
    main(sys.argv[1:])
except KeyboardInterrupt:
    pass
