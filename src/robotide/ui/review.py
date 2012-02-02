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

class ReviewDialog(wx.Frame):

    headers = ['col1', 'col2', 'col3']
    _filter_strings = []

    def __init__(self, controller, parent):
        wx.Frame.__init__(self, parent, title="Review Test Data", style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        self._controller = controller
        self._build_ui()
        self.CenterOnParent()

    def _build_ui(self):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
        self._filter_input = wx.TextCtrl(self)
        self._filter_test_button = ButtonWithHandler(self, 'Show used files')
        line1 = wx.BoxSizer(wx.HORIZONTAL)
        line1.Add(Label(self, label='Exclusion filter: '), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 3)
        line1.Add(self._filter_input, 1, wx.ALL|wx.EXPAND, 3)
        line1.Add(self._filter_test_button, 0, wx.ALL, 3)
        line2 = wx.BoxSizer(wx.HORIZONTAL)
        line2.Add(wx.StaticText(self, label='To skip specific files during the search, you can define comma-separated character sequences that must not be part of the searched files\' name (e.g. common,abc,123)', size=(-1, 40)), 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 3)
        self.Sizer.Add(line1, 0, wx.ALL|wx.EXPAND, 3)
        self.Sizer.Add(line2, 0, wx.ALL|wx.EXPAND, 3)
        
#        style = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL
        style = wx.LB_MULTIPLE
        self._list = wx.ListBox(self, style=style)
#        for col, title in enumerate(self.headers):
#            self._list.InsertColumn(col, title)
#        self._list.SetColumnWidth(0, 250)
        self.Sizer.Add(self._list, 1, wx.ALL|wx.EXPAND | wx.ALL, 3)
        
        self._search_button = ButtonWithHandler(self, 'Search')
        self.Sizer.Add(self._search_button, 0, wx.ALL, 3)
        
        self.SetSize((700,500))

    def OnSearch(self, event):
        self._search_button.Disable()
        self._filter_test_button.Disable()
        resultlist = self._get_unused_keywords()
        self._list.InsertItems(resultlist, 0)
        self._search_button.Enable()
        self._filter_test_button.Enable()

    def OnShowusedfiles(self, event):
        message = "Keywords of the following files will be included in the search:" + "\n".join([df.name for df in self._get_datafile_list()])
        wx.MessageDialog(self, message=message, caption="Included files", style=wx.OK).ShowModal()

    def _get_datafile_list(self):
        self._parse_filter_string()
        return [df for df in self._controller.datafiles if self._include_file(df)]

    def _include_file(self, datafile):
        if isinstance(datafile, DirectoryController):
            return False
        for string in self._filter_strings:
            if string == '':
                continue
            if string in datafile.name:
                return False
        return True

    def _parse_filter_string(self):
        self._filter_strings = self._filter_input.GetValue().split(',')
        print "Filterstring: ", self._filter_strings

    def _get_unused_keywords(self):
        resultlist = []
        namespace = self._controller._namespace
        for keyword_info in namespace.get_all_keywords([df.data for df in self._get_datafile_list()]):
            if not isinstance(keyword_info, LibraryKeywordInfo) and keyword_info.name:
                try:
                    self._controller.execute(FindUsages(keyword_info.name, keyword_info=keyword_info)).next()
                except StopIteration:
#                    print 'Source: %s Keyword: "%s"' % (keyword_info.item.source, keyword_info.name)
                    resultlist.append("%s - %s" % (keyword_info.item.source.rsplit('/', 1)[1], keyword_info.name))
        return resultlist

    def show_it(self):
        self._show()

    def _show(self):
        if not self.IsShown():
            self.Show()
        self.Raise()