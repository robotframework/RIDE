import unittest
from robot.parsing.model import TestCaseFile
from robot.utils.asserts import assert_equals

from robotide.controller.dataloader import DataSanitizer


class TestDataFileSanitizer(unittest.TestCase):

    def test_default_headers_are_removed(self):
        data = TestCaseFile()
        data.testcase_table.set_header(['Test Cases', 'Action', 'Argument'])
        assert_equals(DataSanitizer().sanitize(data).testcase_table.header,
                      ['Test Cases'])


