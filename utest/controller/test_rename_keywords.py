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

import os
import sys
import unittest
from robotide.controller.ctrlcommands import RenameKeywordOccurrences, NullObserver
from .base_command_test import TestCaseCommandTest
from utest.resources import datafilereader

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

SUITESETUPKW = 'Suite Setup Keyword'
GIVENAKW = 'Given a Keyword'
GIVENANEWKW = 'Given a new Keyword'
AKW = 'a Keyword'
WHENAKW = 'When a Keyword'


class TestRenameKeywords(TestCaseCommandTest):

    def test_test_is_gerkin_kw(self):
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("Step 1", "My New Keyword", observer)
        # ._get_gherkin("keyword value")
        is_gherkin, kw_value = myobject._get_gherkin(GIVENAKW)
        assert is_gherkin
        assert kw_value == AKW
        is_gherkin, kw_value = myobject._get_gherkin("Then a Keyword")
        assert is_gherkin
        assert kw_value == AKW
        is_gherkin, kw_value = myobject._get_gherkin("And a Keyword")
        assert is_gherkin
        assert kw_value == AKW
        is_gherkin, kw_value = myobject._get_gherkin(WHENAKW)
        assert is_gherkin
        assert kw_value == AKW
        is_gherkin, kw_value = myobject._get_gherkin("But a Keyword")
        assert is_gherkin
        assert kw_value == AKW
        is_gherkin, kw_value = myobject._get_gherkin("But Given a Keyword")
        assert is_gherkin
        assert kw_value == GIVENAKW
        is_gherkin, kw_value = myobject._get_gherkin("If a Keyword")
        assert not is_gherkin
        assert kw_value == "If a Keyword"

    def test_check_gerkin_kw(self):
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("Step 1", "My New Keyword", observer)
        # ._check_gherkin("new keyword value", "original keyword value")
        original_kw, new_kw = myobject._check_gherkin(GIVENAKW, AKW)
        assert new_kw == GIVENAKW
        assert original_kw == AKW
        original_kw, new_kw = myobject._check_gherkin(AKW, GIVENAKW)
        assert new_kw == AKW
        assert original_kw == GIVENAKW
        original_kw, new_kw = myobject._check_gherkin(WHENAKW, GIVENAKW)
        assert new_kw == WHENAKW
        assert original_kw == GIVENAKW
        original_kw, new_kw = myobject._check_gherkin("My new Keyword", "Old Keyword")
        assert new_kw == "My new Keyword"
        assert original_kw == "Old Keyword"
        original_kw, new_kw = myobject._check_gherkin("But Given a new Keyword", GIVENANEWKW)
        assert new_kw == "But Given a new Keyword"
        assert original_kw == GIVENANEWKW
        original_kw, new_kw = myobject._check_gherkin(GIVENANEWKW, "Given an old Keyword")
        assert new_kw == "a new Keyword"
        assert original_kw == "an old Keyword"


class TestRenameSetupKeywords(unittest.TestCase):

    def setUp(self):
        self.ctrl = datafilereader.construct_project(datafilereader.COMPLEX_TEST)
        self.suites = self.ctrl._suites()

    def test_rename_suite_setup_kw(self):
        kw_list = self.suites[0].get_keyword_names()
        settings = self.suites[0].setting_table
        suite_setup = settings.suite_setup.as_list()
        # self.ctrl.language = ['en']
        print(f"DEBUG: TestRenameSetupKeywords test_rename_suite_setup_kw"
              f" file_language={self.ctrl.file_language}\n"
              f" source= {self.suites[0].source}\n")
        assert kw_list == ['First KW', 'Second KW', 'Test Setup Keyword', 'Test Teardown Keyword',
                           'Keyword Teardown Keyword', SUITESETUPKW, 'Test Teardown in Setting']
        assert suite_setup == ['Suite Setup', 'Run Keywords', SUITESETUPKW, 'AND', 'First KW']
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("First KW", "One Keyword", observer)
        myobject.execute(self.suites[0])
        kw_list = self.suites[0].get_keyword_names()
        settings = self.suites[0].setting_table
        suite_setup = settings.suite_setup.as_list()
        # print(f"DEBUG: kw.list are: {kw_list} \n suite_setup={suite_setup}")
        assert kw_list == ['One Keyword', 'Second KW', 'Test Setup Keyword', 'Test Teardown Keyword',
                           'Keyword Teardown Keyword', SUITESETUPKW, 'Test Teardown in Setting']
        assert suite_setup == ['Suite Setup', 'Run Keywords', SUITESETUPKW, 'AND', 'One Keyword']


if __name__ == "__main__":
    unittest.main()
