#!/usr/bin/env python

import os
import sys

src = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src)

from robotide import main

try:
    main(sys.argv[1:])
except KeyboardInterrupt:
    pass
