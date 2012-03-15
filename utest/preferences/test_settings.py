import unittest
from robotide.preferences.settings import SettingsMigrator


class SettingsMigrationTestCase(SettingsMigrator, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)

    def setUp(self):
        self._old_settings = {}
        self._default_settings = lambda:0
        self._from_0_to_1_called = False
        self._merge_called = False

    def test_migration_from_0_to_1(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 0
        self.migrate()
        self.assertTrue(self._from_0_to_1_called)
        self.assertTrue(self._merge_called)

    def test_no_migration_from_0_to_1_when_old_version_is_1(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 1
        self.migrate()
        self.assertFalse(self._from_0_to_1_called)
        self.assertTrue(self._merge_called)

    def migrate_from_0_to_1(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_0_to_1_called = True

    def merge(self):
        self._merge_called = True

if __name__ == '__main__':
    unittest.main()
