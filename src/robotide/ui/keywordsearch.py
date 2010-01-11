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

from robotide.pluginapi import Plugin, ActionInfo, RideOpenSuite,\
    RideOpenResource, RideImportSetting, RideUserKeyword
from robotide import utils


class KeywordSearch(Plugin):

    def __init__(self, app):
        Plugin.__init__(self, app)
        self._all_keywords = []
        self._criteria = _SearchCriteria()

    def enable(self):
        action = ActionInfo('Tools', 'Search Keywords', self.OnSearch,
                            doc='Search keywords from libraries and resources')
        self.register_action(action)
        self.subscribe(self.refresh, RideOpenSuite, RideOpenResource,
                       RideImportSetting, RideUserKeyword)
        self._dialog = KeywordSearchDialog(self.frame, self)

    def OnSearch(self, event):
        if not self._dialog.IsShown():
            self._dialog.Show()

    def refresh(self, message):
        self._all_keywords = self.model.get_all_keywords()

    def search(self, pattern, search_docs):
        self._criteria = _SearchCriteria(pattern, search_docs)
        return self._search()

    def _search(self):
        return [ kw for kw in self._all_keywords if self._criteria.matches(kw) ]


class _SearchCriteria(object):

    def __init__(self, pattern='', search_docs=True):
        self._pattern = pattern
        self._search_docs = search_docs

    def matches(self, kw):
        if utils.contains(kw.name, self._pattern, ignore=['_']):
            return True
        return self._search_docs and utils.contains(kw.doc, self._pattern)


class KeywordSearchDialog(wx.Frame):

    def __init__(self, parent, searcher):
        wx.Frame.__init__(self, parent, title="Search Keywords")
        self._searcher = searcher
        self._create_components(searcher)
        self._make_bindings()

    def _create_components(self, searcher):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._add_search_control('Filter Names: ')
        self._list = _KeywordList(self)
        self._list.SetSize(self.Size)
        self.Sizer.Add(self._list, 1, wx.EXPAND| wx.ALL, 3)
        self._details = utils.RideHtmlWindow(self)
        self.Sizer.Add(self._details, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSize((700,500))

    def _add_search_control(self, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=label))
        self._search_control = wx.SearchCtrl(self, size=(200,-1),
                                             style=wx.TE_PROCESS_ENTER)
        sizer.Add(self._search_control)
        self._use_doc = wx.CheckBox(self, label='Search Documentation')
        self._use_doc.SetValue(True)
        sizer.Add(self._use_doc)
        self.Sizer.Add(sizer, 0, wx.ALL, 3)

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self._list)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch,
                  self._search_control)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self._search_control)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHECKBOX, self.OnSearch, self._use_doc)

    def OnActivate(self, event):
        self.OnSearch(event)

    def OnSearch(self, event):
        self._keywords = self._searcher.search(*self._get_search_criteria())
        self._list.show_keywords(self._keywords)
        self._details.clear()

    def _get_search_criteria(self):
        return self._search_control.GetValue().lower(), self._use_doc.GetValue()

    def OnItemSelected(self, event):
        self._details.SetPage(self._keywords[event.Index].get_details())

    def OnClose(self, event):
        self.Hide()


class _KeywordList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent):
        style = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._create_headers()

    def _create_headers(self):
        for col, title in enumerate(['Keyword', 'Source', 'Description']):
            self.InsertColumn(col, title)
        self.SetColumnWidth(0, 250)

    def show_keywords(self, keywords):
        self._keywords = keywords
        self.SetItemCount(len(self._keywords))

    def OnGetItemText(self, row, col):
        kw = self._keywords[row]
        return [kw.name, kw.source, kw.shortdoc][col]
