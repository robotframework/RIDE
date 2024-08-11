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

from functools import (total_ordering, cmp_to_key)
import builtins
import wx
from wx import Colour

from ..widgets import (RIDEDialog, VerticalSizer, VirtualList, Label,
                       HelpLabel, ImageProvider)
from ..widgets.list import ListModel

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class TestsDialog(RIDEDialog):

    def __init__(self, fuzzy_search_handler, tag_search_handler, add_to_selected_handler):
        self._fuzzy_search_handler = fuzzy_search_handler
        self._tag_search_handler = tag_search_handler
        self._add_to_selected_handler = add_to_selected_handler
        self._selection_listeners = []
        title = _("Search Tests")
        RIDEDialog.__init__(self, title=title, size=(800, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self.SetSizer(VerticalSizer())
        self.Sizer.Add(self._create_notebook(), 1, wx.ALL | wx.EXPAND | wx.ALIGN_LEFT, 3)

    def _create_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self._notebook.SetBackgroundColour(Colour(self.color_background))
        self._notebook.SetForegroundColour(Colour(self.color_foreground))
        self._notebook.AddPage(self._text_search_panel(), _('Search'))
        self._notebook.AddPage(self._tag_pattern_search_panel(), _('Tag Search'))
        return self._notebook

    def select_page(self, page=0):
        self._notebook.ChangeSelection(page)

    def _text_search_panel(self):
        panel = wx.Panel(self._notebook)
        panel.SetSizer(VerticalSizer())
        self._add_search_control(panel)
        self.tests = _TestSearchListModel([])
        self.tests_list = VirtualList(panel, [_('Test'), _('Tags'), _('Source')], self.tests)
        self.tests_list.SetBackgroundColour(Colour(self.color_secondary_background))
        self.tests_list.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.tests_list.add_selection_listener(self._select_text_search_result)
        panel.Sizer.add_expanding(self.tests_list)
        self._fuzzy_results_text = wx.StaticText(panel, -1, _('Results: '))
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
        controls_sizer.Add(self._create_switch_button(panel), 0, wx.CENTER, 3)
        controls_sizer.Add(self._create_tag_search_button(panel), 0, wx.ALL | wx.EXPAND, 3)
        controls_sizer.Add(self._create_add_to_selected_button(panel), 0, wx.ALL | wx.EXPAND, 3)
        panel.Sizer.Add(controls_sizer)
        panel.Sizer.Add(self._add_info_text(panel, _("Find matches using tag patterns. See RF User "
                                                     "Guide or 'robot --help' for more information.")), 0, wx.ALL, 3)
        self._tags_results = _TestSearchListModel([])
        self._tags_list = VirtualList(panel, [_('Test'), _('Tags'), _('Source')], self._tags_results)
        self._tags_list.SetBackgroundColour(Colour(self.color_secondary_background))
        self._tags_list.SetForegroundColour(Colour(self.color_secondary_foreground))
        self._tags_list.add_selection_listener(self._select_tag_search_result)
        panel.Sizer.add_expanding(self._tags_list)
        self._tags_results_text = wx.StaticText(panel, -1, _('Results: '))
        panel.Sizer.Add(self._tags_results_text, 0, wx.ALL, 3)
        return panel

    def _create_include_line(self, panel):
        include_line = self._horizontal_sizer()
        include_line.Add(Label(panel, label=_('Include'), size=(80, -1)))
        self._tags_to_include_text = wx.TextCtrl(panel, value='', size=(400, -1),
                                                 style=wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL)
        self._tags_to_include_text.SetBackgroundColour(Colour(self.color_secondary_background))
        self._tags_to_include_text.SetForegroundColour(Colour(self.color_secondary_foreground))
        self._tags_to_include_text.Bind(wx.EVT_TEXT_ENTER, self.on_search_tags)
        include_line.Add(self._tags_to_include_text)
        return include_line

    def _create_switch_button(self, panel):
        sizer = self._vertical_sizer()
        img = ImageProvider().SWITCH_FIELDS_ICON
        button = wx.BitmapButton(panel, -1, img, pos=(10, 20))
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.Bind(wx.EVT_BUTTON, self.on_switch_fields, button)
        sizer.Add(button)
        return sizer

    def _create_exclude_line(self, panel):
        exclude_line = self._horizontal_sizer()
        exclude_line.Add(Label(panel, label=_('Exclude'), size=(80, -1)))
        self._tags_to_exclude_text = wx.TextCtrl(panel, value='', size=(400, -1),
                                                 style=wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL)
        self._tags_to_exclude_text.SetBackgroundColour(Colour(self.color_secondary_background))
        self._tags_to_exclude_text.SetForegroundColour(Colour(self.color_secondary_foreground))
        self._tags_to_exclude_text.Bind(wx.EVT_TEXT_ENTER, self.on_search_tags)
        exclude_line.Add(self._tags_to_exclude_text)
        return exclude_line

    def _create_tag_search_button(self, panel):
        button = wx.Button(panel, label=_('Search'))
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        button.Bind(wx.EVT_BUTTON, self.on_search_tags)
        return button

    def on_search_tags(self, event):
        __ = event
        self._tag_search_handler(self._tags_to_include_text.GetValue(),
                                 self._tags_to_exclude_text.GetValue())

    def _create_add_to_selected_button(self, panel):
        button = wx.Button(panel, label=_('Add all to selected'))
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        button.Bind(wx.EVT_BUTTON, self.on_add_to_selected)
        return button

    def on_add_to_selected(self, event):
        __ = event
        self._add_to_selected_handler(self._get_current_tests())

    def on_search_tests(self, event):
        __ = event
        self._fuzzy_search_handler(self._search_control.GetValue())

    def set_search_model(self, search_text, results):
        results = list(results)
        self._search_control.SetValue(search_text)
        self._fuzzy_results_text.SetLabel(_('Results: %d') % len(results))
        self.tests.sorted_tests = results
        self._refresh_list(self.tests_list)

    def set_tag_search_model(self, include_text, exclude_text, results):
        results = list(results)
        self._tags_to_include_text.SetValue(include_text)
        self._tags_to_exclude_text.SetValue(exclude_text)
        self._tags_results_text.SetLabel(_('Results: %d') % len(results))
        self._tags_results.sorted_tests = results
        self._refresh_list(self._tags_list)

    @staticmethod
    def _refresh_list(llist):
        llist.refresh_items()
        llist.Refresh()
        if llist.GetItemCount():
            llist.inform_listeners(0)

    def _add_info_text(self, panel, text=""):
        infopanel = self._horizontal_sizer()
        infopanel.Add(HelpLabel(panel, _("Info. ") + text))
        return infopanel

    def _add_search_control(self, panel):
        panel.SetSizer(VerticalSizer())
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1, panel)
        fuzzy_search_button = wx.Button(panel, label=_('Search'))
        fuzzy_search_button.SetBackgroundColour(Colour(self.color_secondary_background))
        fuzzy_search_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        fuzzy_search_button.Bind(wx.EVT_BUTTON, self.on_search_tests)
        line1.Add(fuzzy_search_button, 0, wx.ALL | wx.EXPAND, 3)
        add_to_selection_button = wx.Button(panel, label=_('Add all to selected'))
        add_to_selection_button.SetBackgroundColour(Colour(self.color_secondary_background))
        add_to_selection_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        add_to_selection_button.Bind(wx.EVT_BUTTON, self.on_add_to_selected)
        line1.Add(add_to_selection_button, 0, wx.ALL | wx.EXPAND, 3)
        panel.Sizer.Add(line1, 0, wx.ALL, 3)
        panel.Sizer.Add(self._add_info_text(panel, _("Find matches by test name, documentation and/or tag.")),
                        0, wx.ALL, 3)
        panel.Sizer.Layout()

    @staticmethod
    def _horizontal_sizer():
        return wx.BoxSizer(wx.HORIZONTAL)

    @staticmethod
    def _vertical_sizer():
        return wx.BoxSizer(wx.VERTICAL)

    def _add_pattern_filter(self, sizer, parent):
        self._search_control = wx.SearchCtrl(parent, value='', size=(200, -1),
                                             style=wx.TE_PROCESS_ENTER)
        self._search_control.SetBackgroundColour(Colour(self.color_secondary_background))
        self._search_control.SetForegroundColour(Colour(self.color_secondary_foreground))
        self._search_control.SetDescriptiveText(_('Search term'))
        self._search_control.Bind(wx.EVT_TEXT_ENTER, self.wrapped)
        sizer.Add(self._search_control, 0, wx.ALL, 3)

    def wrapped(self, event):
        __ = event
        return self._fuzzy_search_handler(self._search_control.GetValue())

    def _select_text_search_result(self, idx):
        if idx != -1:
            for listener in self._selection_listeners:
                listener(self.tests[idx])

    def _select_tag_search_result(self, idx):
        for listener in self._selection_listeners:
            listener(self._tags_results[idx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    @staticmethod
    def _find_index_in_list(item, llist):
        if item is None:
            return 0
        idx = 0
        for tc in llist:
            if tc[0] == item:
                return idx
            idx += 1
        return 0

    def set_focus_to_default_location(self, selected=None):
        if self._notebook.GetSelection() == 0:
            self._set_focus_to_default_location_in_text_search(selected)
        else:
            self._set_focus_to_default_location_in_tag_search(selected)

    def _get_current_tests(self):
        if self._notebook.GetSelection() == 0:
            return [t for t, _ in self.tests.sorted_tests]
        else:
            return [test for test, _ in self._tags_results.sorted_tests]

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

    def on_switch_fields(self, event):
        include_txt = self._tags_to_include_text.GetValue()
        exclude_txt = self._tags_to_exclude_text.GetValue()

        if len(include_txt.strip()) > 0 or len(exclude_txt.strip()) > 0:
            self._tags_to_include_text.SetValue(exclude_txt)
            self._tags_to_exclude_text.SetValue(include_txt)
            self.on_search_tags(event)


@total_ordering
class _TestSearchListModel(ListModel):

    def __init__(self, tests):
        self.sorted_tests = sorted(tests, key=cmp_to_key(lambda x, y: self.m_cmp(x[1], y[1])))

    @property
    def count(self):
        return len(self.sorted_tests)

    def __getitem__(self, item):
        return self.sorted_tests[item]

    def item_text(self, row, col):
        test, _ = self.sorted_tests[row]
        if col == 0:
            return test.name
        if col == 1:
            return u', '.join(str(t) for t in test.tags)
        return test.datafile_controller.longname

    @staticmethod
    def m_cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__class__.__name__.lower() == other.name.lower()

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return self.__class__.__name__.lower() < other.name.lower()
