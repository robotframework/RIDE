#!/usr/bin/env python

from getopt import getopt, GetoptError
from random import randint
import os

SUITE=\
"""*** Settings ***
Resource    resource.txt

*** Test Cases ***
%TESTCASES%

*** Keywords ***
Test Keyword
    Log jee
"""

RESOURCE=\
"""*** Variables ***
@{Resource Var}  MOI

*** Keywords ***
%KEYWORDS%
"""

KEYWORD_TEMPLATE=\
"""My Keyword %KW_ID%
    No Operation"""

TEST_CASE_TEMPLATE=\
"""My Test %TEST_ID%
    My Keyword %KW_ID%
    Log  moi
    Test Keyword
    Log  moi
    Test Keyword
    Log  moi
    Test Keyword
    Log  moi
    Test Keyword
    Log  moi
    Test Keyword
    My Keyword %KW_ID%
    Test Keyword
    Log  moi
    Test Keyword
    Log  moi
    Test Keyword
    Log  moi"""


def generate_tests(number_of_tests, number_of_keywords):
    return '\n'.join(TEST_CASE_TEMPLATE.replace('%TEST_ID%', str(test_id))\
                      .replace('%KW_ID%', str(randint(0,number_of_keywords-1)))\
                      for test_id in xrange(number_of_tests))

def generate_keywords(number_of_keywords):
    return '\n'.join(KEYWORD_TEMPLATE.replace('%KW_ID%', str(i)) for i in xrange(number_of_keywords))

def generate_suite(number_of_tests, number_of_keywords):
    return SUITE.replace('%TESTCASES%', generate_tests(number_of_tests, number_of_keywords))\
                .replace('%KEYWORDS%', generate_keywords(number_of_keywords))

def generate_resource(number_of_keywords):
    return RESOURCE.replace('%KEYWORDS%', generate_keywords(number_of_keywords))

def generate(directory, suites, tests, keywords):
    os.mkdir(directory)
    for suite_index in xrange(suites):
        f = open(os.path.join('.', directory, 'suite%s.txt' % suite_index), 'w')
        f.write(generate_suite(tests, keywords))
        f.close()
    r = open(os.path.join('.', directory, 'resource.txt'), 'w')
    r.write(generate_resource(keywords))
    r.close()

def usage():
    print 'datagenerator.py -d [directory] -s [NUMBER OF SUITES] -t [NUMBER OF TESTS IN SUITE] -k [NUMBER OF KEYWORDS]'

def main(args):
    try:
        opts, args = getopt(args, 'd:s:t:k:', [])
    except GetoptError, e:
        print e
        usage()
        sys.exit(2)
    if len(opts) != 4:
        if opts:
            print opts
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-d':
            directory = arg
        if opt == '-s':
            suites = int(arg)
        if opt == '-t':
            tests = int(arg)
        if opt == '-k':
            keywords = int(arg)
    generate(directory, suites, tests, keywords)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])

