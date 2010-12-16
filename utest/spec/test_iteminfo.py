import sys
import os
import unittest
from robot.running import TestLibrary
from robot.parsing.model import UserKeyword
from robot.utils.asserts import assert_true, assert_equals

from robotide.spec.iteminfo import LibraryKeywordInfo, TestCaseUserKeywordInfo, VariableInfo


testlibpath = os.path.join(os.path.dirname(__file__), '..', 'resources', 'robotdata', 'libs')
sys.path.append(testlibpath)


class _FakeTestCaseFile(object):
    source = '/path/to/testcase.txt'

def assert_in_details(kw_info, *expecteds):
    details = kw_info.details
    for e in expecteds:
        assert_true(e in details, details)


class TestKeywordInfo(unittest.TestCase):

    def test_libkw_arguments_parsing(self):
        libname = 'TestLib'
        lib = TestLibrary(libname)
        kw_info = LibraryKeywordInfo(lib.handlers['testlib_keyword_with_args'])
        assert_in_details(kw_info, 'Testlib',
                          '[ arg1 | arg2=default value | *args ]')

    def test_uk_arguments_parsing(self):
        uk = UserKeyword(_FakeTestCaseFile(), 'My User keyword')
        uk.args.value = ['${arg1}', '${arg2}=def', '@{varargs}']
        kw_info = TestCaseUserKeywordInfo(uk)
        exp_source = 'testcase.txt'
        exp_args = '[ arg1 | arg2=def | *varargs ]'
        assert_in_details(kw_info, exp_source, exp_args)


class TestVariableInfo(unittest.TestCase):

    def test_variable_item_info(self):
        name = '${foo}'
        source = 'source'
        value = True
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_in_details(info, source, 'True')

    def test_variable_item_info_when_value_none(self):
        name = '${foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_in_details(info, source, '')

    def test_list_variable_item_info(self):
        name = '@{foo}'
        source = 'source'
        value = [1,2,3]
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_in_details(info, source, '[ 1 | 2 | 3 ]')

    def test_list_variable_item_info_when_value_none(self):
        name = '@{foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_in_details(info, source, '')

if __name__ == "__main__":
    unittest.main()
