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

import time
import unittest

from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import TestCaseFileController

from resources import COMPLEX_SUITE_PATH
from nose.tools import assert_equal, assert_true


class TestCaseAndUserKeywordCopyingTest(unittest.TestCase):
    controller = TestCaseFileController(
        TestCaseFile(source=COMPLEX_SUITE_PATH).populate())

    def test_test_case_copy(self):
        test = self.controller.tests[0]
        copy = test.copy('New Name')
        assert_equal(copy.name, 'New Name')
        for orig, copied in zip(test.settings, copy.settings):
            assert_equal(orig.value, copied.value)
            assert_true(copied is not orig)
        assert_equal(test.steps, copy.steps)
        assert_true(test.steps is not copy.steps)

    def test_keyword_copy(self):
        test = self.controller.keywords[0]
        copy = test.copy('New Name')
        assert_equal(copy.name, 'New Name')
        for orig, copied in zip(test.settings, copy.settings):
            assert_equal(orig.value, copied.value)
            assert_true(copied is not orig)
        assert_equal(test.steps, copy.steps)
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
