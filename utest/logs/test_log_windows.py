#  Copyright 2023-     Robot Framework Foundation
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
import pytest
from pytest import MonkeyPatch

from robotide.log import LogWindow, message_to_string


class Message:

    def __init__(self, timestamp, loglevel, message):
        self.timestamp = timestamp
        self.level = loglevel
        self.message = message


log = [Message('20230604 20:40:41.415', 'INFO', 'Found Robot Framework version 6.0.2 from path'),
       Message('20230604 20:40:41.416', 'INFO',
               'Started RIDE v2.0.6dev5\tusing python version 3.11.3\n\t with wx version 4.2.0\n\n in linux.'),
       Message('20230604 21:45:05.579', 'PARSER', "Using test data in HTML format is deprecated. Convert "
                                                  "'/home/helio/Test/Robot/Example_backup.html' to plain text format.")]


class TestLogWindows(unittest.TestCase):

    def test_main_panel(self):
        import wx
        import wx.lib.agw.aui as aui
        from robotide.ui.notebook import NoteBook

        myapp = wx.App(None)
        frame = wx.Frame(None)
        notebook_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | \
                         aui.AUI_NB_TAB_EXTERNAL_MOVE | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS
        note = NoteBook(frame, myapp, notebook_style)

        def my_show(*args):
            print("DEBUG:Called my_show")

        with MonkeyPatch().context() as m:
            # m.setattr(LogWindow, 'Show', my_show)
            self._panel = LogWindow(notebook=note, title='RIDE Log', log=log)
            self._panel._create_ui()
            self._panel.update_log()
            self._panel.Show()
            assert self._panel.title == 'RIDE Log'
            self._panel.SelectAll()
            self._panel.Copy()
            self._panel.SetSize(200, 400)
            self._panel.close(note)

    def test_message_log(self):
        result = message_to_string(log[0])
        assert result.strip() == '20230604 20:40:41.415 [INFO]: Found Robot Framework version 6.0.2 from path'

    def test_message_log_2(self):
        result = message_to_string(log[1])
        assert result == "20230604 20:40:41.416 [INFO]: Started RIDE v2.0.6dev5\tusing" \
                         " python version 3.11.3\n\t with wx version 4.2.0\n\n in linux.\n\n"

    def test_message_parserlog(self):
        result = message_to_string(log[1], True)
        assert result == "20230604 20:40:41.416 [INFO]: Started RIDE v2.0.6dev5\tusing" \
                         " python version 3.11.3 with wx version 4.2.0\n\n in linux.\n\n"


if __name__ == '__main__':
    unittest.main()
