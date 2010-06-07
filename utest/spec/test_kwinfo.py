import sys
import os
import unittest
from robot.running import TestLibrary
from robot.parsing.model import UserKeyword
from robot.utils.asserts import assert_true

from robotide.spec.kwinfo import LibraryKeywordInfo, TestCaseUserKeywordInfo


testlibpath = os.path.join(os.path.dirname(__file__), '..', 'resources', 'robotdata', 'libs')
sys.path.append(testlibpath)

class _FakeTestCaseFile(object):
    source = '/path/to/testcase.txt'


class TestKeywordInfo(unittest.TestCase):

    def test_libkw_arguments_parsing(self):
        libname = 'TestLib'
        lib = TestLibrary(libname)
        kw_info = LibraryKeywordInfo(lib.handlers['testlib_keyword_with_args'],
                                     libname)
        exp_start = 'Source: TestLib &lt;test library&gt;<br><br>Arguments: [ arg1 | arg2=default value | *args ]<br><br>'
        assert_true(kw_info.details.startswith(exp_start), kw_info.details)

    def test_uk_arguments_parsing(self):
        uk = UserKeyword(_FakeTestCaseFile(), 'My User keyword')
        uk.args.value = ['${arg1}', '${arg2}=def', '@{varargs}']
        kw_info = TestCaseUserKeywordInfo(uk)
        exp_start = 'Source: /path/to/testcase.txt &lt;test case file&gt;<br><br>Arguments: [ arg1 | arg2=def | *varargs ]<br><br>'
        assert_true(kw_info.details.startswith(exp_start), kw_info.details)


if __name__ == "__main__":
    unittest.main()