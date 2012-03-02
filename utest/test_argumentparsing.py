import unittest
import robotide


class ArgumentParsingTestCase(unittest.TestCase):

    def test_no_args(self):
        self.assertEqual((False, None), robotide._parse_args([]))

    def test_path_to_data(self):
        self.assertEqual((False, 'data'), robotide._parse_args(['data']))

    def test_noupdatecheck(self):
        self.assertEqual((True, None), robotide._parse_args(['--noupdatecheck']))

    def test_noupdatecheck_and_path(self):
        self.assertEqual((True, 'path'), robotide._parse_args(['--noupdatecheck', 'path']))

if __name__ == '__main__':
    unittest.main()
