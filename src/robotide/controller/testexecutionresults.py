#  Copyright 2008-2015 Nokia Solutions and Networks
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
from robotide.publish.messages import RideTestExecutionStarted, RideTestPassed, RideTestFailed, RideTestRunning

class TestExecutionResults(object):
    RUNNING = 'Running'
    PASSED = 'Passed'
    FAILED = 'Failed'

    def __init__(self):
        self.clear()

    def test_execution_started(self):
        self.clear()
        RideTestExecutionStarted(results=self).publish()

    def clear(self):
        self._results = {}

    def set_running(self, test):
        self._results[test] = self.RUNNING
        RideTestRunning(item=test).publish()

    def set_passed(self, test):
        self._results[test] = self.PASSED
        RideTestPassed(item=test).publish()

    def set_failed(self, test):
        self._results[test] = self.FAILED
        RideTestFailed(item=test).publish()

    def is_running(self, test):
        return test in self._results and self._results[test] == self.RUNNING

    def has_passed(self, test):
        return test in self._results and self._results[test] == self.PASSED

    def has_failed(self, test):
        return test in self._results and self._results[test] == self.FAILED

