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

import builtins
import os

import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True) # Avoid failing unit tests in system without X11
import wx
import unittest
from robotide.preferences import Preferences, PreferenceEditor
from robotide.preferences.general import GeneralPreferences
from time import sleep
from utest.resources import FakeSettings, UIUnitTestBase


_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


settings = FakeSettings()


class MyEvent(object):
    def __init__(self, iid):
        self.id = iid

    def GetId(self):
        return self.id

    def Skip(self):
        pass

class MyGeneralPreferences(GeneralPreferences):
        location = 'General'

        def create_colors_sizer(self):
            sizer = wx.BoxSizer()
            return sizer


class TestPreferenceEditor(UIUnitTestBase):

    def test_preferences_dialog(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        settings.set('font size',11)
        generalpanel = MyGeneralPreferences(settings, self.frame)
        preferences = Preferences(settings)
        preferences.add(generalpanel)
        dlg = PreferenceEditor(self.frame, title='Test Preferences Dialog', preferences=preferences)
        # wx.CallLater(5000, dlg.EndModal,ID_CANCEL)
        dlg.CenterOnParent()
        dlg.Show()
        sleep(2)
        generalpanel.Show()
        # panel_title = generalpanel.GetTitle()
        sleep(5)
        generalpanel.Close(True)
        dlg.on_close(MyEvent(0))
        assert dlg.GetTitle() == "Test Preferences Dialog"
        assert generalpanel.name == 'General'
        assert dlg._closing == True

    """
    TODO: Make missing tests
    """



if __name__ == '__main__':
    unittest.main()
