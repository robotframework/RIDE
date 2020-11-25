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

from robotide.contrib.testrunner.CommandArgs import CommandArgs


class CommandBuilderTests(unittest.TestCase):

    def test_build_command_args_default(self):
        args = CommandArgs()
        result = args.build()
        self.assertListEqual(result, [])

    def test_build_command_args_full(self):
        tests = [('suite_name_1', 'test_1'),
                 ('suite_name_1', 'test_2'),
                 ('suite_name_1', 'test_3')]
        args = CommandArgs() \
            .with_existing_args([]) \
            .with_python_path(['/Python Dir',
                               '/opt/testlibs']) \
            .with_output_directory('C:\\Work\\Test 1') \
            .with_log_level('DEBUG') \
            .without_console_color() \
            .with_console_width(7) \
            .with_runnable_tests(tests)

        result = args.build()
        self.assertListEqual(result,
                             ['-C', 'off',
                              '-W', 7,
                              '-P', '/Python Dir:/opt/testlibs',
                              '-d', 'C:\\Work\\Test 1',
                              '-L', 'DEBUG',
                              '--suite', 'suite_name_1',
                              '--test', 'test_1',
                              '--suite', 'suite_name_1',
                              '--test', 'test_2',
                              '--suite', 'suite_name_1',
                              '--test', 'test_3'])

    def test_build_command_args_should_not_override_existing_args(self):
        existing_args = ['--loglevel', 'INFO',
                         '-P', 'C:\\Python Dir\\python.exe',
                         '-d', 'C:\\Test',
                         '-W', 12]  # --consolewidth
        args = CommandArgs() \
            .with_existing_args(existing_args) \
            .with_python_path('C:\\My Python Dir\\my_python.exe') \
            .with_log_level('DEBUG') \
            .with_output_directory('C:\\My Work\\Test 1') \
            .with_console_width(5) \
            .without_console_color()

        result = args.build()
        self.assertListEqual(result,
                             ['--loglevel', 'INFO',
                              '-P', 'C:\\Python Dir\\python.exe',
                              '-d', 'C:\\Test',
                              '-W', 12,  # --consolewidth
                              '-C', 'off'])

    def test_build_command_args_call_some_method_twice(self):
        builder = CommandArgs()\
            .with_log_level('LEVEL_1') \
            .with_log_level('LEVEL_2')

        result = builder.build()
        self.assertListEqual(result, ['-L', 'LEVEL_2'])


if __name__ == '__main__':
    unittest.main()
