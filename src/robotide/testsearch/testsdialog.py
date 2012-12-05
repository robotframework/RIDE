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
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL | wx.EXPAND, 3)
        self._notebook.AddPage(self._text_search_panel(), 'Text Search')
        self._notebook.AddPage(self._tag_pattern_search_panel(), 'Tag Search')

    def _text_search_panel(self):
        panel = wx.Panel(self._notebook)
        panel.SetSizer(VerticalSizer())
        self._add_search_control(panel)
        self.tests = _TestSearchListModel([])
        self.tests_list = VirtualList(panel, ['Test', 'Tags', 'Source'], self.tests)
        self.tests_list.add_selection_listener(self._usage_selected)
        panel.Sizer.add_expanding(self.tests_list)
        self._results_text = wx.StaticText(panel, -1, 'Results: ')
        panel.Sizer.Add(self._results_text, 0, wx.ALL, 3)
        return panel

    def _tag_pattern_search_panel(self):
        panel = wx.Panel(self._notebook)
        panel.SetSizer(VerticalSizer())
        controls_sizer = self._horizontal_sizer()

        tags_controls_sizer = VerticalSizer()
        include_line = self._horizontal_sizer()
        include_line.Add(Label(panel, label='Include', size=(80, -1)))
        include_line.Add(wx.TextCtrl(panel, value='', size=(400, -1)))
        tags_controls_sizer.Add(include_line, 0, wx.ALL, 3)
        exclude_line = self._horizontal_sizer()
        exclude_line.Add(Label(panel, label='Exclude', size=(80, -1)))
        exclude_line.Add(wx.TextCtrl(panel, value='', size=(400, -1)))
        tags_controls_sizer.Add(exclude_line, 0, wx.ALL, 3)

        controls_sizer.Add(tags_controls_sizer)
        controls_sizer.Add(wx.Button(panel, label='Search'), 0, wx.ALL | wx.EXPAND, 3)

        panel.Sizer.Add(controls_sizer)
        list = VirtualList(panel, ['Test', 'Tags', 'Source'], self.tests)
        panel.Sizer.add_expanding(list)
        results = wx.StaticText(panel, -1, 'Results: ')
        panel.Sizer.Add(results, 0, wx.ALL, 3)
        return panel

    def set_search_model(self, search_text, results):
        results = list(results)
        self._search_control.SetValue(search_text)
        self._results_text.SetLabel('Results: %d' % len(results))
        self.tests._tests = results
        self._refresh_tests_list()

    def _refresh_tests_list(self):
        self.tests_list.refresh()
        self.tests_list.Refresh()

    def _add_search_control(self, panel):
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1, panel)
        line1.Add(wx.Button(panel, label='Search'))
        panel.Sizer.Add(line1, 0, wx.ALL, 3)

    def _horizontal_sizer(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer, parent):
        self._search_control = wx.SearchCtrl(parent, value='', size=(200,-1),style=wx.TE_PROCESS_ENTER)
        self._search_control.SetDescriptiveText('Search term')
        wrapped = lambda event: self._search_handler(self._search_control.GetValue())
        self._search_control.Bind(wx.EVT_TEXT_ENTER, wrapped)
        sizer.Add(self._search_control, 0, wx.ALL, 3)

    def _add_only_tags_filter(self, sizer):
        self._only_tags = wx.CheckBox(self, label='Search as a tag pattern')
        self._only_tags.SetValue(False)
        sizer.Add(self._only_tags)

    @property
    def tags_only(self):
        return self._only_tags.GetValue()

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.tests[idx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def _find_index_in_tests_list(self, test):
        idx = 0
        for tc in self.tests:
            if tc[0] == test:
                return idx
            idx += 1
        return 0

    def set_focus_to_default_location(self, selected=None):
        if self.tests.count:
            if selected:
                self.tests_list.Select(self._find_index_in_tests_list(selected))
            else:
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
