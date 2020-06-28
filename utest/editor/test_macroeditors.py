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
import wx
from editor.fakeplugin import FakePlugin
from nose.tools import assert_true
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
        controller = TestCaseController(IncredibleMock(), IncredibleMock())
        plugin = FakePlugin({}, controller)
        self.tc_editor = TestCaseEditor(
            plugin, wx.Frame(None), controller, None)

    def test_delegation_to_kw_editor(self):
        for method, kw_method in \
            [('save', 'save'),
             ('undo', 'OnUndo'),
             ('redo', 'OnRedo'),
             ('cut', 'OnCut'),
             ('copy', 'OnCopy'),
             ('paste', 'OnPaste'),
             ('insert', 'OnInsert'),
             ('insert_rows', 'OnInsertRows'),
             ('delete_rows', 'OnDeleteRows'),
             ('delete', 'OnDelete'),
             ('comment', 'OnCommentRows'),
             ('uncomment', 'OnUncommentRows'),
             ('show_content_assist', 'show_content_assist')]:
            kw_mock = MockKwEditor()
            self.tc_editor.kweditor = kw_mock
            getattr(kw_mock, kw_method).is_to_be_called()
            getattr(self.tc_editor, method)()
            assert_true(getattr(kw_mock, kw_method).has_been_called(),
                        'Should have called "%s" when calling "%s"' %
                        (kw_method, method))


if __name__ == '__main__':
    app = wx.App()
    unittest.main()

