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

import wx

from ..publish.messages import RideItemNameChanged
from ..usages.UsageRunner import Usages
from .editors import _RobotTableEditor, FindUsagesHeader
from .kweditor import KeywordEditor


class TestCaseEditor(_RobotTableEditor):
    __test__ = False
    _settings_open_id = 'test case settings open'

    def _populate(self):
        self.header = self._create_header(self.controller.name)
        self.sizer.Add(self.header, 0, wx.EXPAND | wx.ALL, 5)
        self._add_settings()
        self.sizer.Add((0, 10))
        self._create_kweditor()
        self.plugin.subscribe(self._name_changed, RideItemNameChanged)

    def _create_kweditor(self):
        self.kweditor = KeywordEditor(self, self.controller, self._tree)
        self.sizer.Add(self.kweditor, 1, wx.EXPAND | wx.ALL, 2)
        self._editors.append(self.kweditor)

    def _name_changed(self, message):
        # print(f"DEBUG: macroeditors.py TestCaseEditor _name_changed ENTER {message}\n")
        if message.item == self.controller:
            self.header.SetLabel(message.item.name)
            # print(f"DEBUG: macroeditors.py TestCaseEditor _name_changed  DONE {message.item.name=} {self.controller}")

    def close(self):
        for editor in self._editors:
            editor.close()
        super().close()
        self.plugin.unsubscribe(self._name_changed, RideItemNameChanged)

    def save(self):
        self.kweditor.save()

    def undo(self):
        # DEBUG: On Linux we were having double Ctrl-Z action
        # self.kweditor.on_undo()
        pass

    def redo(self):
        self.kweditor.on_redo()

    def cut(self):
        self.kweditor.on_cut()

    def copy(self):
        self.kweditor.on_copy()

    def paste(self):
        self.kweditor.on_paste()

    def insert(self):
        self.kweditor.on_insert()

    def insert_cells(self):
        self.kweditor.on_insert_cells()

    def delete_cells(self):
        # print("DEBUG macro delete cells ")
        self.kweditor.on_delete_cells()

    def insert_rows(self):
        self.kweditor.on_insert_rows(None)  # DEBUG python 3

    def delete_rows(self):
        self.kweditor.on_delete_rows(None)  # DEBUG python 3

    def on_move_rows_up(self):
        self.kweditor.on_move_rows_up()

    def on_move_rows_down(self):
        self.kweditor.on_move_rows_down()

    def delete(self):
        self.kweditor.on_delete()

    def comment_rows(self):
        self.kweditor.on_comment_rows()

    def uncomment_rows(self):
        self.kweditor.on_uncomment_rows()

    def sharp_comment_rows(self):
        self.kweditor.on_sharp_comment_rows()

    def sharp_uncomment_rows(self):
        self.kweditor.on_sharp_uncomment_rows()

    def comment_cells(self):
        self.kweditor.on_comment_cells(None)

    def uncomment_cells(self):
        self.kweditor.on_uncomment_cells(None)

    def show_content_assist(self):
        self.kweditor.show_content_assist()


class UserKeywordEditor(TestCaseEditor):
    _settings_open_id = 'user keyword settings open'

    def _create_header(self, text, readonly=False):
        def cb(event):
            __ = event
            Usages(self.controller, self._tree.highlight).show()
        return FindUsagesHeader(self, text, cb, color_foreground=self.color_secondary_foreground,
                                color_background=self.color_secondary_background)
