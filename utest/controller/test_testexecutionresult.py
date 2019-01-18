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

import unittest
from robotide.controller.testexecutionresults import TestExecutionResults

class TestExecutionResultTestCase(unittest.TestCase):

    def setUp(self):
        self._results = TestExecutionResults()
        self._test = object()
        self._test2 = object()

    def test_running_test(self):
        self._results.set_running(self._test)
        self._expect_running(self._test)
        self._results.set_passed(self._test)
        self._expect_passed(self._test)

    def _expect_passed(self, test):
        self.assertFalse(self._results.is_running(test))
        self.assertTrue(self._results.has_passed(test))
        self.assertFalse(self._results.has_failed(test))

    def _expect_running(self, test):
        self.assertTrue(self._results.is_running(test))
        self.assertFalse(self._results.has_passed(test))
        self.assertFalse(self._results.has_failed(test))

    def test_running_test_that_fails(self):
        self._results.set_running(self._test)
        self._expect_running(self._test)
        self._results.set_failed(self._test)
        self._expect_failed(self._test)

    def _expect_failed(self, test):
        self.assertFalse(self._results.is_running(test))
        self.assertFalse(self._results.has_passed(test))
        self.assertTrue(self._results.has_failed(test))

    def test_running_two_tests(self):
        self._results.set_running(self._test)
        self._expect_running(self._test)
        self._expect_no_result(self._test2)
        self._results.set_failed(self._test)
        self._expect_failed(self._test)
        self._results.set_running(self._test2)
        self._expect_running(self._test2)
        self._expect_failed(self._test)
        self._results.set_passed(self._test2)
        self._expect_passed(self._test2)
        self._expect_failed(self._test)

    def test_clearing_results(self):
        self._results.set_running(self._test)
        self._results.set_passed(self._test)
        self._results.set_running(self._test2)
        self._results.set_passed(self._test2)
        self._results.clear()
        self._expect_no_result(self._test)
        self._expect_no_result(self._test2)

    def _expect_no_result(self, test):
        self.assertFalse(self._results.is_running(test))
        self.assertFalse(self._results.has_passed(test))
        self.assertFalse(self._results.has_failed(test))


if __name__ == '__main__':
    unittest.main()
