#!/usr/bin/env python
import os
import sys
import time
from nose import run


def test_modules():
    topdir = os.path.dirname(__file__)
    for dirpath, _, filenames in os.walk(topdir):
        for fname in filenames:
            if _is_test_module(fname):
                yield os.path.join(dirpath, fname)

def _is_test_module(fname):
    return fname.startswith('test') and fname.endswith('.py')


def collect_execution_times(test_modules):
    sys.argv.append('--match=^test')
    sys.argv.append('-q')
    for tmodule in test_modules:
        yield(tmodule, _test_module_execution_time(tmodule))

def _test_module_execution_time(tmodule):
    starttime = time.time()
    run(defaultTest=tmodule)
    return time.time() - starttime


def write_results(exectimes, write):
    total = 0.0
    writes = []
    for record in reversed(sorted(exectimes, key=lambda record: record[1])):
        total += record[1]
        write('%s%.02f s (%.02f s)\n' % (record[0].ljust(70), record[1], total))
    write('\nTotal test execution time: %.02f seconds\n' % total)

def main():
    exectimes = collect_execution_times(test_modules())
    with open('testtimes.txt', 'w') as output:
        def write(txt):
            output.write(txt)
            sys.stdout.write(txt)
        write_results(exectimes, write)

if __name__ == '__main__':
    main()
