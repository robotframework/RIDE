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
import os
import unittest
from nose.tools import assert_true, assert_equal

from robotide.robotapi import TestLibrary, UserKeyword, KeywordTable
from robotide.namespace import variablefetcher
from robotide.spec import libraryfetcher

from robotide.spec.iteminfo import LibraryKeywordInfo, TestCaseUserKeywordInfo, VariableInfo, ResourceUserKeywordInfo


testlibpath = os.path.join(os.path.dirname(__file__), '..', 'resources', 'robotdata', 'libs')
sys.path.append(testlibpath)


class _FakeTestCaseFile(object):
    source = '/path/to/testcase.txt'

class _FakeResourceFile(object):
    source = '/path/to/my/resource.html'
    name = 'resource'
    rawname = 'resource'

def assert_in_details(kw_info, *expecteds):
    details = kw_info.details
    for e in expecteds:
        assert_true(e in details, details)


class TestKeywordInfo(unittest.TestCase):

    def test_libkw_arguments_parsing(self):
        libname = 'TestLib'
        lib = TestLibrary(libname)
        kw = lib.handlers['testlib_keyword_with_args']
        kw_info = LibraryKeywordInfo(kw.name, kw.doc, lib.doc_format, kw.library.name, libraryfetcher._parse_args(kw.arguments))
        assert_in_details(kw_info, 'TestLib',
                          '[ arg1 | arg2=default value | *args ]')

    def test_uk_arguments_parsing(self):
        uk = UserKeyword(_FakeTestCaseFile(), 'My User keyword')
        uk.args.value = ['${arg1}', '${arg2}=def', '@{varargs}']
        kw_info = TestCaseUserKeywordInfo(uk)
        exp_source = 'testcase.txt'
        exp_args = '[ arg1 | arg2=def | *varargs ]'
        assert_in_details(kw_info, exp_source, exp_args)

    def test_resource_uk_longname(self):
        uk = UserKeyword(KeywordTable(_FakeResourceFile()), 'UK')
        kw_info = ResourceUserKeywordInfo(uk)
        self.assertEqual(kw_info.longname, 'resource.UK')


class TestVariableInfo(unittest.TestCase):

    def test_variable_item_info(self):
        name = '${foo}'
        source = 'source'
        value = True
        info = VariableInfo(name, value, source)
        assert_equal(info.name, name)
        assert_in_details(info, source, 'True')

    def test_variable_item_info_when_value_none(self):
        name = '${foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equal(info.name, name)
        assert_in_details(info, source, '')

    def test_list_variable_item_info(self):
        name = '@{foo}'
        source = 'source'
        value = variablefetcher._format_value([1,2,3])
        info = VariableInfo(name, value, source)
        assert_equal(info.name, name)
        assert_in_details(info, source, '[ 1 | 2 | 3 ]')

    def test_list_variable_item_info_when_value_none(self):
        name = '@{foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equal(info.name, name)
        assert_in_details(info, source, '')

if __name__ == "__main__":
    unittest.main()
