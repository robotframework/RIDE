#  Copyright 2008-2015 Nokia Solutions and Networks
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

from robotide import utils
from robotide.controller.commands import ChangeTag, DeleteTag
from robotide.publish import RideOpenTagSearch
from robotide.ui.treenodehandlers import ResourceRootHandler, \
    ResourceFileHandler
from robotide.widgets import ButtonWithHandler, PopupMenuItems


class ViewAllTagsDialog(wx.Frame):

    def __init__(self, controller, frame):
        style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | \
            wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, frame, title="View all tags", style=style)
        self.frame = frame
        self.tree = self.frame.tree
        self._controller = controller
        self._results = utils.NormalizedDict()
        self.selected_tests = list()
        self.tagged_test_cases = list()
        self.unique_tags = 0
        self.total_test_cases = 0
        self._index = -1
        self._build_ui()
        self._make_bindings()

    def _build_ui(self):
        self.SetSize((500, 400))
        parent_x, parent_y = self.frame.GetPosition()
        parent_size_x, parent_size_y = self.frame.tree.GetSize()
        self.SetPosition((parent_x + parent_size_x + 50, parent_y + 50))
        self.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._build_notebook()
        self._build_tag_lister()
        self._build_controls()
        self._build_footer()

    def _build_tag_lister(self):
        panel_tag_vw = wx.Panel(self._notebook)
        sizer_tag_vw = wx.BoxSizer(wx.VERTICAL)
        panel_tag_vw.SetSizer(sizer_tag_vw)
        self._tags_list = TagsListCtrl(panel_tag_vw, style=wx.LC_REPORT)
        self._tags_list.InsertColumn(0, "Tag", width=200)
        self._tags_list.InsertColumn(1, "Occurrences", width=25,
                                     format=wx.LIST_FORMAT_CENTER)
        self._tags_list.SetMinSize((450, 250))
        self._tags_list.set_dialog(self)
        sizer_tag_vw.Add(self._tags_list, 1, wx.ALL | wx.EXPAND, 3)
        self._notebook.AddPage(panel_tag_vw, "The List")

    def _build_controls(self):
        self._clear_button = ButtonWithHandler(self, 'Refresh', self.OnClear)
        self._show_tagged_tests_button = ButtonWithHandler(
            self, 'Included Tag Search')
        self._show_excluded_tests_button = ButtonWithHandler(
            self, 'Excluded Tag Search')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._show_tagged_tests_button, 0, wx.ALL, 3)
        controls.Add(self._show_excluded_tests_button, 0, wx.ALL, 3)
        controls.Add(self._clear_button, 0, wx.ALL, 3)
        self.Sizer.Add(controls, 0, wx.ALL | wx.EXPAND, 3)

    def _build_footer(self):
        footer = wx.BoxSizer(wx.HORIZONTAL)
        self._footer_text = wx.StaticText(self, -1, '')
        footer.Add(self._footer_text)
        self.Sizer.Add(footer, 0, wx.ALL, 3)

    def _build_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL | wx.EXPAND, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTagSelected)
        self._tags_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)

    def _execute(self):
        self._clear_search_results()
        self._search_for_tags()

        self.tagged_test_cases = list()
        self.unique_tags = 0

        for tag_name, tests in self._results:
            self._tags_list.SetClientData(self.unique_tags, (tests, tag_name))
            self._tags_list.InsertStringItem(
                self.unique_tags, unicode(tag_name))
            self.tagged_test_cases += tests
            self._tags_list.SetStringItem(self.unique_tags, 1, str(len(tests)))
            self.unique_tags += 1
        self._tags_list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self._tags_list.setResizeColumn(1)
        self.tagged_test_cases = list(set(self.tagged_test_cases))
        self.update_footer()

    def update_footer(self):
        footer_string = "Total tests %d, Tests with tags %d, Unique tags %d, Currently selected tests %d" % \
            (self.total_test_cases, len(self.tagged_test_cases),
             self.unique_tags, len(self.selected_tests))
        self._footer_text.SetLabel(footer_string)

    def show_dialog(self):
        self._execute()
        if not self.IsShown():
            self.Show()
        self.Raise()

    def _clear_search_results(self):
        self.selected_tests = list()
        self._tags_list.ClearAll()

    def _add_view_components(self):
        pass

    def _search_for_tags(self):
        self._unique_tags = utils.NormalizedDict()
        self._tagit = utils.NormalizedDict()
        self._test_cases = list()
        for test in self.frame._controller.all_testcases():
            self._test_cases.append(test)
            for tag in test.tags:
                if tag.is_empty() or len(unicode(tag).strip()) == 0:
                    continue
                else:
                    tag_name = unicode(tag)
                if tag_name in self._unique_tags:
                    self._unique_tags[tag_name].append(test)
                    self._tagit[tag_name].append(tag)
                else:
                    self._unique_tags.set(tag_name, [test])
                    self._tagit[tag_name] = [tag]

        self.total_test_cases = len(self._test_cases)
        self._results = sorted(
            self._unique_tags.items(), key=lambda x: len(x[1]), reverse=True)

    def GetListCtrl(self):
        return self._tags_list

    def OnColClick(self, event):
        event.Skip()

    def _add_checked_tags_into_list(self):
        tags = []
        for _, tag_name in self._tags_list.get_checked_items():
            tags.append(tag_name)
        return tags

    def OnIncludedTagSearch(self, event):
        included_tags = self._add_checked_tags_into_list()
        RideOpenTagSearch(includes=' '.join(included_tags),
                          excludes='').publish()

    def OnExcludedTagSearch(self, event):
        excluded_tags = self._add_checked_tags_into_list()
        RideOpenTagSearch(includes='',
                          excludes=' '.join(excluded_tags)).publish()

    def OnClear(self, event):
        self._execute()
        for _, tests in self._results:
            self.tree.DeselectTests(tests)
        for item in self.tree.GetItemChildren():
            if not isinstance(item.GetData(), ResourceRootHandler or
                              ResourceFileHandler):
                self.tree.CollapseAllSubNodes(item)
        self.update_footer()

    def OnSelectAll(self, event):
        all_tests = []
        for _, tests in self._results:
            all_tests += tests
        self.tree.SelectTests(all_tests)
        self._tags_list.CheckAll()

    def OnRightClick(self, event):
        self._index = event.GetIndex()
        menu_items = ["Select all", "Clear", "---", "Rename", "Delete", "---",
                      "Show tests with this tag",
                      "Show tests without this tag"]
        self.tree._popup_creator.show(self, PopupMenuItems(self, menu_items),
                                      self._controller)

    def OnShowTestsWithThisTag(self, event):
        if self._index == -1:
            return
        _, tag_name = self._tags_list.GetClientData(self._index)
        RideOpenTagSearch(includes=tag_name, excludes="").publish()

    def OnShowTestsWithoutThisTag(self, event):
        if self._index == -1:
            return
        _, tag_name = self._tags_list.GetClientData(self._index)
        RideOpenTagSearch(includes="", excludes=tag_name).publish()

    def OnRename(self, event):
        if self._index == -1:
            return
        tests, tag_name = self._tags_list.GetClientData(self._index)
        tags_to_rename = self._tagit[tag_name.lower()]
        name = wx.GetTextFromUser(
            message="Renaming tag '%s'." % tag_name, default_value=tag_name,
            caption='Rename')
        if name:
            for tag in tags_to_rename:
                tag.controller.execute(ChangeTag(tag, name))
            self._execute()
            for tag_name, tests in self._results:
                self.tree.DeselectTests(tests)

    def OnDelete(self, event):
        if self._index == -1:
            return
        tests, tag_name = self._tags_list.GetClientData(self._index)
        tags_to_delete = self._tagit[tag_name]
        if wx.MessageBox(
            "Delete a tag '%s' ?" % tag_name, caption='Confirm',
                style=wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            for tag in tags_to_delete:
                tag.execute(DeleteTag())
            self._execute()
            for tag_name, tests in self._results:
                self.tree.DeselectTests(tests)

    def _close_dialog(self, event):
        if event.CanVeto():
            self.Hide()
        else:
            self.Destroy()

    def OnTagSelected(self, event):
        self._tags_list.GetItem(event.GetIndex())

    def item_in_kw_list_checked(self, index, flag):
        self.selected_tests = list()
        if flag is False:
            tests, _ = self._tags_list.GetClientData(index)
            self.tree.DeselectTests(tests)
        if self._tags_list.get_number_of_checked_items() > 0:
            for tests, _ in self._tags_list.get_checked_items():
                self.selected_tests += tests
                self.tree.SelectTests(tests)
        self.selected_tests = list(set(self.selected_tests))
        self.update_footer()


class TagsListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin,
                   listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, style):
        self.parent = parent
        wx.ListCtrl.__init__(self, parent=parent, style=style)
        listmix.CheckListCtrlMixin.__init__(self)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(2)
        self._clientData = {}

    def OnCheckItem(self, index, flag):
        if self._dlg:
            self._dlg.item_in_kw_list_checked(index, flag)
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
        total = 0
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                total += 1
        return total

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

    def CheckAll(self):
        for i in range(self.GetItemCount()):
            self.CheckItem(i)
