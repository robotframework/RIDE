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

from robotide.contrib.testrunner.SettingsParser import SettingsParser


class SettingsParserTests(unittest.TestCase):

    def test_get_console_log_name_default(self):
        settings = ['message_log_name', 'Messages.txt']
        result = SettingsParser.get_console_log_name(settings)
        self.assertEqual('', result)

    def test_get_console_log_name(self):
        settings = ['console_log_name', 'Console Log.txt']
        result = SettingsParser.get_console_log_name(settings)
        self.assertEqual('Console Log.txt', result)


if __name__ == '__main__':
    unittest.main()
