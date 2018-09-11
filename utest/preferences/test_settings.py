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
        self._from_2_to_3_called = False
        self._from_3_to_4_called = False
        self._from_4_to_5_called = False
        self._from_5_to_6_called = False
        self._from_6_to_7_called = False
        self._from_7_to_8_called = False
        # self._from_8_to_9_called = False
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

    def test_migration_from_2_to_3(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 2
        self.migrate()
        self.assertFalse(self._from_1_to_2_called)
        self.assertTrue(self._from_2_to_3_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_3_to_4(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 3
        self.migrate()
        self.assertFalse(self._from_2_to_3_called)
        self.assertTrue(self._from_3_to_4_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_4_to_5(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 4
        self.migrate()
        self.assertFalse(self._from_3_to_4_called)
        self.assertTrue(self._from_4_to_5_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_5_to_6(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 5
        self.migrate()
        self.assertFalse(self._from_4_to_5_called)
        self.assertTrue(self._from_5_to_6_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_6_to_7(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 6
        self.migrate()
        self.assertFalse(self._from_5_to_6_called)
        self.assertTrue(self._from_6_to_7_called)
        self.assertTrue(self._merge_called)

    def test_migration_from_7_to_8(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 7
        self.migrate()
        self.assertFalse(self._from_6_to_7_called)
        self.assertTrue(self._from_7_to_8_called)
        self.assertTrue(self._merge_called)

    """
    def test_migration_from_8_to_9(self):
        self._old_settings[SettingsMigrator.SETTINGS_VERSION] = 8
        self.migrate()
        self.assertFalse(self._from_7_to_8_called)
        self.assertTrue(self._from_8_to_9_called)
        self.assertTrue(self._merge_called)
    """

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

    @overrides(SettingsMigrator)
    def migrate_from_2_to_3(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_2_to_3_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 3

    @overrides(SettingsMigrator)
    def migrate_from_3_to_4(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_3_to_4_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 4

    @overrides(SettingsMigrator)
    def migrate_from_4_to_5(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_4_to_5_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 5

    @overrides(SettingsMigrator)
    def migrate_from_5_to_6(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_5_to_6_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 6

    @overrides(SettingsMigrator)
    def migrate_from_6_to_7(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_6_to_7_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 7

    @overrides(SettingsMigrator)
    def migrate_from_7_to_8(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_7_to_8_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 8

    """
    @overrides(SettingsMigrator)
    def migrate_from_8_to_9(self, settings):
        self.assertEqual(self._old_settings, settings)
        self._from_8_to_9_called = True
        settings[SettingsMigrator.SETTINGS_VERSION] = 9
    """

    def merge(self):
        self._merge_called = True

if __name__ == '__main__':
    unittest.main()
