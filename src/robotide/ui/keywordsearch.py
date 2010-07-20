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
    """A plugin for searching keywords based on name or documentation."""

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
        if self._contains(kw.name, self._pattern):
            return True
        return self._search_docs and self._contains(kw.doc, self._pattern)

    def _contains(self, string, pattern):
        return utils.normalize(pattern) in utils.normalize(string)


class KeywordSearchDialog(wx.Frame):

    def __init__(self, parent, searcher):
        wx.Frame.__init__(self, parent, title="Search Keywords")
        self._searcher = searcher
        self._create_components(searcher)
        self._make_bindings()
        self._sort_up = True
        self._sortcol = 0
        self.SetBackgroundColour(wx.NullColour)

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
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

    def OnColClick(self,event):
        col = event.GetColumn()
        if self._is_not_kw_or_source_col(col):
            event.Skip()
            return
        if self._col_already_selected(col):
            self._swap_sort_direction()
        else:
            self._set_sort_up()
        self._sortcol = col
        self.OnSearch(event)
        event.Skip()

    def _is_not_kw_or_source_col(self, col):
        return col >= 2

    def _col_already_selected(self, col):
        return col == self._sortcol

    def _swap_sort_direction(self):
        self._sort_up = not self._sort_up

    def _set_sort_up(self):
        self._sort_up = True

    def OnActivate(self, event):
        self.OnSearch(event)

    def OnSearch(self, event):
        self._keywords = _KeywordData(self._searcher.search(*self._get_search_criteria()),
                                      self._sortcol, self._sort_up)
        self._list.show_keywords(self._keywords)
        self._details.clear()
        self.Refresh()

    def _get_search_criteria(self):
        return self._search_control.GetValue().lower(), self._use_doc.GetValue()

    def OnItemSelected(self, event):
        self._details.SetPage(self._keywords[event.Index].details)

    def OnClose(self, event):
        self.Hide()


class _KeywordData(list):
    headers = ['Name', 'Source', 'Description']

    def __init__(self, keywords, sort_col=0, sort_up=True):
        for kw in self._sort(keywords, sort_col, sort_up):
            self.append(kw)

    def _sort(self, keywords, sort_col, sort_up):
        return self._sort_by_attr(keywords, self.headers[sort_col].lower(),
                                  sort_up)

    def _sort_by_attr(self, keywords, attr_name, sort_up):
        return sorted(keywords, cmp=self._get_comparator_for(attr_name),
                      reverse=not sort_up)

    def _get_comparator_for(self, atrr_name):
        return lambda kw, kw2: cmp(self._value_lowerer(kw, atrr_name),
                                   self._value_lowerer(kw2, atrr_name))

    def _value_lowerer(self, kw, attr_name):
        return getattr(kw, attr_name).lower()


class _KeywordList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent):
        style = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._create_headers()

    def _create_headers(self):
        for col, title in enumerate(_KeywordData.headers):
            self.InsertColumn(col, title)
        self.SetColumnWidth(0, 250)

    def show_keywords(self, keywords):
        self._keywords = keywords
        self.SetItemCount(len(self._keywords))

    def OnGetItemText(self, row, col):
        kw = self._keywords[row]
        return [kw.name, kw.source, kw.shortdoc][col]

