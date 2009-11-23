#!/usr/bin/env python

"""Helper script to run all Robot Framework's unit tests.

usage: run_utest.py [options]

options: 
    -q, --quiet     Minimal output
    -v, --verbose   Verbose output
    -d, --doc       Show test's doc string instead of name and class
                    (implies verbosity)
    -h, --help      Show help
"""

import unittest
import os
import sys
import re
import getopt

base = os.path.abspath(os.path.dirname(__file__))
for path in [ "../src", 'resources/robotdata/libs']:
    path = os.path.join(base, path.replace('/', os.sep))
    if path not in sys.path:
        sys.path.insert(0, path)

testfile = re.compile("^test_.*\.py$", re.IGNORECASE)


def get_tests(patterns, directory=None):
    if directory is None:
        directory = base
    sys.path.append(directory)
    tests = []
    modules = []
    for name in os.listdir(directory):
        if name.startswith("."): continue
        fullname = os.path.join(directory, name)
        if os.path.isdir(fullname):
            tests.extend(get_tests(patterns, fullname))
        elif testfile.match(name) and _match_pattern(name, patterns):
            modules.append(_load_module(directory, name))
    tests.extend([ unittest.defaultTestLoader.loadTestsFromModule(module)
                   for module in modules ])
    return tests

def _load_module(dir, file_name):
    modname = os.path.basename(file_name)
    sys.path.insert(0, dir)
    module = __import__(modname)
    if dir != os.path.dirname(module.__file__):
        del(sys.modules[modname])
        module = __import__(modname)
    sys.path.pop(0)
    return module

def _match_pattern(name, patterns):
    if not patterns:
        return True
    for pattern in patterns:
        if pattern in name:
            return True
    return False


def parse_args(argv):
    docs = 0
    verbosity = 1
    args = []
    try:
        options, args = getopt.getopt(argv, 'hH?vqd', 
                                      ['help','verbose','quiet','doc'])
    except getopt.error, err:
        usage_exit(err)
    for opt, value in options:
        if opt in ('-h','-H','-?','--help'):
            usage_exit()
        if opt in ('-q','--quit'):
            verbosity = 0
        if opt in ('-v', '--verbose'):
            verbosity = 2
        if opt in ('-d', '--doc'):
            docs = 1
            verbosity = 2
    return docs, verbosity, args


def usage_exit(msg=None):
    print __doc__
    if msg is None:
        rc = 251
    else:
        print '\nError:', msg
        rc = 252
    sys.exit(rc)


if __name__ == '__main__':
    docs, vrbst, patterns = parse_args(sys.argv[1:])
    tests = get_tests(patterns)
    suite = unittest.TestSuite(tests)
    runner = unittest.TextTestRunner(descriptions=docs, verbosity=vrbst)
    result = runner.run(suite)
    rc = len(result.failures) + len(result.errors)
    if rc > 250: rc = 250
    sys.exit(rc)
