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

    def __init__(self, fuzzy_search_handler, tag_search_handler):
        self._fuzzy_search_handler = fuzzy_search_handler
        self._tag_search_handler = tag_search_handler
        self._selection_listeners = []
        title = "Search Tests"
        Dialog.__init__(self, title=title, size=(650, 400))
        self.SetSizer(VerticalSizer())
        self.Sizer.Add(self._create_notebook(), 1, wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, 3)

    def _create_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self._notebook.AddPage(self._text_search_panel(), 'Search')
        self._notebook.AddPage(self._tag_pattern_search_panel(), 'Tag Search')
        return self._notebook

    def _text_search_panel(self):
        panel = wx.Panel(self._notebook)
        panel.SetSizer(VerticalSizer())
        self._add_search_control(panel)
        self.tests = _TestSearchListModel([])
        self.tests_list = VirtualList(panel, ['Test', 'Tags', 'Source'], self.tests)
        self.tests_list.add_selection_listener(self._select_text_search_result)
        panel.Sizer.add_expanding(self.tests_list)
        self._fuzzy_results_text = wx.StaticText(panel, -1, 'Results: ')
        panel.Sizer.Add(self._fuzzy_results_text, 0, wx.ALL, 3)
        return panel

    def _tag_pattern_search_panel(self):
        panel = wx.Panel(self._notebook)
        panel.SetSizer(VerticalSizer())
        tags_controls_sizer = VerticalSizer()
        tags_controls_sizer.Add(self._create_include_line(panel), 0, wx.ALL, 3)
        tags_controls_sizer.Add(self._create_exclude_line(panel), 0, wx.ALL, 3)
        controls_sizer = self._horizontal_sizer()
        controls_sizer.Add(tags_controls_sizer)
        controls_sizer.Add(self._create_tag_search_button(panel), 0, wx.ALL | wx.EXPAND, 3)
        panel.Sizer.Add(controls_sizer)
        panel.Sizer.Add(self._add_info_text(panel, "Find matches using tag patterns.\nSee http://robotframework.googlecode.com/hg/doc/userguide/RobotFrameworkUserGuide.html?#by-tag-names"), 0, wx.ALL, 3)
        self._tags_results = _TestSearchListModel([])
        self._tags_list = VirtualList(panel, ['Test', 'Tags', 'Source'], self._tags_results)
        self._tags_list.add_selection_listener(self._select_tag_search_result)
        panel.Sizer.add_expanding(self._tags_list)
        self._tags_results_text = wx.StaticText(panel, -1, 'Results: ')
        panel.Sizer.Add(self._tags_results_text, 0, wx.ALL, 3)
        return panel

    def _create_include_line(self, panel):
        include_line = self._horizontal_sizer()
        include_line.Add(Label(panel, label='Include', size=(80, -1)))
        self._tags_to_include_text = wx.TextCtrl(panel, value='', size=(400, -1), style=wx.TE_PROCESS_ENTER)
        self._tags_to_include_text.Bind(wx.EVT_TEXT_ENTER, self.OnSearchTags)
        include_line.Add(self._tags_to_include_text)
        return include_line

    def _create_exclude_line(self, panel):
        exclude_line = self._horizontal_sizer()
        exclude_line.Add(Label(panel, label='Exclude', size=(80, -1)))
        self._tags_to_exclude_text = wx.TextCtrl(panel, value='', size=(400, -1), style=wx.TE_PROCESS_ENTER)
        self._tags_to_exclude_text.Bind(wx.EVT_TEXT_ENTER, self.OnSearchTags)
        exclude_line.Add(self._tags_to_exclude_text)
        return exclude_line

    def _create_tag_search_button(self, panel):
        button = wx.Button(panel, label='Search')
        button.Bind(wx.EVT_BUTTON, self.OnSearchTags)
        return button

    def OnSearchTags(self, event):
        self._tag_search_handler(self._tags_to_include_text.GetValue(), self._tags_to_exclude_text.GetValue())

    def set_search_model(self, search_text, results):
        results = list(results)
        self._search_control.SetValue(search_text)
        self._fuzzy_results_text.SetLabel('Results: %d' % len(results))
        self.tests._tests = results
        self._refresh_list(self.tests_list)

    def set_tag_search_model(self, include_text, exclude_text, results):
        results = list(results)
        self._tags_to_include_text.SetValue(include_text)
        self._tags_to_exclude_text.SetValue(exclude_text)
        self._tags_results_text.SetLabel('Results: %d' % len(results))
        self._tags_results._tests = results
        self._refresh_list(self._tags_list)

    def _refresh_list(self, list):
        list.refresh()
        list.Refresh()

    def _add_info_text(self, panel, text = ""):
        infopanel = self._horizontal_sizer()
        infotext = wx.StaticText(panel, label="Info. " + text)
        font = wx.Font(12, wx.NORMAL, wx.ITALIC, wx.NORMAL)
        infotext.SetFont(font)
        infopanel.Add(infotext)
        return infopanel

    def _add_search_control(self, panel):
        panel.SetSizer(VerticalSizer())
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1, panel)
        fuzzy_search_button = wx.Button(panel, label='Search')
        line1.Add(fuzzy_search_button)
        panel.Sizer.Add(line1, 0, wx.ALL, 3)
        panel.Sizer.Add(self._add_info_text(panel, "Find matches by test name, documentation and/or tag."), 0, wx.ALL, 3)

    def _horizontal_sizer(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer, parent):
        self._search_control = wx.SearchCtrl(parent, value='', size=(200,-1), style=wx.TE_PROCESS_ENTER)
        self._search_control.SetDescriptiveText('Search term')
        wrapped = lambda event: self._fuzzy_search_handler(self._search_control.GetValue())
        self._search_control.Bind(wx.EVT_TEXT_ENTER, wrapped)
        sizer.Add(self._search_control, 0, wx.ALL, 3)

    def _select_text_search_result(self, idx):
        for listener in self._selection_listeners:
            listener(self.tests[idx])

    def _select_tag_search_result(self, idx):
        for listener in self._selection_listeners:
            listener(self._tags_results[idx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def _find_index_in_list(self, item, list):
        if item is None:
            return 0
        idx = 0
        for tc in list:
            if tc[0] == item:
                return idx
            idx += 1
        return 0

    def set_focus_to_default_location(self, selected=None):
        if self._notebook.GetSelection() == 0:
            self._set_focus_to_default_location_in_text_search(selected)
        else:
            self._set_focus_to_default_location_in_tag_search(selected)

    def _set_focus_to_default_location_in_text_search(self, selected):
        if self.tests.count:
            self.tests_list.Select(self._find_index_in_list(selected, self.tests))
            self.tests_list.SetFocus()
        else:
            self._search_control.SetFocus()

    def _set_focus_to_default_location_in_tag_search(self, selected):
        if self._tags_results.count:
            self._tags_list.Select(self._find_index_in_list(selected, self._tags_results))
            self._tags_list.SetFocus()
        else:
            self._tags_to_include_text.SetFocus()


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
