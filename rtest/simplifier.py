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

def simplify(trace, runner):
    try:
        return _simplify(1, trace, runner)
    except ResetSimplify as reset:
        return simplify(reset.trace, runner)


def _simplify(min_i, trace, runner):
    max_i = len(trace)
    if max_i == min_i:
        return trace
    step = (max_i-1)/min_i
    for start in range(0, max_i-1, step):
        new_trace = trace[:start]+trace[start+step:]
        if test_trace(new_trace, runner):
            return _simplify(min_i, new_trace, runner)
    return _simplify(min_i+1, trace, runner)


class ResetSimplify(Exception):

    def __init__(self, trace):
        Exception.__init__(self)
        self.trace = trace


def test_trace(trace, runner):
    print('>'*80)
    print('! >>> %d' % len(trace))
    runner.initialize()
    try:
        run_trace(runner, trace)
        return False
    except ValueError:  # was Exception:
        if runner.count <= trace[-1]:
            raise ResetSimplify([i for i in trace if i < runner.count])
        return True


def run_trace(runner, trace):
    i = 0
    while trace:
        if i == trace[0]:
            runner.step()
            trace = trace[1:]
        else:
            runner.skip_step()
        i += 1

if __name__ == '__main__':
    import random

    class Runner(object):

        def __init__(self, data):
            self._original_data = data
            self._fails = data[-1]
            self._data = data[:-1]
            self.count = 0

        def initialize(self):
            self.__init__(self._original_data)

        def step(self):
            self.count += 1
            if (not self._data) and (not self._fails):
                return
            self._data.pop(0)

        def skip_step(self):
            self.count += 1
            d = self._data.pop(0)
            self._fails &= (not d)

    for z in range(10):
        try:
            my10k = xrange(10000)
        except NameError:  # py3
            my10k = range(10000)
        test_data = [False for _ in my10k]
        test_data[-1] = True
        for i in range(random.randint(0, 10)):
            test_data[random.randint(0, 9999)] = True
        runner = Runner(test_data)
        trace = range(10000)
        print('!!')
        optimal_trace = simplify(trace, runner)
        print(optimal_trace)
        print('--')
        for n in optimal_trace:
            assert test_data[n]
        assert len([i for i in test_data if i]) == len(optimal_trace)
