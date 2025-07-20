#  Copyright 2023-     Robot Framework Foundation
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

from robotide.robotapi import LOG_LEVELS
from robotide.contrib.testrunner.ArgsParser import ArgsParser

DEFAULT_LOGS = '/home/tester/logs'


class ArgsParserTests(unittest.TestCase):

    def test_get_message_log_level_default(self):
        args = ['-C', 'off',
                '-W', 7,
                '-P', '/Python Dir:/opt/testlibs',
                '-d', 'C:\\Work\\Test 1',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_message_log_level(args)
        # print(f"DEBUG: ArgsParserTests {result=}")
        self.assertEqual(LOG_LEVELS['INFO'], result)  # '-L', 'DEBUG',

    def test_get_message_log_level_debug_short(self):
        args = ['-L', 'DEBUG',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['DEBUG'], result)

    def test_get_message_log_level_debug_full(self):
        args = ['-d', 'C:\\Work\\Test 1',
                '--suite', 'suite_name_1',
                '--loglevel', 'DEBUG',
                '--test', 'test_1']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['DEBUG'], result)

    def test_get_message_log_level_invalid(self):
        args = ['--suite', 'suite_name_1',
                '--loglevel', 'INVALID',
                '--test', 'test_1']
        self.assertRaises(TypeError, ArgsParser.get_message_log_level, args)

    def test_get_message_log_level_info_from_multiple(self):
        args = ['-L', 'INFO',
                '--test', 'test_1',
                '--loglevel', 'WARN']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['INFO'], result)

    def test_get_message_log_level_none(self):
        args = ['--test', 'test_1',
                '--loglevel', 'NONE']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['NONE'], result)

    def test_get_message_log_level_skip(self):
        args = ['--test', 'test_1',
                '-L', 'SKIP']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['SKIP'], result)

    def test_get_message_log_level_fail(self):
        args = ['--test', 'test_1',
                '-L', 'FAIL']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['FAIL'], result)

    def test_get_message_log_level_error(self):
        args = ['--test', 'test_1',
                '-L', 'ERROR']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['ERROR'], result)

    def test_get_message_log_level_warn(self):
        args = ['--test', 'test_1',
                '-L', 'WARN']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['WARN'], result)

    def test_get_message_log_level_trace(self):
        args = ['--test', 'test_1',
                '-L', 'TRACE']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['TRACE'], result)

    def test_get_message_log_level_trace_from_all(self):
        args = ['--test', 'test_1',
                '--loglevel', 'NONE:SKIP:FAIL:ERROR:WARN:INFO:DEBUG:TRACE']
        result = ArgsParser.get_message_log_level(args)
        self.assertEqual(LOG_LEVELS['TRACE'], result)

    def test_get_output_directory_default(self):
        args = ['-L', 'INFO:DEBUG',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_output_directory(args, DEFAULT_LOGS)
        self.assertEqual(DEFAULT_LOGS, result)

    def test_get_output_directory_short(self):
        args = ['-d', '/tmp/logs',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_output_directory(args, DEFAULT_LOGS)
        self.assertEqual('/tmp/logs', result)

    def test_get_output_directory_long(self):
        args = ['--outputdir', '/temp/report',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_output_directory(args, DEFAULT_LOGS)
        self.assertEqual('/temp/report', result)

    def test_get_named_suite_short(self):
        args = ['-N', 'My Named Suite',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_named_suite(args)
        self.assertEqual('My Named Suite', result)

    def test_get_named_suite_long(self):
        args = ['--name', 'My Named Suite',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        result = ArgsParser.get_named_suite(args)
        self.assertEqual('My Named Suite', result)


if __name__ == '__main__':
    unittest.main()
