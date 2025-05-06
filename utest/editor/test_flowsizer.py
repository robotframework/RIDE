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

import unittest
import wx
from wx import Size, StaticText
from wx.core import NewIdRef

from robotide.editor.flowsizer import HorizontalFlowSizer
from utest.resources import FakeSettings
from time import sleep


class _BaseSuiteTest(unittest.TestCase):

    def setUp(self):
        settings = FakeSettings()
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.Show()

    def tearDown(self):
        wx.CallLater(5000, self.app.ExitMainLoop)
        self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None

class TestFlowSizer(_BaseSuiteTest):

    def test_initiating(self):
        sizer = HorizontalFlowSizer()
        min_size = sizer.CalcMin()
        assert min_size == Size(0, 0)

    def test_recalculate_sizer(self):
        sizer = HorizontalFlowSizer()
        label = StaticText(self.frame, id=-1, label="Example label ")
        sizer.Add(label)
        txt = StaticText(self.frame, id=-1, label="This is the other text field,")
        sizer.Add(txt)
        self.frame.SetSizer(sizer)
        self.frame.Refresh()
        sleep(5)
        lsz = label.GetSize()
        label.SetLabel("Now a big string to verify the resize.")
        txt.SetSize(lsz)
        sizer.RecalcSizes()
        sleep(5)
        self.frame.Refresh()

if __name__ == "__main__":
    unittest.main()
