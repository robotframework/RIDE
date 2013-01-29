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
from robotide.publish import PUBLISHER, RideOpenTagSearch
from robotide.searchtests.dialogsearchtests import TestsDialog
from robotide.searchtests.searchtests import TestSearchPlugin
from robotide.ui.searchdots import DottedSearch
from robotide.ui.treenodehandlers import ResourceRootHandler, ResourceFileHandler
from robotide.usages.UsageRunner import ResourceFileUsages
from robotide.widgets import Label, ButtonWithHandler

class ViewAllTagsDialog(wx.Frame):

    def __init__(self, controller, frame):
        wx.Frame.__init__(self, frame, title="View All Tags", style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.FRAME_FLOAT_ON_PARENT)
        self.frame = frame
        self.tree = self.frame.tree
        self._controller = controller
        self._results = NormalizedDict()
        self.selected_tests = 0
        self.total_occurrences = 0
        self.unique_tags = 0
        self._build_ui()
        self._make_bindings()
        self._execute()

    def _build_ui(self):
        self.SetSize((600,600))
        self.SetPosition((500,300))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._build_notebook()
        self._build_tag_lister()
        self._build_controls()
        self._build_footer()

    def _build_tag_lister(self):
        panel_tag_vw = wx.Panel(self._notebook)
        sizer_tag_vw = wx.BoxSizer(wx.VERTICAL)
        panel_tag_vw.SetSizer(sizer_tag_vw)
        self._tags_list = TagsListCtrl(panel_tag_vw,style=wx.LC_REPORT)
        self._tags_list.InsertColumn(0, "Tag", width=300)
        self._tags_list.InsertColumn(1, "Occurrences", width=25, format=wx.LIST_FORMAT_CENTER)
        #self._tags_list.InsertColumn(2, "Types", width=150)
        self._tags_list.SetMinSize((550, 250))
        self._tags_list.set_dialog(self)
        sizer_tag_vw.Add(self._tags_list, 1, wx.ALL | wx.EXPAND, 3)
        self._notebook.AddPage(panel_tag_vw, "The List")

    def _build_controls(self):
        self._clear_button = ButtonWithHandler(self, 'Clear')
        self._show_tests_button = ButtonWithHandler(self, 'Show Tests')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._show_tests_button, 0, wx.ALL, 3)
        controls.Add(self._clear_button, 0, wx.ALL, 3)
        self.Sizer.Add(controls, 0, wx.ALL | wx.EXPAND, 3)

    def _build_footer(self):
        footer = wx.BoxSizer(wx.HORIZONTAL)
        self._footer_text = wx.StaticText(self, -1, 'Results: %d' % len(self._results.items()))
        footer.Add(self._footer_text)
        self.Sizer.Add(footer, 0, wx.ALL, 3)

    def _build_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL | wx.EXPAND, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTagSelected)
        #self.Bind(wx.EVT_BUTTON, self.OnShowfilestobesearched, self._filter_test_button)
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultSelected, self._unused_kw_list)
        #self.Bind(wx.EVT_CHECKBOX, self._upate_filter_regex, self._filter_regex_switch)
        #self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._toggle_filter_active, self._filter_pane)

    def _execute(self):
        self._results = self._search_results()
        index = 0
        self.total_occurrences = 0
        self.unique_tags = 0

        for tag_name, tests in self._results:
            #tag_name, tag_type = tag_data.split(":")
            self._tags_list.SetClientData(self.unique_tags, (tests,tag_name))
            self._tags_list.InsertStringItem(self.unique_tags, str(tag_name))
            occurrences = len(tests)
            self.total_occurrences += occurrences
            self._tags_list.SetStringItem(self.unique_tags, 1, str(occurrences))
            #self._tags_list.SetStringItem(index, 2, str(tag_type))
            self.unique_tags += 1
        self._tags_list.SetColumnWidth(1,wx.LIST_AUTOSIZE_USEHEADER)
        self._tags_list.setResizeColumn(1)
        self.update_footer()

    def update_footer(self):
        footer_string = "Tagged tests %d, Unique tags %d, Selected tests %d" % \
                    (self.total_occurrences, self.unique_tags, self.selected_tests)
        self._footer_text.SetLabel(footer_string)

    def show_dialog(self):
        if not self.IsShown():
            self.Show()
        self.Raise()

    def _clear_search_results(self):
        self.selected_tests = 0
        self._tags_list.ClearAll()

    def _add_view_components(self):
        pass

    def _search_results(self):
        self._unique_tags = NormalizedDict()
        for test in self.frame._controller.all_testcases():
            for tag in test.tags:
                tag_info = unicode(tag)
                #if isinstance(tag, ForcedTag):
                #    tag_info += ":forced"
                #elif isinstance(tag, DefaultTag):
                #    tag_info += ":default"
                #else:
                #    tag_info += ":test"
                if self._unique_tags.has_key(tag_info):
                    self._unique_tags[tag_info].append(test)
                else:
                    self._unique_tags.set(tag_info, [test])

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
        return self._tags_list

    def OnColClick(self, event):
        event.Skip()

    def OnShowTests(self, event):
        included_tags = []
        excluded_tags = []
        for tests,tag_name in self._tags_list.get_checked_items():
            included_tags.append(tag_name)
        RideOpenTagSearch(includes=' '.join(included_tags), excludes=' '.join(excluded_tags)).publish()

    def OnClear(self, event):
        self._clear_search_results()
        self._execute()
        for tag_name, tests in self._results:
            self.tree.DeselectTests(tests)
        #print dir(self.tree)
        #self.tree.CollapseAndReset(self.tree._root)
        for item in self.tree.GetItemChildren():
            if not isinstance(item.GetData(), ResourceRootHandler or ResourceFileHandler):
                self.tree.CollapseAllSubNodes(item)
        self.update_footer()

    def _close_dialog(self, event):
        if event.CanVeto():
            self.Hide()
        else:
            self.Destroy()

    def OnTagSelected(self, event):
        item = self._tags_list.GetItem(event.GetIndex())

    def item_in_kw_list_checked(self, index, flag):
        self.selected_tests = 0
        if flag == False:
            self.tree.DeselectTests(self._tags_list.GetClientData(index))
        if self._tags_list.get_number_of_checked_items() > 0:
            for tests,tag_name in self._tags_list.get_checked_items():
                self.selected_tests += len(tests)
                self.tree.SelectTests(tests)
        self.update_footer()


class TagsListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, style):
        self.parent = parent
        wx.ListCtrl.__init__(self, parent=parent, style=style)
        listmix.CheckListCtrlMixin.__init__(self)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(2)
        self._clientData = {}

    def OnCheckItem(self, index, flag):
        if self._dlg:
            self._dlg.item_in_kw_list_checked(index,flag)
        else:
            pass

    def get_next_checked_item(self):
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                item = self.GetItem(i)
                return ([i, self.GetClientData(item.GetData()), item])
        return None

    def get_checked_items(self):
        items = []
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                items.append(self.GetClientData(i))
        return items

    def get_number_of_checked_items(self):
        sum = 0
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                sum += 1
        return sum

    def set_dialog(self, dialog):
        self._dlg = dialog

    def SetClientData(self, index, data):
        self._clientData[index] = data

    def GetClientData(self, index):
        return self._clientData.get(index, None)

    def RemoveClientData(self, index):
        del self._clientData[index]

    def ClearAll(self):
        self.DeleteAllItems()
        self._clientData.clear()

    def print_data(self):
        print self._clientData