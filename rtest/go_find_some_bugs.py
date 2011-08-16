#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
import random
import time
import sys

from model import RIDE
from test_runner import Runner

seed = long(time.time() * 256)
if len(sys.argv) == 3:
    seed = long(sys.argv[2])
print 'seed = ', str(seed)
print 'path = ', sys.argv[1]
random.seed(seed)

try:
    ride = RIDE(random, sys.argv[1])

    ride_runner = Runner(ride, random)

    ride._open_test_dir()
    ride._create_suite()
    ride.create_test()
    #for j in range(584):
    #    ride_runner.skip_step()
    #ride_runner.step()
    #for k in range(17):
    #    ride_runner.skip_step()
    #ride_runner.step()
    #ride_runner.skip_step()
    for i in range(10000):
        ride_runner.step()
except :
    print 'i = ', i
    print 'seed was', str(seed)
    print 'path was', sys.argv[1]
    raise
