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
from robotide.widgets import Dialog, VerticalSizer, VirtualList, Label
import wx

class TestsDialog(Dialog):

    def __init__(self, search_text, tests):
        self._search_text = search_text
        self._selection_listeners = []
        title = "Search Tests (%d)" % tests.count
        Dialog.__init__(self, title=title, size=(650, 400))
        self.SetSizer(VerticalSizer())
        self._add_search_control()
        self.tests = tests
        #TODO: Why is third header needed? - for some reason does not show second column texts without
        self.tests_list = VirtualList(self, ['Test', 'Tags', 'Source'], self.tests)
        self.tests_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(self.tests_list)

    def _add_search_control(self):
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1)
        self._add_doc_filter(line1)
        self.Sizer.Add(line1, 0, wx.ALL, 3)

    def _horizontal_sizer(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer):
        sizer.Add(Label(self, label='Search term: '))
        self._search_control = wx.SearchCtrl(self, value=self._search_text, size=(200,-1),style=wx.TE_PROCESS_ENTER)
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
