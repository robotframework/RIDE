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
import robotide.lib.robot.errors
from robotide.contrib.testrunner.runprofiles import PybotProfile


class TestPybotArgumentsValidation(unittest.TestCase):

    def setUp(self):
        self._profile = PybotProfile(lambda: 0)

    def test_invalid_argument(self):

        self.assertRaisesRegex(robotide.lib.robot.errors.DataError,
                               'option --invalidargument not recognized',
                               self._profile._get_invalid_message,
                               '--invalidargument')

    def test_valid_argument_short(self):
        self._working_arguments('-T')

    def _working_arguments(self, args):
        self.assertEqual(None, self._profile._get_invalid_message(args))

    def test_valid_argument_long(self):
        self._working_arguments('--timestampoutputs')

    def test_valid_argument_with_value(self):
        self._working_arguments('--log somelog.html')

    def test_runfailed_argument_works(self):
        self._working_arguments('--rerunfailed output.xml')


if __name__ == '__main__':
    unittest.main()
