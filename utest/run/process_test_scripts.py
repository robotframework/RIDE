#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import sys
import time


def output(sleep=0.1):
    print('start')
    for i in range(2):
        print('running iteration %d' % i * 500)
        time.sleep(float(sleep))
    print('done')


def count_args(*args):
    print(len(args))

def stderr():
    sys.stderr.write('This is stderr\n')

globals()[sys.argv[1]](*sys.argv[2:])

