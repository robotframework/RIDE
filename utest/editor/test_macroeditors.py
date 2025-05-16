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

import unittest
import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True) # Avoid failing unit tests in system without X11
import wx
from .fakeplugin import FakePlugin
from robotide.controller.macrocontrollers import TestCaseController
from robotide.editor.macroeditors import TestCaseEditor


TestCaseEditor._populate = lambda self: None


class IncredibleMock(object):

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self


class MockKwEditor(object):

    _expect = None
    _called = None

    def __getattr__(self, item):
        self._active_item = item
        return self

    def __call__(self, *args, **kwargs):
        self._called = self._active_item

    def is_to_be_called(self):
        self._expect = self._active_item

    def has_been_called(self):
        return self._active_item == self._expect == self._called


class MacroEditorTest(unittest.TestCase):

    def setUp(self):
        myapp = wx.App(None)
        controller = TestCaseController(IncredibleMock(), IncredibleMock())
        plugin = FakePlugin({}, controller)
        self.tc_editor = TestCaseEditor(
            plugin, wx.Frame(None), controller, None)

    def test_delegation_to_kw_editor(self):
        for method, kw_method in \
            [('save', 'save'),
             # ('undo', 'on_undo'),  # Disabled because of double Ctrl-Z
             ('redo', 'on_redo'),
             ('cut', 'on_cut'),
             ('copy', 'on_copy'),
             ('paste', 'on_paste'),
             ('insert', 'on_insert'),
             ('insert_cells', 'on_insert_cells'),
             ('insert_rows', 'on_insert_rows'),
             ('delete_rows', 'on_delete_rows'),
             ('delete_cells', 'on_delete_cells'),
             ('delete', 'on_delete'),
             ('show_content_assist', 'show_content_assist')]:
            kw_mock = MockKwEditor()
            self.tc_editor.kweditor = kw_mock
            getattr(kw_mock, kw_method).is_to_be_called()
            getattr(self.tc_editor, method)()
            assert getattr(kw_mock, kw_method).has_been_called(), (f"Should have called \""
                                                                   f"{kw_method}\" when calling \"{method}\"")


if __name__ == '__main__':
    app = wx.App()
    unittest.main()

