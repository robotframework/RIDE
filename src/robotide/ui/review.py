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

import os
import wx
import wx.lib.mixins.listctrl as listmix
import time
import re
from robotide.context import IS_MAC
from robotide.ui.searchdots import DottedSearch
from robotide.widgets import ButtonWithHandler, Label
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.usages.commands import FindUsages
from robotide.controller.filecontrollers import TestCaseFileController, ResourceFileController, TestDataDirectoryController
from threading import Thread

class ReviewDialog(wx.Frame):

    def __init__(self, controller, frame):
        wx.Frame.__init__(self, frame, title="Search unused keywords", style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.index = 0
        self.frame = frame
        self._search_model = ResultModel()
        self._runner = ReviewRunner(controller, self._search_model)
        self._build_ui()
        self._make_bindings()
        self._set_default_values()
        self.CenterOnParent()

    def _build_ui(self):
        self.SetSize((800,600))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._build_header()
        self._build_filter()
        self._build_notebook()
        self._build_unused_keywords()
        self._build_controls()

    def _build_header(self):
        label_introduction = wx.StaticText(self,
                                           label='This dialog helps you finding unused keywords within your opened proj'
                                                 'ect.\nIf you want, you can restrict the search to a set of files with'
                                                 ' the filter.')
        label_filter_is = wx.StaticText(self, label='Filter is')
        self.label_filter_status = wx.StaticText(self, label='inactive')
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer.Add(label_introduction, 0, wx.ALL | wx.EXPAND, 3)
        header_sizer.AddStretchSpacer(1)
        header_sizer.Add(label_filter_is, 0,
                         wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_BOTTOM, 3)
        header_sizer.Add(self.label_filter_status, 0,
                         wx.ALL | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT, 3)
        self.Sizer.Add(header_sizer, 0, wx.ALL | wx.EXPAND, 3)

    def _build_filter(self):
        self._filter_pane = MyCollapsiblePane(self, label="Filter",
                                              style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        self._filter_input = wx.TextCtrl(self._filter_pane.GetPane(),
                                         size=(-1, 20))
        self._filter_regex_switch = wx.CheckBox(self._filter_pane.GetPane(),
                                                wx.ID_ANY, label="Use RegEx")
        self._filter_info = wx.StaticText(self._filter_pane.GetPane(),
                                          label='Here you can define one or more strings separated by comma (e.g. common,abc,123).\nThe filter matches if at least one string is part of the filename.\nIf you don\'t enter any strings, all opened files are included')
        filter_source_box = wx.StaticBox(self._filter_pane.GetPane(), label="Search")
        self._filter_source_testcases = wx.CheckBox(self._filter_pane.GetPane(),
                                                    wx.ID_ANY,
                                                    label="Test case files")
        self._filter_source_resources = wx.CheckBox(self._filter_pane.GetPane(),
                                                    wx.ID_ANY,
                                                    label="Resource files")
        self._filter_mode = wx.RadioBox(self._filter_pane.GetPane(),
                                        label="Mode",
                                        choices=["exclude", "include"])
        self._filter_test_button = wx.Button(self._filter_pane.GetPane(),
                                             wx.ID_INFO, label="Test the filter")
        filter_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filter_box_sizer.SetSizeHints(self._filter_pane.GetPane())
        filter_source_sizer = wx.StaticBoxSizer(filter_source_box, wx.VERTICAL)
        checkbox_border = 0 if IS_MAC else 3
        filter_source_sizer.Add(self._filter_source_testcases, 0, wx.ALL, checkbox_border)
        filter_source_sizer.Add(self._filter_source_resources, 0, wx.ALL, checkbox_border)
        filter_options = wx.BoxSizer(wx.VERTICAL)
        filter_options.Add(filter_source_sizer, 0,
                           wx.BOTTOM | wx.RIGHT | wx.LEFT | wx.EXPAND, 3)
        filter_options.Add(self._filter_mode, 0, wx.ALL | wx.EXPAND, 3)
        filter_input_sizer = wx.BoxSizer(wx.VERTICAL)
        filter_input_sizer.SetMinSize((600, -1))
        filter_input_sizer.Add(self._filter_info, 0, wx.ALL | wx.ALIGN_LEFT, 3)
        filter_input_sizer.Add(self._filter_input, 0, wx.ALL | wx.EXPAND, 3)
        filter_input_sizer.Add(self._filter_regex_switch, 0, wx.ALL | wx.ALIGN_RIGHT, 3)
        filter_input_sizer.Add(self._filter_test_button, 0, wx.ALL | wx.ALIGN_CENTER, 3)
        filter_box_sizer.Add(filter_options, 0, wx.ALL | wx.EXPAND, 3)
        filter_box_sizer.Add(filter_input_sizer, 0, wx.ALL | wx.EXPAND, 3)
        self._filter_pane.GetPane().SetSizer(filter_box_sizer)
        self.Sizer.Add(self._filter_pane, 0, wx.ALL | wx.EXPAND, 3)

    def _build_unused_keywords(self):
        panel_unused_kw = wx.Panel(self._notebook)
        sizer_unused_kw = wx.BoxSizer(wx.VERTICAL)
        panel_unused_kw.SetSizer(sizer_unused_kw)
        self._unused_kw_list = ResultListCtrl(panel_unused_kw,
                                              style=wx.LC_REPORT)
        self._unused_kw_list.InsertColumn(0, "Keyword", width=400)
        self._unused_kw_list.InsertColumn(1, "File", width=250)
        self._unused_kw_list.SetMinSize((650, 250))
        self._unused_kw_list.set_dialog(self)
        self._delete_button = wx.Button(panel_unused_kw, wx.ID_ANY,
                                        'Delete marked keywords')
        sizer_unused_kw.Add(self._unused_kw_list, 1, wx.ALL | wx.EXPAND, 3)
        unused_kw_controls = wx.BoxSizer(wx.HORIZONTAL)
        unused_kw_controls.AddStretchSpacer(1)
        unused_kw_controls.Add(self._delete_button, 0, wx.ALL | wx.ALIGN_RIGHT,
                               3)
        sizer_unused_kw.Add(unused_kw_controls, 0, wx.ALL | wx.EXPAND, 3)
        self._notebook.AddPage(panel_unused_kw, "Unused Keywords")

    def _build_controls(self):
        self._search_button = ButtonWithHandler(self, 'Search')
        self._abort_button = ButtonWithHandler(self, 'Abort')
        self._status_label = Label(self, label='')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._search_button, 0, wx.ALL, 3)
        controls.Add(self._abort_button, 0, wx.ALL, 3)
        controls.Add(self._status_label, 1, wx.ALL | wx.EXPAND, 3)
        self.Sizer.Add(controls, 0, wx.ALL | wx.EXPAND, 3)

    def _build_notebook(self):
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL | wx.EXPAND, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        self.Bind(wx.EVT_TEXT, self._update_filter, self._filter_input)
        self.Bind(wx.EVT_RADIOBOX, self._update_filter_mode, self._filter_mode)
        self.Bind(wx.EVT_CHECKBOX, self._update_filter_source_testcases, self._filter_source_testcases)
        self.Bind(wx.EVT_CHECKBOX, self._update_filter_source_resources, self._filter_source_resources)
        self.Bind(wx.EVT_BUTTON, self.OnDeletemarkedkeywords, self._delete_button)
        self.Bind(wx.EVT_BUTTON, self.OnShowfilestobesearched, self._filter_test_button)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultSelected, self._unused_kw_list)
        self.Bind(wx.EVT_CHECKBOX, self._update_filter_regex, self._filter_regex_switch)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._toggle_filter_active, self._filter_pane)

    def _set_default_values(self):
        check_testcases = True
        self._filter_source_testcases.SetValue(check_testcases)
        self._runner.set_filter_source_testcases(check_testcases)
        check_resources = True
        self._filter_source_resources.SetValue(check_resources)
        self._runner.set_filter_source_resources(check_resources)
        filter_mode = 0
        self._filter_mode.SetSelection(filter_mode)
        self._runner.set_filter_mode(filter_mode == 0)
        use_regex = False
        self._filter_regex_switch.SetValue(use_regex)
        self._runner.set_filter_use_regex(use_regex)
        filter_string = ''
        self._filter_input.ChangeValue(filter_string)
        self._runner.parse_filter_string(filter_string)
        self._disable_filter()
        self._abort_button.Disable()
        self._delete_button.Disable()

    def _update_filter(self, event):
        self._runner.parse_filter_string(event.GetString())

    def _update_filter_mode(self, event):
        self._runner.set_filter_mode(event.GetInt() == 0)

    def _update_filter_source_testcases(self, event):
        self._runner.set_filter_source_testcases(self._filter_source_testcases.IsChecked())

    def _update_filter_source_resources(self, event):
        self._runner.set_filter_source_resources(self._filter_source_resources.IsChecked())

    def _update_filter_regex(self, event):
        self._runner.set_filter_use_regex(self._filter_regex_switch.IsChecked())

    def _toggle_filter_active(self, event):
        if event.GetCollapsed():
            self._disable_filter()
        else:
            self._enable_filter()
        self._filter_pane.on_change(event)

    def _disable_filter(self):
        self._runner.set_filter_active(False)
        self.label_filter_status.SetLabel('inactive')
        self.label_filter_status.SetForegroundColour(wx.RED)

    def _enable_filter(self):
        self._runner.set_filter_active(True)
        self.label_filter_status.SetLabel('active')
        self.label_filter_status.SetForegroundColour((0,200,0))

    def OnSearch(self, event):
        self.begin_searching()
        self._runner._run_review()

    def OnAbort(self, event):
        self.end_searching()

    def OnDeletemarkedkeywords(self, event):
        item = self._unused_kw_list.get_next_checked_item()
        while item:
            index = item[0]
            kw = item[1]
            listitem = item[2]
            item_id = listitem.GetData()
            self._unused_kw_list.DeleteItem(index)
            self._unused_kw_list.RemoveClientData(item_id)
            kw.delete()
            self._update_notebook_text("Unused Keywords (%d)" % self._unused_kw_list.GetItemCount())
            self.update_status("")
            item = self._unused_kw_list.get_next_checked_item()
        self.item_in_kw_list_checked()

    def OnShowfilestobesearched(self, event):
        df_list = self._runner._get_datafile_list()
        if not df_list:
            string_list = "(None)"
        else:
            string_list = "\n".join(df.name for df in df_list)
        message = "Keywords of the following files will be included in the search:\n\n" + string_list
        wx.MessageDialog(self, message=message, caption="Included files", style=wx.OK|wx.ICON_INFORMATION).ShowModal()

    def OnResultSelected(self, event):
        self.frame.tree.select_node_by_data(self._unused_kw_list.GetClientData(event.GetData()))

    def item_in_kw_list_checked(self):
        if self._unused_kw_list.get_number_of_checked_items() > 0:
            self._delete_button.Enable()
        else:
            self._delete_button.Disable()

    def show_dialog(self):
        if not self.IsShown():
            self._clear_search_results()
            self.Show()
        self.Raise()

    def _close_dialog(self, event):
        if self._search_model.searching:
            self.end_searching()
        if event.CanVeto():
            self.Hide()
        else:
            self.Destroy()

    def begin_searching(self):
        self._abort_button.Enable()
        self._search_button.Disable()
        self._filter_pane.Disable()
        self._unused_kw_list.Disable()
        self._clear_search_results()
        self._dots = DottedSearch(self, self._update_unused_keywords)
        self._dots.start()

    def _clear_search_results(self):
        self._unused_kw_list.ClearAll()
        self._update_notebook_text('Unused Keywords')
        self._delete_button.Disable()
        self._status_label.SetLabel('')
        self._search_model.clear_search()

    def add_result_unused_keyword(self, index, keyword):
        keyword_info = keyword.info
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            self._unused_kw_list.InsertItem(index, keyword_info.name)
        else:
            self._unused_kw_list.InsertStringItem(index, keyword_info.name)
        filename = os.path.basename(keyword_info.item.source)
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            self._unused_kw_list.SetItem(index, 1, filename)
        else:
            self._unused_kw_list.SetStringItem(index, 1, filename)
        self._unused_kw_list.SetItemData(index, index)
        self._unused_kw_list.SetClientData(index, keyword)

    def _update_unused_keywords(self, dots):
        count_before = self._unused_kw_list.GetItemCount()
        for index, kw in list(enumerate(self._search_model.keywords))[count_before:]:
            self.add_result_unused_keyword(index, kw)
        self.update_status("Searching.%s \t- %s" % (dots, self._search_model.status))
        if not self._search_model.searching:
            self.end_searching()

    def _update_notebook_text(self, new_text):
        self._notebook.SetPageText(0, new_text)

    def update_status(self, message, increase=1):
        self._status_label.SetLabel(message)

    def end_searching(self):
        self._dots.stop()
        self._search_model.end_search()
        self._update_notebook_text('Unused Keywords (%d)' % (self._unused_kw_list.GetItemCount()))
        self.update_status("Search finished - Found %d Unused Keywords" % (self._unused_kw_list.GetItemCount()))
        self._unused_kw_list.Enable()
        self._abort_button.Disable()
        self._filter_pane.Enable()
        self._search_button.Enable()

    def send_radiobox_event(self, mycontrol):
        cmd = wx.CommandEvent(wx.EVT_RADIOBOX.evtType[0])
        cmd.SetEventObject(mycontrol)
        cmd.SetId(mycontrol.GetId())
        mycontrol.GetEventHandler().ProcessEvent(cmd)


class ReviewRunner(object):

    def __init__(self, controller, model):
        self._controller = controller
        self._model = model
        self._filter = ResultFilter()

    def set_filter_active(self, value):
        self._filter.active = value

    def set_filter_mode(self, exclude):
        self._filter.excludes = exclude

    def set_filter_source_testcases(self, value):
        self._filter.check_testcases = value

    def set_filter_source_resources(self, value):
        self._filter.check_resources = value

    def set_filter_use_regex(self, value):
        self._filter.use_regex = value

    def parse_filter_string(self, filter_string):
        self._filter.set_strings(filter_string.split(','))

    def _get_datafile_list(self):
        return [df for df in self._controller.datafiles if self._filter.include_file(df)]

    def _run_review(self):
        self._model.begin_search()
        Thread(target=self._run).start()

    def _run(self):
        self._stop_requested = False
        self._model.status = 'listing datafiles'
        for df in self._get_datafile_list():
            libname = os.path.basename(df.source).rsplit('.', 1)[0]
            self._model.status = 'searching from '+libname
            for keyword in df.keywords:
                time.sleep(0) # GIVE SPACE TO OTHER THREADS -- Thread.yield in Java
                self._model.status = "%s.%s" % (libname, keyword.name)
                if not self._model.searching:
                    break
                # Check if it is unused
                if not isinstance(keyword, LibraryKeywordInfo) and keyword.name:
                    if self._is_unused(keyword):
                        self._model.add_unused_keyword(keyword)
            if not self._model.searching:
                break
        self._model.end_search()

    def _is_unused(self, keyword):
        try:
            next(self._controller.execute(FindUsages(keyword.name, keyword_info=keyword.info)))
            return False
        except StopIteration:
            return True


class ResultFilter(object):

    def __init__(self):
        self._strings = []
        self.excludes = True
        self.check_testcases = True
        self.check_resources = True
        self.use_regex = False
        self.active = False

    def set_strings(self, strings):
        self._strings = [s.strip() for s in strings if s.strip()]

    def include_file(self, datafile):
        if isinstance(datafile, TestDataDirectoryController):
            return False
        if not self.active:
            return True
        if not self.check_testcases and isinstance(datafile, TestCaseFileController):
            return False
        if not self.check_resources and isinstance(datafile, ResourceFileController):
            return False
        if not self._strings:
            return True
        return self.excludes ^ any(self._results(datafile.name))

    def _results(self, name):
        for string in self._strings:
            if self.use_regex:
                yield bool(re.match(string, name))
            else:
                yield string in name


class ResultModel(object):

    def __init__(self):
        self.clear_search()

    def clear_search(self):
        self.status = ''
        self.keywords = []
        self.searching = False

    def add_unused_keyword(self, keyword):
        self.keywords += [keyword]

    def begin_search(self):
        self.searching = True

    def end_search(self):
        self.searching = False


class ResultListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, style):
        self.parent = parent
        wx.ListCtrl.__init__(self, parent=parent, style=style)
        listmix.CheckListCtrlMixin.__init__(self)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(2)
        self._clientData = {}

    def set_dialog(self, dialog):
        self._dlg = dialog

    def OnCheckItem(self, index, flag):
        if self._dlg:
            self._dlg.item_in_kw_list_checked()
        else:
            print("No dialog set")

    def get_next_checked_item(self):
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                item = self.GetItem(i)
                return ([i, self.GetClientData(item.GetData()), item])
        return None

    def get_number_of_checked_items(self):
        sum = 0
        for i in range(self.GetItemCount()):
            if self.IsChecked(i):
                sum += 1
        return sum

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
        print(self._clientData)

class MyCollapsiblePane(wx.CollapsiblePane):

    def __init__(self, parent, *args, **kwargs):
        wx.CollapsiblePane.__init__(self, parent, *args, **kwargs)
        self.Bind(wx.EVT_SIZE, self._recalc_size)

    def _recalc_size(self, event=None):
        if self.IsExpanded():
            expand_button_height = 32  # good guess...
            height = 150 if IS_MAC else 135
            self.SetSizeHints(650, height + expand_button_height)
        if self.IsCollapsed():
            self.SetSizeHints(650, 40)
        if event:
            event.Skip()

    def on_change(self, event):
        self.GetParent().Layout()
