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
from pytest import MonkeyPatch

from robotide.widgets.htmlwnd import HtmlWindow
from utest.resources import FakeSettings


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

class TestHtmlWindows(_BaseSuiteTest):

    def test_initiating_with_data(self):
        dialog = HtmlWindow(self.frame, text='<h2>Initial content</h2>')
        wx.CallLater(2000, dialog.close)
        dialog.Show()

    def test_adding_data_named_color(self):

        with MonkeyPatch().context() as ctx:
            import robotide
            from robotide.preferences.settings import RideSettings

            class SideEffect(RideSettings):

                def __init__(self):
                    _settings = RideSettings.__init__(self)
                    _settings['General'].set('background help', 'green')
                    print("DEBUG: test_htmlwnd.py sideeffect __init__")

                def get(self, name, default):
                    __ = name
                    __ = default
                    print(f"DEBUG: test_htmlwnd.py sideeffect get={'green'}")
                    return 'green'

            with MonkeyPatch().context() as m:
                m.setattr(robotide.preferences.settings, 'RideSettings', SideEffect)
                from time import sleep
                dialog = HtmlWindow(self.frame)
                dialog.Show()
                sleep(2)
                dialog.set_content('<h2>Added content</h2>')
                sleep(4)
                wx.CallLater(4800, dialog.clear)
                dialog.set_content('<h2 align="center">New and centered content</h2>')
                wx.CallLater(4900, dialog.close)

    def test_adding_data(self):
        from time import sleep
        dialog = HtmlWindow(self.frame)
        dialog.set_content('<h2>Added content</h2>')
        dialog.Show()
        wx.CallLater(4800, dialog.clear)
        sleep(4)
        dialog.set_content('<h2 align="center">New and centered content</h2>')
        wx.CallLater(4900, dialog.close)


if __name__ == "__main__":
    unittest.main()
