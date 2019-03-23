#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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
from robotide.utils.versioncomparator import cmp_versions


class VersionComparatorTestCase(unittest.TestCase):

    def test_versions(self):
        self.assertEqual(1, cmp_versions("1.0", "0.0"))
        self.assertEqual(-1, cmp_versions("0.0", "1.0"))
        self.assertEqual(0, cmp_versions("0.0", "0.0"))

    def test_none(self):
        self.assertEqual(1, cmp_versions("21", None))
        self.assertEqual(-1, cmp_versions(None, "3.21"))
        self.assertEqual(0, cmp_versions(None, None))

    def test_trunk_is_smaller_than_released_version(self):
        self.assertEqual(1, cmp_versions("0.02", "trunk"))
        self.assertEqual(1, cmp_versions("1.2.3", "trunk"))
        self.assertEqual(1, cmp_versions("13.001", "trunk"))

    def test_zero_and_empty_are_equal(self):
        self.assertEqual(0, cmp_versions("0", "0.0.0.0"))
        self.assertEqual(0, cmp_versions("2.0.1", "2.0.1.0"))

    def test_release_candidate_is_smaller_than_released(self):
        self.assertEqual(1, cmp_versions("0.45", "0.45rc1"))
        self.assertEqual(-1, cmp_versions("1.4rc2", "1.4"))

    def test_alpha_less_than_beta_less_than_rc(self):
        self.assertEqual(1, cmp_versions("0b", "0a"))
        self.assertEqual(-1, cmp_versions("1.0b", "1.0rc1"))

if __name__ == "__main__":
    unittest.main()
