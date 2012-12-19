import unittest
from robotide.preferences.imports import Setting

class TestImportSetting(unittest.TestCase):

    def setUp(self):
        settings = {'name':['foo']}
        self.import_setting = Setting(settings, 'name', 'help')
        self.assertEqual(['foo'], self.import_setting.current_value)

    def test_that_empty_data_is_cleaned(self):
        self._test_data_set('', [])

    def _test_data_set(self, value, expected):
        self.import_setting.set(value)
        self.assertEqual(expected, self.import_setting.current_value)

    def test_that_only_non_empty_data_is_set(self):
        self._test_data_set(',,bar, ,', ['bar'])

    def test_values_are_stripped(self):
        self._test_data_set('z  ,   b ,  a b', ['z', 'b', 'a b'])

if __name__ == '__main__':
    unittest.main()
