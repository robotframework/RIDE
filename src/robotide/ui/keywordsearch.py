#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from robotide.pluginapi import Plugin, ActionInfo
from robotide import utils


class KeywordSearch(Plugin):

    def __init__(self, app):
        Plugin.__init__(self, app)
        self.all_keywords = self.model and self.model.get_all_keywords() or []
        self.keywords = self.all_keywords

    def enable(self):
        action = ActionInfo('Tools', 'Search Keywords', self.OnSearch,
                            doc='Search keywords from libraries and resources')
        self.register_action(action)
        self.refresh()
        self._dialog = KeywordSearchDialog(self.frame, self)

    def OnSearch(self, event):
        # TODO: dirty hack
        if not self.all_keywords:
            self.refresh()
        if not self._dialog.IsShown():
            self._dialog.Show()

    def refresh(self):
        self.keywords = self.all_keywords = self.model and self.model.get_all_keywords() or []

    def search(self, pattern, search_docs):
        self.keywords = [ kw for kw in self.all_keywords if \
                          self._matches_criteria(kw, pattern, search_docs) ]
        return self.keywords

    def get_documentation(self, index):
        return self.keywords[index].get_details()

    def _matches_criteria(self, kw, pattern, search_docs):
        if utils.contains(kw.name, pattern, ignore=['_']):
            return True
        return search_docs and utils.contains(kw.doc, pattern)


class KeywordSearchDialog(wx.Frame):

    def __init__(self, parent, searcher):
        wx.Frame.__init__(self, parent, title="Search Keywords")
        self._searcher = searcher
        self._create_components(searcher)
        self._make_bindings()

    def _create_components(self, searcher):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._add_search_control('Filter Names: ')
        self._list = _KeywordList(self, searcher)
        self._list.SetSize(self.Size)
        self.Sizer.Add(self._list, 1, wx.EXPAND| wx.ALL, 3)
        self._details = utils.RideHtmlWindow(self)
        self.Sizer.Add(self._details, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSize((700,500))

    def _add_search_control(self, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=label))
        self._search_control = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        sizer.Add(self._search_control)
        self._use_doc = wx.CheckBox(self, label='Search Documentation')
        self._use_doc.SetValue(True)
        sizer.Add(self._use_doc)
        self.Sizer.Add(sizer, 0, wx.ALL, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self._list)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self._search_control)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self._search_control)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHECKBOX, self.OnSearch, self._use_doc)

    def OnClose(self, event):
        self.Hide()

    def OnSearch(self, event):
        pattern= self._search_control.GetValue().lower()
        use_doc = self._use_doc.GetValue()
        self._list.filter_and_show_keywords(pattern, use_doc)
        self._details.clear()

    def OnActivate(self, event):
        self.OnSearch(event)

    def OnItemSelected(self, event):
        doc = self.keyword_searcher.get_documentation(event.GetIndex())
        self._details.SetPage(doc)


class _KeywordList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, searcher):
        wx.ListCtrl.__init__(self, parent, 
                             style=wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|
                                   wx.LC_HRULES|wx.LC_VIRTUAL)
        ListCtrlAutoWidthMixin.__init__(self)
        self._create_headers()
        self._searcher = searcher
        self.filter_and_show_keywords('', True)
        self._previous_search_term = None

    def _create_headers(self):
        for col, title in enumerate(['Keyword', 'Source', 'Description']):
            self.InsertColumn(col, title)
        self.SetColumnWidth(0, 250)

    def filter_and_show_keywords(self, pattern, use_doc):
        self._keywords = self._searcher.search(pattern, use_doc)
        self.SetItemCount(len(self._keywords))

    def OnGetItemText(self, row, col):
        kw = self._keywords[row]
        if col == 0:
            return kw.name
        elif col == 1:
            return kw.source
        return kw.shortdoc
