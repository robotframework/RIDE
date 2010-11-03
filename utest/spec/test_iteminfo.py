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


class TestKeywordInfo(unittest.TestCase):

    def test_libkw_arguments_parsing(self):
        libname = 'TestLib'
        lib = TestLibrary(libname)
        kw_info = LibraryKeywordInfo(lib.handlers['testlib_keyword_with_args'])
        exp_start = 'Source: TestLib &lt;test library&gt;<br><br>Arguments: [ arg1 | arg2=default value | *args ]<br><br>'
        assert_true(kw_info.details.startswith(exp_start), kw_info.details)

    def test_uk_arguments_parsing(self):
        uk = UserKeyword(_FakeTestCaseFile(), 'My User keyword')
        uk.args.value = ['${arg1}', '${arg2}=def', '@{varargs}']
        kw_info = TestCaseUserKeywordInfo(uk)
        exp_start = 'Source: testcase.txt &lt;test case file&gt;<br><br>Arguments: [ arg1 | arg2=def | *varargs ]<br><br>'
        assert_true(kw_info.details.startswith(exp_start), kw_info.details)


class TestVariableInfo(unittest.TestCase):

    def test_variable_item_info(self):
        name = '${foo}'
        source = 'source'
        value = True
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_equals(info.details, 'Source: %s<br><br>Value:<br>%s' % (source, value))

    def test_variable_item_info_when_value_none(self):
        name = '${foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_equals(info.details, 'Source: %s<br><br>Value:<br>%s' % (source, value))

    def test_list_variable_item_info(self):
        name = '@{foo}'
        source = 'source'
        value = [1,2,3]
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_equals(info.details, 'Source: %s<br><br>Value:<br>[ %s ]' % (source, ' | '.join(str(i) for i in value)))
    
    def test_list_variable_item_info_when_value_none(self):
        name = '@{foo}'
        source = 'source'
        value = None
        info = VariableInfo(name, value, source)
        assert_equals(info.name, name)
        assert_equals(info.details, 'Source: %s<br><br>Value:<br>[  ]' % source)

if __name__ == "__main__":
    unittest.main()