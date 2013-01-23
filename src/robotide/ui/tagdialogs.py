#  Copyright 2008-2013 Nokia Siemens Networks Oyj
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
import wx.lib.mixins.listctrl as listmix

from robot.utils import NormalizedDict
from robotide.controller.tags import ForcedTag, DefaultTag
from robotide.ui.review import ResultListCtrl
from robotide.ui.searchdots import DottedSearch
from robotide.widgets import Dialog, VerticalSizer, VirtualList, Label, ButtonWithHandler
from robotide.widgets.list import ListModel

class ViewAllTagsDialog(wx.Frame):

    def __init__(self, controller, frame):
        wx.Frame.__init__(self, frame, title="View All Tags", style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.FRAME_FLOAT_ON_PARENT)
        self.frame = frame
        self._controller = controller
        self._build_ui()
        self._make_bindings()
        self._execute()

    def _build_ui(self):
        self.SetSize((800,600))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._build_notebook()
        self._build_tag_lister()
        self._build_controls()

    def _build_tag_lister(self):
        panel_tag_vw = wx.Panel(self._notebook)
        sizer_tag_vw = wx.BoxSizer(wx.VERTICAL)
        panel_tag_vw.SetSizer(sizer_tag_vw)
        self._tags_list = ResultListCtrl(panel_tag_vw,style=wx.LC_REPORT)
        self._tags_list.InsertColumn(0, "Tag", width=400)
        self._tags_list.InsertColumn(1, "Occurrences", width=50)
        self._tags_list.InsertColumn(2, "Types", width=200)
        self._tags_list.SetMinSize((650, 250))
        self._tags_list.set_dialog(self)
        sizer_tag_vw.Add(self._tags_list, 1, wx.ALL | wx.EXPAND, 3)
        self._notebook.AddPage(panel_tag_vw, "The List")

    def _build_controls(self):
        self._refresh_button = ButtonWithHandler(self, 'Refresh')
        self._status_label = Label(self, label='')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._refresh_button, 0, wx.ALL, 3)
        controls.Add(self._status_label, 1, wx.ALL | wx.EXPAND, 3)
        self.Sizer.Add(controls, 0, wx.ALL | wx.EXPAND, 3)

    def _build_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL | wx.EXPAND, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        #self.Bind(wx.EVT_BUTTON, self.OnShowfilestobesearched, self._filter_test_button)
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultSelected, self._unused_kw_list)
        #self.Bind(wx.EVT_CHECKBOX, self._upate_filter_regex, self._filter_regex_switch)
        #self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._toggle_filter_active, self._filter_pane)

    def _execute(self):
        results = self._search_results()
        index = 0
        for key, val in results:
            self._tags_list.InsertStringItem(index, str(key))
            occurrences = len(val)
            self._tags_list.SetStringItem(index, 1, str(occurrences))
            type_list = []
            for item in val:
                test_name, tag_type = item.split(":")
                if tag_type not in type_list:
                    type_list.append(tag_type)
            self._tags_list.SetStringItem(index, 2, ','.join(type_list))
            index += 1

    def show_dialog(self):
        if not self.IsShown():
           # self._clear_search_results()
            #self._execute()
            self.Show()
        self.Raise()


    def _clear_search_results(self):
        self._tags_list.ClearAll()
        #self._update_notebook_text('Unused Keywords')
        self._status_label.SetLabel('')

    def add_usage(self, usage):
        self.usages.add_usage(usage)

    def begin_searching(self):
        self._dots = DottedSearch(self, self._update_searching)
        self._dots.start()

    def _update_searching(self, dots):
        self.SetTitle("'%s' - %d matches found - Searching%s" % (self._name, self.usages.total_usages, dots))
        self.usage_list.refresh()

    def end_searching(self):
        self._dots.stop()
        self.SetTitle("'%s' - %d matches" % (self._name, self.usages.total_usages))
        self.usage_list.refresh()

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.usages.usage(idx).item.parent, self._name)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def _add_view_components(self):
        pass

    def _search_results(self):
        self._unique_tags = NormalizedDict()
        tag_info = ""
        for test in self.frame._controller.all_testcases():
            for tag in test.tags:
                tag_info = test.longname
                if isinstance(tag, ForcedTag):
                    tag_info += ":forced"
                elif isinstance(tag, DefaultTag):
                    tag_info += ":default"
                else:
                    tag_info += ":test"
                if self._unique_tags.has_key(unicode(tag)):
                    self._unique_tags[unicode(tag)].append(tag_info)
                else:
                    self._unique_tags.set(unicode(tag), [tag_info])

        return sorted(self._unique_tags.items(), key=lambda x: len(x[1]), reverse=True)

    def _search(self, data):
        for test in data.tests:
            match = False
            if match:
                yield test, match
        for s in data.suites:
            for test, match in self._search(s):
                yield test, match

    def GetListCtrl(self):
        return self.list_ctrl

    def OnColClick(self, event):
        print "column clicked"
        event.Skip()

    def OnRefresh(self, event):
        self._clear_search_results()
        self._execute()

    def _close_dialog(self, event):
        if event.CanVeto():
            self.Hide()
        else:
            self.Destroy()

