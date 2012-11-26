#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robotide.utils import overrides
from robotide.widgets import Dialog, VerticalSizer, VirtualList, Label
import wx
from robotide.widgets.list import ListModel

class TestsDialog(Dialog):

    def __init__(self, search_handler):
        self._search_handler = search_handler
        self._selection_listeners = []
        title = "Search Tests"
        Dialog.__init__(self, title=title, size=(650, 400))
        self.SetSizer(VerticalSizer())
        self._add_search_control()
        self.tests = _TestSearchListModel([])
        self.tests_list = VirtualList(self, ['Test', 'Tags', 'Source'], self.tests)
        self.tests_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(self.tests_list)

    def set_search_model(self, search_text, results):
        self._search_control.SetValue(search_text)
        self.tests._tests = list(results)
        self.tests_list.refresh()

    def _add_search_control(self):
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1)
        self._add_doc_filter(line1)
        self.Sizer.Add(line1, 0, wx.ALL, 3)

    def _horizontal_sizer(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer):
        sizer.Add(Label(self, label='Search term: '))
        self._search_control = wx.SearchCtrl(self, value='', size=(200,-1),style=wx.TE_PROCESS_ENTER)
        wrapped = lambda event: self._search_handler(self._search_control.GetValue())
        self._search_control.Bind(wx.EVT_TEXT_ENTER, wrapped)
        sizer.Add(self._search_control)

    def _add_doc_filter(self, sizer):
        self._use_doc = wx.CheckBox(self, label='Search only tags')
        self._use_doc.SetValue(False)
        sizer.Add(self._use_doc)

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.tests[idx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def set_focus_to_default_location(self):
        if self.tests.count:
            self.tests_list.Select(0)
            self.tests_list.SetFocus()
        else:
            self._search_control.SetFocus()


class _TestSearchListModel(ListModel):

    def __init__(self, tests):
        self._tests = sorted(tests, cmp=lambda x, y: cmp(x[1], y[1]))

    @property
    @overrides(ListModel)
    def count(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def item_text(self, row, col):
        test, match = self._tests[row]
        if col == 0:
            return test.name
        if col == 1:
            return u', '.join(unicode(t) for t in test.tags)
        return test.datafile_controller.longname
