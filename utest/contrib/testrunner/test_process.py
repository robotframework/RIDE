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
import time
from robot.version import VERSION
from utest.resources import datafilereader

from robotide.contrib.testrunner.testrunner import Process

if VERSION >= '7.1.1':
    console_out = b"==============================================================================\n" \
                  b"Small Test                                                                    \n" \
                  b"==============================================================================\n" \
                  b"Small Test.Test                                                               \n" \
                  b"==============================================================================\n" \
                  b"Passing                                                               | PASS |\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Failing                                                               | FAIL |\n" \
                  b"this fails\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Small Test.Test                                                       | FAIL |\n" \
                  b"2 tests, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Small Test                                                            | FAIL |\n" \
                  b"2 tests, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Output:  NONE\n"
elif VERSION >= '4.0':
    console_out = b"==============================================================================\n" \
                  b"Small Test                                                                    \n" \
                  b"==============================================================================\n" \
                  b"Small Test.Test                                                               \n" \
                  b"==============================================================================\n" \
                  b"Passing                                                               | PASS |\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Failing                                                               | FAIL |\n" \
                  b"this fails\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Small Test.Test                                                       | FAIL |\n" \
                  b"2 tests, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Small Test                                                            | FAIL |\n" \
                  b"2 tests, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Output:  None\n"
else:
    console_out = b"==============================================================================\n" \
                  b"Small Test                                                                    \n" \
                  b"==============================================================================\n" \
                  b"Small Test.Test                                                               \n" \
                  b"==============================================================================\n" \
                  b"Passing                                                               | PASS |\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Failing                                                               | FAIL |\n" \
                  b"this fails\n" \
                  b"------------------------------------------------------------------------------\n" \
                  b"Small Test.Test                                                       | FAIL |\n" \
                  b"2 critical tests, 1 passed, 1 failed\n2 tests total, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Small Test                                                            | FAIL |\n" \
                  b"2 critical tests, 1 passed, 1 failed\n2 tests total, 1 passed, 1 failed\n" \
                  b"==============================================================================\n" \
                  b"Output:  None\n"


class ProcessUnicodeTestCase(unittest.TestCase):

    def test_unicode_command(self):
        try:
            Process(r'\xf6').run_command(r'echo \xf6')
        except UnicodeEncodeError:
            self.fail('Should not throw unicode error')
        except OSError:
            pass

    def test_running_robot_test(self):
        output, errors = self._run_small_test()
        print(output, errors)
        parsed_output = bytes(output.replace(b'\r', b''))
        parsed_errors = bytes(errors.replace(b'\r', b''))
        assert parsed_output == console_out
        self.assertTrue(parsed_output.startswith(console_out), msg=repr(output))
        # Because of deprecation messages in RF 3.1, from Equal to Regex
        self.assertRegex(parsed_errors, b".*\\[ WARN \\] this passes\n")

    @staticmethod
    def _run_small_test():
        p = Process(datafilereader.SMALL_TEST_PATH)
        p.run_command('robot --extension robot:txt --output NONE --log NONE --report NONE .')
        max_time = 7.0
        while p.is_alive() and max_time > 0:
            time.sleep(0.1)
            max_time -= 0.1
        if max_time <= 0:
            p.kill()
            raise AssertionError('process did not stop in 7 second time')
        return p.get_output(), p.get_errors()

    def test_stopping_robot_with_listener_should_generate_outputs(self):
        pass

    def test_stopping_robot_with_two_kill_signals_should_not_generate_outputs(self):
        pass


if __name__ == '__main__':
    unittest.main()
