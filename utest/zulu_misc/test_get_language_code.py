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

class TestMisc(unittest.TestCase):

    def test_get_code(self):
        import wx
        from robotide.application import RIDE

        main_app = RIDE()
        code = main_app._get_language_code()
        assert code in (wx.LANGUAGE_ENGLISH, wx.LANGUAGE_ENGLISH_WORLD, wx.LANGUAGE_PORTUGUESE)
        # Uncomment next lines if you want to see the app
        # wx.CallLater(8000, main_app.ExitMainLoop)
        # main_app.MainLoop()


if __name__ == '__main__':
    unittest.main()