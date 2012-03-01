import unittest
from robotide.utils.versioncomparator import cmp_versions


class VersionComparatorTestCase(unittest.TestCase):

    def test_versions(self):
        self.assertEqual(1, cmp_versions('1.0', '0.0'))
        self.assertEqual(-1, cmp_versions('0.0', '1.0'))
        self.assertEqual(0, cmp_versions('0.0', '0.0'))

    def test_none(self):
        self.assertEqual(1, cmp_versions('21', None))
        self.assertEqual(-1, cmp_versions(None, '3.21'))
        self.assertEqual(0, cmp_versions(None, None))

    def test_trunk_is_smaller_than_released_version(self):
        self.assertEqual(1, cmp_versions('0.02', 'trunk'))
        self.assertEqual(1, cmp_versions('1.2.3', 'trunk'))
        self.assertEqual(1, cmp_versions('13.001', 'trunk'))

    def test_zero_and_empty_are_equal(self):
        self.assertEqual(0, cmp_versions('0', '0.0.0.0'))
        self.assertEqual(0, cmp_versions('2.0.1', '2.0.1.0'))

    def test_release_candidate_is_smaller_than_released(self):
        self.assertEqual(1, cmp_versions('0.45', '0.45rc1'))
        self.assertEqual(-1, cmp_versions('1.4rc2', '1.4'))

    def test_alpha_less_than_beta_less_than_rc(self):
        self.assertEqual(1, cmp_versions('0b', '0a'))
        self.assertEqual(-1, cmp_versions('1.0b', '1.0rc1'))

if __name__ == '__main__':
    unittest.main()
