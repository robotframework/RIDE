#!/usr/bin/env python
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
    mytests = range(number_of_tests)
    return '\n'.join(TEST_CASE_TEMPLATE.replace('%TEST_ID%', str(test_id))\
                      .replace('%KW_ID%', str(randint(0,number_of_keywords-1)))\
                      for test_id in mytests)


def generate_keywords(number_of_keywords):
    mykeywords = range(number_of_keywords)
    return '\n'.join(KEYWORD_TEMPLATE.replace('%KW_ID%', str(i)) for i in mykeywords)


def generate_suite(number_of_tests, number_of_keywords):
    return SUITE.replace('%TESTCASES%', generate_tests(number_of_tests, number_of_keywords))\
                .replace('%KEYWORDS%', generate_keywords(number_of_keywords))


def generate_resource(number_of_keywords):
    return RESOURCE.replace('%KEYWORDS%', generate_keywords(number_of_keywords))


def generate(directory, suites, tests, keywords):
    os.mkdir(directory)
    mysuites = range(suites)
    for suite_index in mysuites:
        f = open(os.path.join('.', directory, 'suite%s.txt' % suite_index), 'w')
        f.write(generate_suite(tests, keywords))
        f.close()
    r = open(os.path.join('.', directory, 'resource.txt'), 'w')
    r.write(generate_resource(keywords))
    r.close()


def usage():
    print('datagenerator.py -d [directory] -s [NUMBER OF SUITES] -t [NUMBER OF TESTS IN SUITE] -k [NUMBER OF KEYWORDS]')


def main(args):
    try:
        opts, args = getopt(args, 'd:s:t:k:', [])
    except GetoptError as e:
        print(e)
        usage()
        sys.exit(2)
    if len(opts) != 4:
        if opts:
            print(opts)
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

