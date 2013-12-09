
def simplify(trace, runner):
    try:
        return _simplify(1, trace, runner)
    except ResetSimplify, reset:
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
    print '>'*80
    print '! >>> %d' % len(trace)
    runner.initialize()
    try:
        run_trace(runner, trace)
        return False
    except Exception:
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
        test_data = [False for _ in xrange(10000)]
        test_data[-1] = True
        for i in range(random.randint(0, 10)):
            test_data[random.randint(0, 9999)] = True
        runner = Runner(test_data)
        trace = range(10000)
        print '!!'
        optimal_trace = simplify(trace, runner)
        print optimal_trace
        print '--'
        for n in optimal_trace:
            assert test_data[n]
        assert len([i for i in test_data if i]) == len(optimal_trace)
