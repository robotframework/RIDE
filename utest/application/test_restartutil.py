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
import time

from pytest import MonkeyPatch


class RestartUtilTestCase(unittest.TestCase):

    def setUp(self):
        self._callback_called = False
        self.RESULT = True

    def test_restart_dialog(self):
        import robotide.application
        import wx
        import robotide.application.updatenotifier

        def my_ask(title, message, frame=None,  no_default=False):
            print("DEBUG:Called my_ask")
            time.sleep(1)
            self._callback_called = True
            return self.RESULT

        with MonkeyPatch().context() as ctx:
            myapp = wx.App(None)
            self.frame = wx.Frame(None)

            with MonkeyPatch().context() as m:
                m.setattr(robotide.application.updatenotifier, '_askyesno', my_ask)
                from robotide.application.restartutil import do_restart, restart_dialog
                self.RESULT = True
                result = restart_dialog()
                time.sleep(2)
                # assert result is False  # OK when running with invoke test-ci
                assert result is True  # OK running in IDE or with invoke on real system
                self.RESULT = False
                result = restart_dialog()
                time.sleep(2)
                assert result is False
                assert self._callback_called is True
                self._callback_called = False
                self.RESULT = False
                result = do_restart()
                time.sleep(6)
                assert result is False
                assert self._callback_called is True


if __name__ == '__main__':
    unittest.main()
