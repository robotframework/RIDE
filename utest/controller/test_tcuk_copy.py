import time
import unittest

from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import TestCaseFileController

from resources import COMPLEX_SUITE_PATH
from nose.tools import assert_equals, assert_true


class TestCaseAndUserKeywordCopyingTest(unittest.TestCase):
    controller = TestCaseFileController(
        TestCaseFile(source=COMPLEX_SUITE_PATH).populate())

    def test_test_case_copy(self):
        test = self.controller.tests[0]
        copy = test.copy('New Name')
        assert_equals(copy.name, 'New Name')
        for orig, copied in zip(test.settings, copy.settings):
            assert_equals(orig.value, copied.value)
            assert_true(copied is not orig)
        assert_equals(test.steps, copy.steps)
        assert_true(test.steps is not copy.steps)

    def test_keyword_copy(self):
        test = self.controller.keywords[0]
        copy = test.copy('New Name')
        assert_equals(copy.name, 'New Name')
        for orig, copied in zip(test.settings, copy.settings):
            assert_equals(orig.value, copied.value)
            assert_true(copied is not orig)
        assert_equals(test.steps, copy.steps)
        assert_true(test.steps is not copy.steps)

    def test_test_copy_performance(self):
        self._run_copy_test(self.controller.tests[0])

    def test_keyword_copy_performance(self):
        self._run_copy_test(self.controller.keywords[0])

    def _run_copy_test(self, item):
        self._test_copy(item, 10)
        self._test_copy(item, 200)

    def _test_copy(self, item, count):
        start_time = time.time()
        for i in range(0, count):
            item.copy(str(i))
        self.assertTrue(time.time() < (start_time + 2),
                        "Copy operation takes too long time")


if __name__ == '__main__':
    unittest.main()
