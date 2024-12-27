#  Copyright 2024-     Robot Framework Foundation
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

class TestMisc(unittest.TestCase):

    def setUp(self):
        from robotide.application import RIDE
        self.main_app = RIDE()
        self.settings = self.main_app.settings
        self.frame = self.main_app.frame
        self.main_app.SetExitOnFrameDelete(True)


    def tearDown(self):
        self.main_app.Destroy()
        self.main_app = None

    def test_get_code(self):
        code = self.main_app._get_language_code()
        assert code in (wx.LANGUAGE_ENGLISH, wx.LANGUAGE_ENGLISH_WORLD, wx.LANGUAGE_PORTUGUESE)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(8000, main_app.ExitMainLoop)
        # main_app.MainLoop()


if __name__ == '__main__':
    unittest.main()