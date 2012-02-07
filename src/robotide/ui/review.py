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

import wx
from robotide.widgets import ButtonWithHandler, Label
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.usages.commands import FindUsages
from robotide.controller.filecontrollers import DirectoryController
from threading import Thread

class ReviewDialog(wx.Frame):

    def __init__(self, controller, parent):
        wx.Frame.__init__(self, parent, title="Review Test Data", style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        self.index = 0
        self._runner = ReviewRunner(controller, self)
        self._build_ui()
        self._make_bindings()
        self._set_default_values()
        self.CenterOnParent()

    def _build_ui(self):
        
        # General
        self.SetSize((700,500))
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
        # Filter
        self._filter_box = wx.StaticBox(self, label="Filter")
        self._filter_input = wx.TextCtrl(self, size=(-1, 20))
        self._filter_info = wx.StaticText(self, label='Here you can define comma-separated character sequences that must (not) be part of the files\' name (e.g. common,abc,123)', size=(-1, 40))
        self._filter_mode = wx.RadioBox(self, label="Mode", choices=["exclude", "include"])
        self._filter_bool = wx.RadioBox(self, label="Bool", choices=["AND", "OR"])
        self._filter_test_button = ButtonWithHandler(self, 'Show files to be searched')
        filter_box_sizer = wx.StaticBoxSizer(self._filter_box, wx.VERTICAL)
        filter_box_sizer.Add(self._filter_input, 0, wx.ALL|wx.EXPAND, 3)
        filter_box_sizer.Add(self._filter_info, 0, wx.ALL|wx.EXPAND, 3)
        filter_options = wx.BoxSizer(wx.HORIZONTAL)
        filter_options.Add(self._filter_mode, 0, wx.ALL, 3)
        filter_options.Add(self._filter_bool, 0, wx.ALL, 3)
        filter_options.AddStretchSpacer(1)
        filter_options.Add(self._filter_test_button, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT, 3)
        filter_box_sizer.Add(filter_options, 0, wx.ALL|wx.EXPAND, 3)
        self.Sizer.Add(filter_box_sizer, 0, wx.ALL|wx.EXPAND, 3)
        
        # Unused Keywords
        self._list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self._list.InsertColumn(0, "Keyword", width=250)
        self._list.InsertColumn(1, "File", width=250)
        self.Sizer.Add(self._list, 1, wx.ALL|wx.EXPAND | wx.ALL, 3)
        
        # Controls
        self._search_button = ButtonWithHandler(self, 'Search')
        self._abort_button = ButtonWithHandler(self, 'Abort')
        self._status_label = Label(self, label='')
        controls = wx.BoxSizer(wx.HORIZONTAL)
        controls.Add(self._search_button, 0, wx.ALL, 3)
        controls.Add(self._abort_button, 0, wx.ALL, 3)
        controls.Add(self._status_label, 1, wx.ALL|wx.EXPAND, 3)
        self.Sizer.Add(controls, 0, wx.ALL, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_CLOSE, self._close_dialog)
        self.Bind(wx.EVT_TEXT, self._update_filter, self._filter_input)
        self.Bind(wx.EVT_RADIOBOX, self._update_filter_mode, self._filter_mode)
        self.Bind(wx.EVT_RADIOBOX, self._update_filter_bool, self._filter_bool)

    def _set_default_values(self):
        self._filter_mode.SetSelection(0)
        self._runner.set_filter_mode(True)
        self._filter_bool.SetSelection(1)
        self._runner.set_filter_bool(False)
        self._abort_button.Disable()

    def _update_filter(self, event):
        self._runner._parse_filter_string(self._filter_input.GetValue())

    def _update_filter_mode(self, event):
        self._runner.set_filter_mode(event.GetInt() == 0)

    def _update_filter_bool(self, event):
        self._runner.set_filter_bool(event.GetInt() == 0)

    def OnSearch(self, event):
        self._runner._search_unused_keywords()

    def OnAbort(self, event):
        self._runner.request_stop()

    def OnShowfilestobesearched(self, event):
        message = "Keywords of the following files will be included in the search:\n\n" + "\n".join([df.name for df in self._runner._get_datafile_list()])
        wx.MessageDialog(self, message=message, caption="Included files", style=wx.OK).ShowModal()

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
        self._list.DeleteAllItems()

    def add_result(self, keyword_info):
        self._list.InsertStringItem(self.index, keyword_info.name)
        self._list.SetStringItem(self.index, 1, keyword_info.item.source.rsplit('/', 1)[1])
        self.index += 1

    def update_status(self, message, increase=1):
        self._status_label.SetLabel(message)

    def end_searching(self):
        self.update_status("")
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
        self._filter_uses_and = True
        self._results_unused_keywords = []

    def set_filter_mode(self, exclude):
        self._filter_excludes = exclude

    def set_filter_bool(self, value):
        self._filter_uses_and = value

    def _get_datafile_list(self):
        list = [df for df in self._controller.datafiles if self._include_file(df)]
        return list

    def _include_file(self, datafile):
        if isinstance(datafile, DirectoryController):
            return False
        if len(self._filter_strings) == 0:
            return True
        results = []
        for string in self._filter_strings:
            if string == '':
                continue
            results.append(string in datafile.name)
        
        if self._filter_excludes and self._filter_uses_and:
            overall_result = False in results
        elif self._filter_excludes and not self._filter_uses_and:
            overall_result = True not in results
        elif not self._filter_excludes and self._filter_uses_and:
            overall_result = False not in results
        elif not self._filter_excludes and not self._filter_uses_and:
            overall_result = True in results
        
        return overall_result

    def _parse_filter_string(self, filter_string):
        self._filter_strings = filter_string.split(',')

    def _search_unused_keywords(self):
        worker = Thread(target=self._run)
        worker.start()

    def _run(self):
        self._stop_requested = False
        self._dlg.begin_searching()
        for df in self._get_datafile_list():
            for keyword in df.keywords:
                keyword_info = keyword.info
                self._dlg.update_status("Checking %s" % keyword_info.name)
                if self._stop_requested  == True:
                    break
                if not isinstance(keyword_info, LibraryKeywordInfo) and keyword_info.name:
                    try:
                        self._controller.execute(FindUsages(keyword_info.name, keyword_info=keyword_info)).next()
                    except StopIteration:
                        self._dlg.add_result(keyword_info)
            if self._stop_requested == True:
                break
        self._dlg.end_searching()

    def request_stop(self):
        self._stop_requested = True
