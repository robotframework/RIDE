import os.path
import unittest

from resources.setting_utils import TestSettingsHelper
from robotide.preferences.settings import SettingsMigrator


class TestMergeSettings(TestSettingsHelper):

    def setUp(self):
        base = os.path.join(os.path.dirname(__file__), '..', 'resources')
        self.settings_cfg = os.path.join(base, 'settings2.cfg')
        self.user_cfg = os.path.join(base, 'user2.cfg')

    def tearDown(self):
        pass

    def test_merge_settings(self):
        SettingsMigrator(self.settings_cfg, self.user_cfg).merge()
        SettingsMigrator(self.settings_cfg, self.user_cfg).merge()
        content = self._read_settings_file_content(self.user_cfg)
        line_count = len(content.splitlines())
        self.assertEquals(line_count, 33, "line count should be 33 was %s" %
                          line_count)


if __name__ == "__main__":
    unittest.main()
