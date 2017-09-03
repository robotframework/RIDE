import sys
import unittest
from robotide.controller.ctrlcommands import *
from nose.tools import assert_true, assert_false, assert_equal

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
try:
    from base_command_test import TestCaseCommandTest
except ImportError:  # Python 3
    from .base_command_test import TestCaseCommandTest


class TestRenameKeywords(TestCaseCommandTest):

    def test_test_is_gerkin_kw(self):
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("Step 1", "My New Keyword", observer)
        # ._get_gherkin("keyword value")
        is_gherkin, kw_value = myobject._get_gherkin("Given a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("Then a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("And a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("When a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("But a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("But Given a Keyword")
        assert_true(is_gherkin)
        assert_equal(kw_value, "Given a Keyword")
        is_gherkin, kw_value = myobject._get_gherkin("If a Keyword")
        assert_false(is_gherkin)
        assert_equal(kw_value, "If a Keyword")

    def test_check_gerkin_kw(self):
        observer = NullObserver()
        myobject = RenameKeywordOccurrences("Step 1", "My New Keyword", observer)
        # ._check_gherkin("new keyword value", "original keyword value")
        original_kw, new_kw = myobject._check_gherkin("Given a Keyword", "a Keyword")
        assert_equal(new_kw, "Given a Keyword")
        assert_equal(original_kw, "a Keyword")
        original_kw, new_kw = myobject._check_gherkin("a Keyword", "Given a Keyword")
        assert_equal(new_kw, "a Keyword")
        assert_equal(original_kw, "Given a Keyword")
        original_kw, new_kw = myobject._check_gherkin("When a Keyword", "Given a Keyword")
        assert_equal(new_kw, "When a Keyword")
        assert_equal(original_kw, "Given a Keyword")
        original_kw, new_kw = myobject._check_gherkin("My new Keyword", "Old Keyword")
        assert_equal(new_kw, "My new Keyword")
        assert_equal(original_kw, "Old Keyword")
        original_kw, new_kw = myobject._check_gherkin("But Given a new Keyword", "Given a new Keyword")
        assert_equal(new_kw, "But Given a new Keyword")
        assert_equal(original_kw, "Given a new Keyword")
        original_kw, new_kw = myobject._check_gherkin("Given a new Keyword", "Given an old Keyword")
        assert_equal(new_kw, "a new Keyword")
        assert_equal(original_kw, "an old Keyword")

if __name__ == "__main__":
    unittest.main()
