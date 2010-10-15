#  Copyright 2010 Nokia Siemens Networks Oyj
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

import os.path
import unittest

from robotide.context.settings import _merge_settings

from resources.setting_utils import TestSettingsHelper


class TestMergeSettings(TestSettingsHelper):

    def setUp(self):
        base = os.path.join(os.path.dirname(__file__), '..', 'resources')
        self.settings_cfg = os.path.join(base, 'settings2.cfg')
        self.user_cfg = os.path.join(base, 'user2.cfg')

    def tearDown(self):
        pass

    def test_merge_settings(self):
        _merge_settings(self.settings_cfg, self.user_cfg)
        _merge_settings(self.settings_cfg, self.user_cfg)
        content = self._read_settings_file_content(self.user_cfg)
        line_count = len(content.splitlines())
        self.assertEquals(line_count, 33, "line count should be 33 was %s" % 
                          line_count)


if __name__ == "__main__":
    unittest.main()
