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

import tempfile
import unittest
import os
from utest.resources import datafilereader
from robotide.controller.filecontrollers import TestDataDirectoryController, ExcludedDirectoryController, \
    DirtyRobotDataException


class TestExcludesLogic(unittest.TestCase):

    def setUp(self):
        self.project = datafilereader.construct_project(datafilereader.SIMPLE_TEST_SUITE_PATH, tempfile.gettempdir())

    def tearDown(self):
        p = self.project._settings.excludes._exclude_file_path
        if os.path.exists(p):
            os.remove(p)

    def _get_resource_dir(self):
        return datafilereader.get_ctrl_by_name(datafilereader.SIMPLE_TEST_SUITE_INNER_RESOURCE_DIR, self.project.datafiles)

    def test_excluding_and_including(self):
        resource_dir = self._get_resource_dir()
        self.assertEqual(resource_dir.__class__, TestDataDirectoryController)
        resource_dir.exclude()
        resource_dir = self._get_resource_dir()
        self.assertEqual(resource_dir.__class__, ExcludedDirectoryController)
        resource_dir.remove_from_excludes()
        resource_dir = self._get_resource_dir()
        self.assertEqual(resource_dir.__class__, TestDataDirectoryController)

    def test_excluding_throws_exception_if_dirty_data(self):
        resource_dir = self._get_resource_dir()
        resu = resource_dir.children[0]
        resu.mark_dirty()
        self.assertRaises(DirtyRobotDataException, resource_dir.exclude)

if __name__ == '__main__':
    unittest.main()
