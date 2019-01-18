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

from math import ceil
import os
import time
import sys
import traceback
from rtest import simplifier


ROOT = os.path.dirname(__file__)
src = os.path.join(ROOT, '..', 'src')

sys.path.insert(0, src)


from .test_runner import Runner


def do_test(seed, path):
    i = None
    try:
        ride_runner = init_ride_runner(seed, path)
        for i in range(10000):
            ride_runner.step()
        return 'PASS', seed, i, path
    except Exception:
        print('-'*80)
        traceback.print_exc()
        print('i = ', i)
        print('seed was', str(seed))
        print('path was', path)
        return 'FAIL', seed, i or 0, path

def init_ride_runner(seed, path):
    return Runner(seed, path, ROOT).initialize()

def split(start, end):
    return int(ceil(float(end - start) / 2)) + start

def skip_steps(runner, number_of_steps):
    for i in range(number_of_steps):
        runner.skip_step()

def debug(seed, path, last_index, trace, start, end):
    print('*'*80)
    if last_index == start:
        return trace + [last_index]
    if end <= start:
        return debug(seed, path, last_index, trace + [end], end+1, last_index)
    runner = init_ride_runner(seed, path)
    if trace != []:
        run_trace(runner, trace)
    midpoint = split(start, end)
    runner.skip_steps(midpoint)
    try:
        for j in range(midpoint, last_index):
            runner.step()
        return debug(seed, path, last_index, trace, start, midpoint-1)
    except Exception as err:
        if runner.count == last_index:
            return debug(seed, path, last_index, trace, midpoint, end)
        else:
            print('New exception during debugging!')
            return debug(seed, path, runner.count, trace, midpoint,
                         runner.count)


def run_trace(runner, trace):
    i = 0
    while i < trace[-1]:
        if i in trace:
            runner.step()
        else:
            runner.skip_step()
        i += 1


def generate_seed():
    seed = long(time.time() * 256)
    if len(sys.argv) == 3:
        seed = long(sys.argv[2])
    return seed


def _debugging(seed, path, i):
    print('='*80)
    trace = debug(seed, path, i, [], 0, i)
    print('#'*80)
    print(trace)
    print('%'*80)
    print('seed = ', seed)
    run_trace(init_ride_runner(seed, path), trace)


def main(path):
    result, seed, i, path = do_test(generate_seed(), path)
    # _debugging(seed, path, i)
    #  ???>>>!!! simplifier.simplify(range(i+1), init_ride_runner(seed, path))
    return result != 'FAIL'

if __name__ == '__main__':
    if not main(sys.argv[1]):
        print('error occurred!')
        sys.exit(1) #indicate failure
