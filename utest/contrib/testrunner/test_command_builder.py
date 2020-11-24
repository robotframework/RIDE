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

from robotide.contrib.testrunner.CommandBuilder import CommandBuilder


class CommandBuilderStub(CommandBuilder):
    def _get_listener_path(self):
        return 'C:\\My Work\\Python\\TestRunnerAgent.py'


class CommandBuilderTests(unittest.TestCase):

    def test_build_command_default(self):
        builder = CommandBuilderStub()
        result = builder.build()
        self.assertEqual(result, '')

    def test_build_command_full(self):
        builder = CommandBuilderStub()
        builder.set_prefix('prefix')
        builder.add_arg_file('C:\\User name\\Temp\\Ride\\arg_file.txt')
        builder.set_listener(5522)
        builder.set_suite_source('C:\\My Work\\TestSuite.robot')

        result = builder.build()
        self.assertEqual(result,
                         'prefix -A "C:\\User name\\Temp\\Ride\\arg_file.txt" --listener "C:\\My Work\\Python\\TestRunnerAgent.py:5522:False" "C:\\My Work\\TestSuite.robot"')

    def test_build_command_call_method_twice(self):
        builder = CommandBuilderStub()
        builder.set_prefix('prefix_1')
        builder.set_prefix('prefix_2')
        builder.add_arg_file('C:\\User name\\Temp\\Ride\\arg_file1.txt')
        builder.add_arg_file('C:\\User name\\Temp\\Ride\\arg_file2.txt')

        result = builder.build()
        self.assertEqual(result, 'prefix_2 -A "C:\\User name\\Temp\\Ride\\arg_file2.txt"')


if __name__ == '__main__':
    unittest.main()
