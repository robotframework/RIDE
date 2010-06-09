#  Copyright 2008 Nokia Siemens Networks Oyj
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

from resources import COMPLEX_SUITE_PATH


class PerformanceTest(unittest.TestCase):
    """Test for performance issue 276"""

    def setUp(self):
        self.suite = TestCaseFile(COMPLEX_SUITE_PATH)
        self.start_time = time.time()

    def run_copy_test(self, collection):
        self._test_copy(collection, 10)
        self._test_copy(collection, 200)

    def _test_copy(self, collection, count):
        for i in range(0, count):
            collection.copy(collection[0], str(i))
        self.assertTrue(time.time() < (self.start_time + 2), 
                        "Copy operation takes too long time")


class TestTestCaseCopyPerformance(PerformanceTest):

    def test_copy_performance(self):
        self.run_copy_test(self.suite.tests)


class TestUserKeywordCopyPerformance(PerformanceTest):

    def test_copy_performance(self):
        self.run_copy_test(self.suite.keywords)


if __name__ == '__main__':
    unittest.main()
