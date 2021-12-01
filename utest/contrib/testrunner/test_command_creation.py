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

from robotide.contrib.testrunner.Command import Command


class CommandStub(Command):
    def _get_listener_path(self):
        return 'C:\\My Work\\Python\\TestRunnerAgent.py'


class CommandCreationTests(unittest.TestCase):

    def test_build_command_default(self):
        command = CommandStub()
        result = command.build()
        self.assertEqual(result, '')

    def test_build_command_full(self):
        command = CommandStub() \
            .with_prefix('prefix') \
            .with_args_file('C:\\User name\\Temp\\Ride\\arg_file.robot')\
            .with_listener(5522) \
            .with_tests_suite_file('C:\\My Work\\TestSuite.robot')

        result = command.build()
        self.assertEqual(result,
                         'prefix -A "C:\\User name\\Temp\\Ride\\arg_file.robot" --listener "C:\\My Work\\Python\\TestRunnerAgent.py:5522:False" "C:\\My Work\\TestSuite.robot"')

    def test_build_command_call_some_method_twice(self):
        command = CommandStub() \
            .with_prefix('prefix_1') \
            .with_prefix('prefix_2') \
            .with_args_file('C:\\User name\\Temp\\Ride\\arg_file1.robot') \
            .with_args_file('C:\\User name\\Temp\\Ride\\arg_file2.robot')

        result = command.build()
        self.assertEqual(result, 'prefix_2 -A "C:\\User name\\Temp\\Ride\\arg_file2.robot"')


if __name__ == '__main__':
    unittest.main()
