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

from robotide.usages.UsageRunner import Usages
from robotide.publish.messages import RideItemNameChanged

from .kweditor import KeywordEditor
from .editors import _RobotTableEditor, FindUsagesHeader


class TestCaseEditor(_RobotTableEditor):
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

    def _name_changed(self, data):
        if data.item == self.controller:
            self.header.SetLabel(data.item.name)

    def close(self):
        for editor in self._editors:
            editor.close()
        _RobotTableEditor.close(self)
        self.kweditor.close()
        self.plugin.unsubscribe(self._name_changed, RideItemNameChanged)

    def save(self):
        self.kweditor.save()

    def undo(self):
        self.kweditor.OnUndo()

    def redo(self):
        self.kweditor.OnRedo()

    def cut(self):
        self.kweditor.OnCut()

    def copy(self):
        self.kweditor.OnCopy()

    def paste(self):
        self.kweditor.OnPaste()

    def insert(self):
        self.kweditor.OnInsert()

    def insert_cells(self):
        self.kweditor.OnInsertCells()

    def delete_cells(self):
        # print("DEBUG macro delete cells ")
        self.kweditor.OnDeleteCells()

    def insert_rows(self):
        self.kweditor.OnInsertRows(None)  # DEBUG python 3

    def delete_rows(self):
        self.kweditor.OnDeleteRows(None)  # DEBUG python 3

    def delete(self):
        self.kweditor.OnDelete()

    def comment(self):
        self.kweditor.OnCommentRows()

    def uncomment(self):
        self.kweditor.OnUncommentRows()

    def show_content_assist(self):
        self.kweditor.show_content_assist()

    def view(self):
        _RobotTableEditor.view(self)
        self.kweditor.SetFocus()


class UserKeywordEditor(TestCaseEditor):
    _settings_open_id = 'user keyword settings open'

    def _create_header(self, name):
        def cb(event):
            Usages(self.controller, self._tree.highlight).show()
        return FindUsagesHeader(self, name, cb)
