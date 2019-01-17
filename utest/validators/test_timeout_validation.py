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
from robotide.validators import TimeoutValidator

class TimeoutValidationTest(unittest.TestCase):

    def setUp(self):
        self.validator = TimeoutValidator()
        self.validator._set_window_value = self._catch_value
        self._value = ""

    def _catch_value(self, value):
        self._value = value

    def test_timeout_validation_passes(self):
        result = self.validator._validate("2h 30min 45sec")
        self.assertEqual( result, None, "Empty string should have been returned from validate: %s" % result)

    def test_timeout_validation_negative_cases(self):
        self._run_validation("-1000","-1","0")

    def test_timeout_validation_illegal_format(self):
        self._run_validation("1 minuuttia", "2 tuntia ja muuta","dshfkjhsdkjfhjk")

    def _run_validation(self, *test_values):
        errors = []
        for val in test_values:
            result = self.validator._validate(val)
            if result == None:
                errors.append("\n%s should have failed, but didn't, got '%s'" % (val, result))
        self.assertEqual(len(errors), 0, ''.join(errors))

if __name__ == '__main__':
    unittest.main()
