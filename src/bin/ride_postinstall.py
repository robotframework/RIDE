#!/usr/bin/env python

#  Copyright 2008-2015 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import os
import sys

# Must be protected against reimporting
# As multiprocessing has an odd requirement
# and we use multiprocessing
# http://docs.python.org/library/multiprocessing.html#windows
if __name__ == '__main__':
    arg = " ".join(sys.argv[1:]) if len(sys.argv[1:]) > 0 else "-help"
    py = sys.executable
    os.system("{} -m robotide.postinstall {}\n".format(py,arg))
