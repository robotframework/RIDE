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
from robotide.context import SETTINGS_DIRECTORY

TEST_PROJECT = os.path.join(DATAPATH, 'test_project')
PROJECT_EMPTY_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'empty_project_settings')
PROJECT_EMPTY_PROJECT_SETTINGS_TEST= os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, 'minimal.robot')
PROJECT_NO_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'no_project_settings')
PROJECT_NO_PROJECT_SETTINGS_TEST= os.path.join(PROJECT_NO_PROJECT_SETTINGS, 'minimal.robot')
SUBPROJECT_WITH_PROJECT_SETTINGS_ONE = os.path.join(TEST_PROJECT, 'with_project_settings_one')
SUBPROJECT_WITH_PROJECT_SETTINGS_ONE_TEST= os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS_ONE, 'minimal.robot')
SUBPROJECT_PROJECT_SETTINGS_TWO = os.path.join(TEST_PROJECT, 'with_project_settings_two')
SUBPROJECT_PROJECT_SETTINGS_TWO_TEST= os.path.join(SUBPROJECT_PROJECT_SETTINGS_TWO, 'minimal.robot')
SUBPROJECT_EMPTY_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'with_project_settings_two',
                                                'subproject_empty_project_settings')
SUBPROJECT_EMPTY_PROJECT_SETTINGS_TEST= os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, 'minimal.robot')
SUBPROJECT_NO_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'with_project_settings_two',
                                                'subproject_no_project_settings')
SUBPROJECT_NO_PROJECT_SETTINGS_TEST= os.path.join(SUBPROJECT_NO_PROJECT_SETTINGS, 'minimal.robot')
SUBPROJECT_WITH_PROJECT_SETTINGS = os.path.join(TEST_PROJECT, 'with_project_settings_two',
                                                'subproject_with_project_settings')
SUBPROJECT_WITH_PROJECT_SETTINGS_TEST= os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS, 'minimal.robot')

"""
.
├── empty_project_settings
│   ├── minimal.robot
│   └── .robot
│       └── .gitkeep
├── no_project_settings
│   └── minimal.robot
├── with_project_settings_one
│   ├── minimal.robot
│   └── .robot
│       └── ride_settings.cfg
└── with_project_settings_two
    ├── minimal.robot
    ├── .robot
    │   └── ride_settings.cfg
    ├── subproject_empty_project_settings
    │   ├── minimal.robot
    │   └── .robot
    │       └── .gitkeep
    ├── subproject_no_project_settings
    │   └── minimal.robot
    └── subproject_with_project_settings
        ├── minimal.robot
        └── .robot
            └── ride_settings.cfg
"""


class TestProjectSettings(unittest.TestCase):

    def setUp(self):
        if os.path.isfile(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')):
            os.remove(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))
        if os.path.isfile(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')):
            os.remove(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))

    def _setUp(self):
        from robotide.application import RIDE
        self.main_app = RIDE()
        self.settings = self.main_app.settings
        self.frame = self.main_app.frame
        # self.main_app.SetExitOnFrameDelete(True)

    def _tearDown(self):
        # builtins.__import__ = real_import
        # self.frame.Close(True)
        self.main_app.ExitMainLoop()
        self.main_app.Destroy()
        self.main_app = None
        if os.path.isfile(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')):
            os.remove(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))
        if os.path.isfile(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')):
            os.remove(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))

    def test_project_empty_init_one(self):
        """ Empty projects create a settings file """
        import robotide.application
        import wx

        from robotide.application import RIDE

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            class SideEffect(RIDE):

                def __init__(self):
                    self.frame = wx.Frame(None)
                    self.settings_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')

                def OnInit(self):  # Overrides wx method
                    pass

                def MainLoop(self):  # Overrides wx method
                    pass

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application, 'RIDE', SideEffect)
                self._setUp()
                assert os.path.isdir(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot'))
                assert not os.path.exists(os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))
                settings_file = self.main_app.initialize_project_settings(PROJECT_EMPTY_PROJECT_SETTINGS_TEST)
                assert settings_file == os.path.join(PROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')

    def test_project_empty_init_two(self):
        """ Empty projects create a settings file """
        import robotide.application
        import wx

        from robotide.application import RIDE

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            class SideEffect(RIDE):

                def __init__(self):
                    self.frame = wx.Frame(None)
                    self.settings_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')

                def OnInit(self):  # Overrides wx method
                    pass

                def MainLoop(self):  # Overrides wx method
                    pass

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application, 'RIDE', SideEffect)
                self._setUp()
                assert os.path.isdir(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot'))
                assert not os.path.exists(os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))
                settings_file = self.main_app.initialize_project_settings(SUBPROJECT_EMPTY_PROJECT_SETTINGS_TEST)
                assert settings_file == os.path.join(SUBPROJECT_EMPTY_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')


    def test_project_no_init(self):
        """ No projects don't create a settings file, and use default settings or project above """
        import robotide.application
        import wx

        from robotide.application import RIDE

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            class SideEffect(RIDE):

                def __init__(self):
                    self.frame = wx.Frame(None)
                    self.settings_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')

                def OnInit(self):  # Overrides wx method
                    pass

                def MainLoop(self):  # Overrides wx method
                    pass

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application, 'RIDE', SideEffect)
                self._setUp()
                assert not os.path.exists(os.path.join(PROJECT_NO_PROJECT_SETTINGS, '.robot'))
                settings_file = self.main_app.initialize_project_settings(PROJECT_NO_PROJECT_SETTINGS_TEST)
                # print(f"DEBUG: PROJECT_NO_PROJECT_SETTINGS settings=={settings_file}")
                assert settings_file == os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
                # assert settings_file == os.path.join(PROJECT_NO_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')
                assert not os.path.exists(os.path.join(SUBPROJECT_NO_PROJECT_SETTINGS, '.robot'))
                settings_file = self.main_app.initialize_project_settings(SUBPROJECT_NO_PROJECT_SETTINGS_TEST)
                # print(f"DEBUG: SUBPROJECT_NO_PROJECT_SETTINGS settings=={settings_file}")
                assert settings_file == os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')

    def test_project_init(self):
        """ Projects use its settings file """
        import robotide.application
        import wx

        from robotide.application import RIDE

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)

            class SideEffect(RIDE):

                def __init__(self):
                    self.frame = wx.Frame(None)
                    self.settings_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')

                def OnInit(self):  # Overrides wx method
                    pass

                def MainLoop(self):  # Overrides wx method
                    pass

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application, 'RIDE', SideEffect)
                self._setUp()
                assert os.path.exists(os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS_ONE, '.robot', 'ride_settings.cfg'))
                settings_file = self.main_app.initialize_project_settings(SUBPROJECT_WITH_PROJECT_SETTINGS_ONE_TEST)
                assert settings_file == os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS_ONE, '.robot', 'ride_settings.cfg')

                assert os.path.exists(os.path.join(SUBPROJECT_PROJECT_SETTINGS_TWO, '.robot', 'ride_settings.cfg'))
                settings_file = self.main_app.initialize_project_settings(SUBPROJECT_PROJECT_SETTINGS_TWO_TEST)
                assert settings_file == os.path.join(SUBPROJECT_PROJECT_SETTINGS_TWO, '.robot', 'ride_settings.cfg')

                assert os.path.exists(os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg'))
                settings_file = self.main_app.initialize_project_settings(SUBPROJECT_WITH_PROJECT_SETTINGS_TEST)
                assert settings_file == os.path.join(SUBPROJECT_WITH_PROJECT_SETTINGS, '.robot', 'ride_settings.cfg')


if __name__ == '__main__':
    unittest.main()
