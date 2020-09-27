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
from utest.resources import datafilereader


class TestParents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = datafilereader.construct_project(
            datafilereader.SIMPLE_TEST_SUITE_PATH)
        cls.directory = cls.project.data
        cls.test = datafilereader.get_ctrl_by_name(
            'TestSuite1', cls.project.datafiles)
        cls.resource = datafilereader.get_ctrl_by_name(
            datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME,
            cls.project.datafiles)
        cls.external_resource = datafilereader.get_ctrl_by_name(
            'Resu', cls.project.datafiles)

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def test_test_suite_parent_is_directory(self):
        self.assertEqual(self.test.parent, self.directory)
        self.assertTrue(self.test in self.directory.children)

    def test_local_resource_parent_is_directory(self):
        self.assertEqual(self.resource.parent, self.directory)
        self.assertTrue(self.resource in self.directory.children)

    def test_external_resource_parent_is_undefined(self):
        self.assertEqual(self.external_resource.parent, None)
        self.assertTrue(self.external_resource not in self.directory.children)

if __name__ == '__main__':
    unittest.main()
