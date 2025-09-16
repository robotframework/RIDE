#  Copyright 2025-     Robot Framework Foundation
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
import os.path
import sys
import unittest
import pytest
from pytest import MonkeyPatch
import wx
from utest.resources.datafilereader import DATAPATH

TEST_PROJECT = os.path.join(DATAPATH, 'test_project')
SUBPROJECT_WITH_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'with_project_settings_two',
                                                'subproject_with_project_settings')
SUBPROJECT_WITH_PROJECT_SETTINGS_TEST= os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS, 'minimal.robot')


class TestProjectSettings(unittest.TestCase):

    def setUp(self):
        from robotide.application import RIDE
        self.main_app = RIDE()
        self.settings = self.main_app.settings
        self.frame = self.main_app.frame
        self.main_app.SetExitOnFrameDelete(True)

    def tearDown(self):
        # builtins.__import__ = real_import
        self.main_app.ExitMainLoop()
        self.main_app.Destroy()
        self.main_app = None

    def test_project_init(self):
        settings_file = self.main_app.initialize_project_settings(SUBPROJECT_WITH_PROJECT_SETTINGS)
        assert settings_file == os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')


if __name__ == '__main__':
    unittest.main()
