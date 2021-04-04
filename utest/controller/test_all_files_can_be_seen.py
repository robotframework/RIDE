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


class TestAllFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = datafilereader.construct_project(
            datafilereader.ALL_FILES_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def test_all_files_can_be_seen(self):
        all_files = self.project.data
        self.assertEqual(all_files.name, 'All Files')
        self.assertEqual(len(all_files.suites), 3)
        self._verify_names(all_files, 'Used Resource', 'Unused Resource',
                           'Resource Dir', 'Suite Dir', 'Suite2 Dir')
        resource_dir = self._get_child(all_files, 'Resource Dir')
        self._verify_names(resource_dir, *())
        suite_dir = self._get_child(all_files, 'Suite Dir')
        self._verify_names(suite_dir, 'Suite')

    def _get_child(self, controller, name):
        return [c for c in controller.children if c.name == name][0]

    def _verify_names(self, controller, *names):
        self.assertEqual(set(c.name for c in controller.children), set(names))

    def test_unused_resource_knows_it_is_unused(self):
        unused = datafilereader.get_ctrl_by_name('Unused Resource',
                                                 self.project.datafiles)
        self.assertFalse(unused.is_used())

    def test_used_resource_knows_it_is_used(self):
        used = datafilereader.get_ctrl_by_name('Used Resource',
                                               self.project.datafiles)
        self.assertTrue(used.is_used())


if __name__ == '__main__':
    unittest.main()
