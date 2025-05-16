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
from robotide.preferences.managesettingsdialog import SaveLoadSettings
from time import sleep
from utest.resources import FakeSettings, UIUnitTestBase


_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

ID_LOAD = 5551
ID_SAVE = 5552
ID_CANCEL = -1
settings = FakeSettings()

class MyEvent(object):
    def __init__(self, iid):
        self.id = iid

    def GetId(self):
        return self.id

    def Skip(self):
        pass


class TestSaveLoadSettings(UIUnitTestBase):

    def test_on_load_cancel(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        dlg = SaveLoadSettings(self.frame, settings)
        # wx.CallLater(5000, dlg.EndModal,ID_CANCEL)
        dlg.CenterOnParent()
        dlg.Show()
        sleep(5)
        result = dlg.on_load(MyEvent(ID_SAVE))
        assert dlg.GetTitle() == _("Save or Load Settings")
        assert result==ID_CANCEL

    def test_on_load(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        dlg = SaveLoadSettings(self.frame, settings)
        wx.CallLater(5000, dlg.Close, True)
        dlg.CenterOnParent()
        # dlg.Show()
        sleep(2)
        # TODO: mock wx.FileDialog
        # result = dlg.on_load(MyEvent(ID_LOAD))
        assert dlg.GetTitle() == _("Save or Load Settings")
        # assert result==ID_LOAD

    def test_on_save_cancel(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        dlg = SaveLoadSettings(self.frame, settings)
        # wx.CallLater(5000, dlg.EndModal,ID_CANCEL)
        dlg.CenterOnParent()
        dlg.Show()
        sleep(5)
        result = dlg.on_save(MyEvent(ID_LOAD))
        assert dlg.GetTitle() == _("Save or Load Settings")
        assert result==ID_CANCEL

    def test_on_save(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        dlg = SaveLoadSettings(self.frame, settings)
        wx.CallLater(5000, dlg.Close, True)
        dlg.CenterOnParent()
        # dlg.Show()
        sleep(2)
        # TODO: mock wx.FileDialog
        # result = dlg.on_save(MyEvent(ID_SAVE)
        assert dlg.GetTitle() == _("Save or Load Settings")
        # assert result==ID_SAVE

    def test_on_close(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        dlg = SaveLoadSettings(self.frame, settings)
        # wx.CallLater(5000, dlg.EndModal,ID_CANCEL)
        dlg.CenterOnParent()
        dlg.Show()
        sleep(5)
        result = dlg.on_close()
        assert dlg.GetTitle() == _("Save or Load Settings")
        assert result==ID_CANCEL

    def test_load_and_merge_fails(self):
        self.frame = wx.Frame(None)
        self.frame.CenterOnScreen()
        self.frame.Show()
        settings.add_section('Plugins')
        settings.get_without_default('Plugins').add_section('Grid')
        dlg = SaveLoadSettings(self.frame, settings)
        # wx.CallLater(5000, dlg.EndModal,ID_CANCEL)
        dlg.CenterOnParent()
        dlg.Show()
        sleep(2)
        # TODO: assert Exception
        try:
            dlg.load_and_merge('nonvalid_path.cfg')
        except KeyError:
            pass




if __name__ == '__main__':
    unittest.main()
