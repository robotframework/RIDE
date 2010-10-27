import unittest
from robot.parsing.model import TestCaseFile
from robot.utils.asserts import assert_equals

from robotide.controller.filecontrollers import TestCaseFileController

VALID_NAME = 'Valid name'


class TestCaseNameValidationTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile()).tests

    def test_valid_name(self):
        self._validate_name(VALID_NAME, True)

    def test_empty_name(self):
        self._validate_name('', False)

    def test_name_with_only_whitespace(self):
        self._validate_name('      ', False)

    def test_duplicate_name(self):
        self.ctrl.new(VALID_NAME)
        self._validate_name(VALID_NAME, False)

    def _validate_name(self, name, expected_valid):
        assert_equals(self.ctrl.validate_name(name).valid, expected_valid)


class TestCaseCreationTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile()).tests

    def test_whitespace_is_stripped(self):
        test = self.ctrl.new('   ' + VALID_NAME + '\t   \n')
        assert_equals(test.name, VALID_NAME)
