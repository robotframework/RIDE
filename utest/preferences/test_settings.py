import unittest
from robotide.preferences.settings import SettingsMigrator
from robotide.utils import overrides


class SettingsMigrationTestCase(SettingsMigrator, unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)

    def setUp(self):
        self._old_settings = {}
        self._default_settings = lambda: 0
        self._from_0_to_1_called = False
        self._from_1_to_2_called = False
        self._merge_called = False

    def test_migration_from_0_to_2(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 0
        self.migrate()
        self.assertTrue(self._from_0_to_1_called)
        self.assertTrue(self._from_1_to_2_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_1_to_2(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 1
        self.migrate()
        self.assertFalse(self._from_0_to_1_called)
        self.assertTrue(self._from_1_to_2_called)
        self.assertTrue(self._merge_called)

    @overrides(SettingsMigrator)
    def migrate_from_0_to_1(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_0_to_1_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 1

    @overrides(SettingsMigrator)
    def migrate_from_1_to_2(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_1_to_2_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 2

    def merge(self):
        self._merge_called = True

if __name__ == '__main__':
    unittest.main()
