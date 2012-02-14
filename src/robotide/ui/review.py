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

import os
import wx
import wx.lib.mixins.listctrl as listmix
import time
import re
from robotide.context import SETTINGS
from robotide.widgets import ButtonWithHandler, Label
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.usages.commands import FindUsages
from robotide.controller.filecontrollers import DirectoryController, TestCaseFileController, ResourceFileController
from threading import Thread

class ReviewDialog(wx.Frame):

    def __init__(self, controller, frame):
        wx.Frame.__init__(self, frame, title="Review Test Data", style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        self.index = 0
        self.frame = frame
        self._runner = ReviewRunner(controller, self)
        self._build_ui()
        self._make_bindings()
        self._set_default_values()
        self.CenterOnParent()

    def _build_ui(self):
        
        # General
        self.SetSize((700,600))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
        # Filter
        self._filter_box = wx.StaticBox(self, label="Filter")
        self._filter_input = wx.TextCtrl(self, size=(-1, 20))
        self._filter_regex_switch = wx.CheckBox (self, wx.ID_ANY, label="Use RegEx")
        self._filter_info = wx.StaticText(self, label='Here you can define one or more strings separated by comma (e.g. common,abc,123). The filter matches if at least one string is part of the filename.\nIf you don\'t enter any strings, all opened files are included', size=(-1, 80))
        self._filter_source_box = wx.StaticBox(self, label="Search")
        self._filter_source_testcases = wx.CheckBox(self, wx.ID_ANY, label="Test cases")
        self._filter_source_resources = wx.CheckBox(self, wx.ID_ANY, label="Resources")
        self._filter_mode = wx.RadioBox(self, label="Mode", choices=["exclude", "include"])
        self._filter_test_button = ButtonWithHandler(self, 'Show files to be searched')
        filter_box_sizer = wx.StaticBoxSizer(self._filter_box, wx.HORIZONTAL)
        filter_source_sizer = wx.StaticBoxSizer(self._filter_source_box, wx.VERTICAL)
        filter_source_sizer.Add(self._filter_source_testcases, 0, wx.ALL, 0)
        filter_source_sizer.Add(self._filter_source_resources, 0, wx.ALL, 0)
        filter_options = wx.BoxSizer(wx.VERTICAL)
        filter_options.Add(filter_source_sizer, 0, wx.BOTTOM|wx.RIGHT|wx.LEFT|wx.EXPAND, 3)
        filter_options.Add(self._filter_mode, 0, wx.ALL|wx.EXPAND, 3)
        filter_input_sizer = wx.BoxSizer(wx.VERTICAL)
        filter_input_sizer.AddSpacer(10)
        filter_input_sizer.Add(self._filter_input, 0, wx.ALL|wx.EXPAND, 3)
        filter_input_sizer.Add(self._filter_regex_switch, 0, wx.ALL|wx.ALIGN_RIGHT, 3)
        filter_input_sizer.Add(self._filter_info, 0, wx.ALL|wx.EXPAND, 3)
        filter_input_sizer.AddStretchSpacer(1)
        filter_controls = wx.BoxSizer(wx.HORIZONTAL)
        filter_controls.AddStretchSpacer(1)
        filter_controls.Add(self._filter_test_button, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT, 3)
        filter_input_sizer.Add(filter_controls, 0, wx.ALL|wx.EXPAND, 3)
        filter_box_sizer.Add(filter_options, 0, wx.ALL|wx.EXPAND, 3)
        filter_box_sizer.Add(filter_input_sizer, 1, wx.ALL|wx.EXPAND, 3)
        self.Sizer.Add(filter_box_sizer, 0, wx.ALL|wx.EXPAND, 3)
        
        # Notebook
        self._notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        self.Sizer.Add(self._notebook, 1, wx.ALL|wx.EXPAND, 3)
        
        # Unused Keywords
        panel_unused_kw = wx.Panel(self._notebook)
        sizer_unused_kw = wx.BoxSizer(wx.VERTICAL)
        panel_unused_kw.SetSizer(sizer_unused_kw)
        self._unused_kw_list = ResultListCtrl(panel_unused_kw, style=wx.LC_REPORT)
        self._unused_kw_list.InsertColumn(0, "Keyword", width=400)
        self._unused_kw_list.InsertColumn(1, "File", width=250)
        self._unused_kw_list.set_dialog(self)
        self._delete_button = wx.Button(panel_unused_kw, wx.ID_ANY, 'Delete marked keywords')
        sizer_unused_kw.Add(self._unused_kw_list, 1, wx.ALL|wx.EXPAND | wx.ALL, 3)
        unused_kw_controls = wx.BoxSizer(wx.HORIZONTAL)
        unused_kw_controls.AddStretchSpacer(1)
        unused_kw_controls.Add(self._delete_button, 0, wx.ALL|wx.ALIGN_RIGHT, 3)
        sizer_unused_kw.Add(unused_kw_controls, 0, wx.ALL|wx.EXPAND, 3)
        self._notebook.AddPage(panel_unused_kw, "Unused Keywords")
        
        # Controls
        self._search_button = ButtonWithHandler(self, 'Search')
        self._abort_button = ButtonWithHandler(self, 'Abort')
        self._status_label = Label(self, label='')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._search_button, 0, wx.ALL, 3)
        controls.Add(self._abort_button, 0, wx.ALL, 3)
        controls.Add(self._status_label, 1, wx.ALL|wx.EXPAND, 3)
        self.Sizer.Add(controls, 0, wx.ALL|wx.EXPAND, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        self.Bind(wx.EVT_TEXT, self._update_filter, self._filter_input)
        self.Bind(wx.EVT_RADIOBOX, self._update_filter_mode, self._filter_mode)
        self.Bind(wx.EVT_CHECKBOX, self._update_filter_source_testcases, self._filter_source_testcases)
        self.Bind(wx.EVT_CHECKBOX, self._update_filter_source_resources, self._filter_source_resources)
        self.Bind(wx.EVT_BUTTON, self.OnDeletemarkedkeywords, self._delete_button)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultSelected, self._unused_kw_list)
        self.Bind(wx.EVT_CHECKBOX, self._upate_filter_regex, self._filter_regex_switch)

    def _set_default_values(self):
        check_testcases = SETTINGS.get('review_check_testcases', True)
        self._filter_source_testcases.SetValue(check_testcases)
        self._runner.set_filter_source_testcases(check_testcases)
        check_resources = SETTINGS.get('review_check_resources', True)
        self._filter_source_resources.SetValue(check_resources)
        self._runner.set_filter_source_resources(check_resources)
        filter_mode = SETTINGS.get('review_filter_mode', 0)
        self._filter_mode.SetSelection(filter_mode)
        self._runner.set_filter_mode(filter_mode == 0)
        use_regex = SETTINGS.get('review_use_regex', False)
        self._filter_regex_switch.SetValue(use_regex)
        self._runner.set_filter_use_regex(use_regex)
        filter_string = SETTINGS.get('review_filter_string', '')
        self._filter_input.ChangeValue(filter_string)
        self._runner.parse_filter_string(filter_string)
        self._abort_button.Disable()
        self._delete_button.Disable()

    def _update_filter(self, event):
        self._runner.parse_filter_string(event.GetString())
        SETTINGS.set('review_filter_string', event.GetString())

    def _update_filter_mode(self, event):
        self._runner.set_filter_mode(event.GetInt() == 0)
        SETTINGS.set('review_filter_mode', event.GetInt())

    def _update_filter_source_testcases(self, event):
        self._runner.set_filter_source_testcases(event.Checked())
        SETTINGS.set('review_check_testcases', event.Checked())

    def _update_filter_source_resources(self, event):
        self._runner.set_filter_source_resources(event.Checked())
        SETTINGS.set('review_check_resources', event.Checked())

    def _upate_filter_regex(self, event):
        self._runner.set_filter_use_regex(event.Checked())
        SETTINGS.set('review_use_regex', event.Checked())

    def OnSearch(self, event):
        self._runner._run_review()

    def OnAbort(self, event):
        self._runner.request_stop()

    def OnDeletemarkedkeywords(self, event):
        item = self._unused_kw_list.get_next_checked_item()
        while(item):
            index = item[0]
            kw = item[1]
            listitem = item[2]
            item_id = listitem.GetData()
            self._unused_kw_list.DeleteItem(index)
            self._unused_kw_list.RemoveClientData(item_id)
            kw.delete()
            self._notebook.SetPageText(0, "Unused keywords (%d)" % self._unused_kw_list.GetItemCount())
            item = self._unused_kw_list.get_next_checked_item()

    def OnShowfilestobesearched(self, event):
        df_list = self._runner._get_datafile_list()
        if len(df_list) == 0:
            string_list = "(None)"
        else:
            string_list = "\n".join([df.name for df in df_list])
        message = "Keywords of the following files will be included in the search:\n\n" + string_list
        wx.MessageDialog(self, message=message, caption="Included files", style=wx.OK).ShowModal()

    def OnResultSelected(self, event):
        self.frame.tree.select_node_by_data(self._unused_kw_list.GetClientData(event.GetData()))

    def item_in_kw_list_checked(self):
        if self._unused_kw_list.get_number_of_checked_items() > 0:
            self._delete_button.Enable()
        else:
            self._delete_button.Disable()

    def show_dialog(self):
        if not self.IsShown():
            self.Show()
        self.Raise()

    def _close_dialog(self, event):
        if event.CanVeto():
            self.Hide()
        else:
            self.Destroy()

    def begin_searching(self):
        self._abort_button.Enable()
        self._search_button.Disable()
        self._filter_input.Disable()
        self._filter_test_button.Disable()
        self._unused_kw_list.Disable()
        self._unused_kw_list.ClearAll()
        self.index = 0

    def add_result_unused_keyword(self, keyword):
        keyword_info = keyword.info
        self._unused_kw_list.InsertStringItem(self.index, keyword_info.name)
        filename = os.path.basename(keyword_info.item.source)
        self._unused_kw_list.SetStringItem(self.index, 1, filename)
        self._unused_kw_list.SetItemData(self.index, self.index)
        self._unused_kw_list.SetClientData(self.index, keyword)
        self._notebook.SetPageText(0, "Unused keywords (%d)" % self._unused_kw_list.GetItemCount())
        self.index += 1

    def update_status(self, message, increase=1):
        self._status_label.SetLabel(message)

    def end_searching(self):
        self.update_status("")
        self._unused_kw_list.Enable()
        self._abort_button.Disable()
        self._filter_input.Enable()
        self._filter_test_button.Enable()
        self._search_button.Enable()

    def send_radiobox_event(self, mycontrol):
        cmd = wx.CommandEvent(wx.EVT_RADIOBOX.evtType[0])
        cmd.SetEventObject(mycontrol)
        cmd.SetId(mycontrol.GetId())
        mycontrol.GetEventHandler().ProcessEvent(cmd)


class ReviewRunner():

    def __init__(self, controller, dialog):
        self._controller = controller
        self._dlg = dialog
        self._filter_strings = []
        self._filter_excludes = True
        self._filter_check_testcases = True
        self._filter_check_resources = True
        self._filter_use_regex = False
        self._results_unused_keywords = []

    def set_filter_mode(self, exclude):
        self._filter_excludes = exclude

    def set_filter_source_testcases(self, value):
        self._filter_check_testcases = value

    def set_filter_source_resources(self, value):
        self._filter_check_resources = value

    def set_filter_use_regex(self, value):
        self._filter_use_regex = value

    def _get_datafile_list(self):
        return [df for df in self._controller.datafiles if self._include_file(df)]

    def _include_file(self, datafile):
        if isinstance(datafile, DirectoryController):
            return False
        
        if not self._filter_check_testcases and isinstance(datafile, TestCaseFileController):
            return False
        
        if not self._filter_check_resources and isinstance(datafile, ResourceFileController):
            return False
        
        if len(self._filter_strings) == 0:
            return True
        
        results = []
        for string in self._filter_strings:
            if string == '':
                continue
            if self._filter_use_regex:
                results.append(not re.match(string, datafile.name) == None)
            else:
                results.append(string in datafile.name)
        
        if len(results) == 0:
            return True
        
        found = True in results
        return self._filter_excludes ^ found

    def parse_filter_string(self, filter_string):
        self._filter_strings = filter_string.split(',')

    def _run_review(self):
        worker = Thread(target=self._run)
        worker.start()

    def _run(self):
        self._stop_requested = False
        wx.CallAfter(self._dlg.begin_searching)
        for df in self._get_datafile_list():
            libname = os.path.basename(df.source).rsplit('.', 1)[0]
            for keyword in df.keywords:
                time.sleep(0) # GIVE SPACE TO OTHER THREADS -- Thread.yield in Java
                wx.CallAfter(self._dlg.update_status, "%s.%s" % (libname, keyword.name))
                if self._stop_requested == True:
                    break
                
                # Check if it is unused
                if not isinstance(keyword, LibraryKeywordInfo) and keyword.name:
                    try:
                        self._controller.execute(FindUsages(keyword.name, keyword_info=keyword.info)).next()
                    except StopIteration:
                        wx.CallAfter(self._dlg.add_result_unused_keyword, keyword)
                
            if self._stop_requested == True:
                break
        wx.CallAfter(self._dlg.end_searching)

    def request_stop(self):
        self._stop_requested = True


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
            print "No dialog set"

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
        print self._clientData
