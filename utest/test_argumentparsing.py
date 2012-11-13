import unittest
import robotide


class ArgumentParsingTestCase(unittest.TestCase):

    def test_no_args(self):
        self._assert_args([])

    def _assert_args(self, tested, expected_no_update_check=False, expected_debug_console=False, expected_path=None):
        self.assertEqual((expected_no_update_check, expected_debug_console, expected_path), robotide._parse_args(tested))

    def test_path_to_data(self):
        self._assert_args(['data'], expected_path='data')

    def test_noupdatecheck(self):
        self._assert_args(['--noupdatecheck'], expected_no_update_check=True)

    def test_noupdatecheck_and_path(self):
        self._assert_args(['--noupdatecheck', 'path'], expected_no_update_check=True, expected_path='path')

    def test_debugconsole(self):
        self._assert_args(['--debugconsole'], expected_debug_console=True)

    def test_debugconsole_and_path(self):
        self._assert_args(['--debugconsole', 'dir'], expected_debug_console=True, expected_path='dir')

if __name__ == '__main__':
    unittest.main()
