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
import os.path

from robotide.pluginapi import Plugin, ActionInfo, RideOpenSuite,\
    RideOpenResource, RideImportSetting, RideUserKeyword
from robotide import utils
from robotide import context
from robotide.utils.components import PopupMenuItem


ALL_KEYWORDS = '<all keywords>'
ALL_USER_KEYWORDS = '<all user keywords>'
ALL_LIBRARY_KEYWORDS = '<all library keywords>'


class KeywordSearch(Plugin):
    """A plugin for searching keywords based on name or documentation."""

    def __init__(self, app):
        Plugin.__init__(self, app)
        self.all_keywords = []
        self._criteria = _SearchCriteria()

    def enable(self):
        action = ActionInfo('Tools', 'Search Keywords', self.OnSearch,
                            shortcut='F5',
                            doc='Search keywords from libraries and resources')
        self.register_action(action)
        self.subscribe(self.refresh, RideOpenSuite, RideOpenResource,
                       RideImportSetting, RideUserKeyword)
        self._dialog = KeywordSearchDialog(self.frame, self)
        self.tree.register_context_menu_hook(self._search_resource)

    def OnSearch(self, event):
        self._clear_search_criteria()
        self._show_dialog()

    def _clear_search_criteria(self):
        self._dialog.set_filters()

    def _show_dialog(self):
        if not self._dialog.IsShown():
            self._dialog.Show()
        self._dialog.Raise()

    def refresh(self, message):
        self.all_keywords = self.model.get_all_keywords()

    def search(self, pattern, search_docs, source_filter):
        self._criteria = _SearchCriteria(pattern, search_docs, source_filter)
        return self._search()

    def _search(self):
        return [ kw for kw in self.all_keywords if self._criteria.matches(kw) ]

    def _search_resource(self, item):
        if item.is_directory_suite():
            return []
        callable = lambda x: self._show_resource(os.path.basename(item.source))
        return [PopupMenuItem('Search Keywords', callable=callable)]

    def _show_resource(self, resource):
        self._dialog.set_filters(source=resource)
        self._show_dialog()


class _SearchCriteria(object):

    def __init__(self, pattern='', search_docs=True, source_filter=ALL_KEYWORDS):
        self._pattern = pattern
        self._search_docs = search_docs
        self._source_filter = source_filter

    def matches(self, kw):
        if not self._matches_source_filter(kw):
            return False
        if self._contains(kw.name, self._pattern):
            return True
        return self._search_docs and self._contains(kw.doc, self._pattern)

    def _matches_source_filter(self, kw):
        if self._source_filter == ALL_KEYWORDS:
            return True
        if self._source_filter == ALL_USER_KEYWORDS and kw.is_user_keyword():
            return True
        if self._source_filter == ALL_LIBRARY_KEYWORDS and kw.is_library_keyword():
            return True
        return self._source_filter == kw.source

    def _contains(self, string, pattern):
        return utils.normalize(pattern) in utils.normalize(string)


class KeywordSearchDialog(wx.Frame):

    def __init__(self, parent, searcher):
        wx.Frame.__init__(self, parent, title="Search Keywords")
        self._plugin = searcher
        self._create_components()
        self._make_bindings()
        self._sort_up = True
        self._sortcol = 0
        self._last_selected_kw = None
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.CenterOnParent()

    def set_filters(self, pattern='', search_docs=True, source=ALL_KEYWORDS):
        self._search_control.SetValue(pattern)
        self._use_doc.SetValue(search_docs)
        self._source_filter.SetValue(source)

    def _create_components(self):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._add_search_control()
        self._list = _KeywordList(self, self._plugin)
        self._list.SetSize(self.Size)
        self.Sizer.Add(self._list, 1, wx.EXPAND| wx.ALL, 3)
        self._details = utils.RideHtmlWindow(self)
        self.Sizer.Add(self._details, 1, wx.EXPAND | wx.ALL, 3)
        self.SetSize((700,500))

    def _add_search_control(self):
        line1 = wx.BoxSizer(wx.HORIZONTAL)
        self._add_pattern_filter(line1)
        self._add_doc_filter(line1)
        self.Sizer.Add(line1, 0, wx.ALL, 3)
        line2 = wx.BoxSizer(wx.HORIZONTAL)
        self._add_source_filter(line2)
        self.Sizer.Add(line2, 0, wx.ALL, 3)

    def _add_pattern_filter(self, sizer):
        sizer.Add(wx.StaticText(self, label='Search term: '))
        self._search_control = wx.SearchCtrl(self, size=(200,-1),
                                             style=wx.TE_PROCESS_ENTER)
        sizer.Add(self._search_control)

    def _add_doc_filter(self, sizer):
        self._use_doc = wx.CheckBox(self, label='Search documentation')
        self._use_doc.SetValue(True)
        sizer.Add(self._use_doc)

    def _add_source_filter(self, sizer):
        sizer.Add(wx.StaticText(self, label='Source: '))
        self._source_filter = wx.ComboBox(self, value=ALL_KEYWORDS, size=(300, -1),
                                          choices=self._get_sources(), style=wx.CB_DROPDOWN)
        sizer.Add(self._source_filter)

    def _get_sources(self):
        sources = []
        for kw in self._plugin.all_keywords:
            if kw.source not in sources:
                sources.append(kw.source)
        return [ALL_KEYWORDS, ALL_USER_KEYWORDS, ALL_LIBRARY_KEYWORDS] + sorted(sources)

    def _update_sources(self):
        self._source_filter.Clear()
        for source in self._get_sources():
            self._source_filter.Append(source)

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self._list)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnFirstSearch,
                  self._search_control)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnFirstSearch, self._search_control)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHECKBOX, self.OnUseDocChange, self._use_doc)
        self.Bind(wx.EVT_COMBOBOX, self.OnSourceFilterChange, self._source_filter)
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
        self._populate_search()
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
        self._update_sources()
        self._populate_search()

    def OnUseDocChange(self, event):
        self._populate_search()

    def OnFirstSearch(self, event):
        self._populate_search(self._get_search_text())

    def OnSourceFilterChange(self, event):
        self._populate_search()

    def OnKey(self, event):
        # Needed for HtmlWindow callback
        pass

    def OnItemSelected(self, event):
        self._last_selected_kw = self._keywords[event.Index]
        self._update_details()

    def OnClose(self, event):
        self.Hide()

    def _populate_search(self, search_criteria=None):
        self._keywords = _KeywordData(self._plugin.search(*self._get_search_criteria()),
                                      self._sortcol, self._sort_up, search_criteria)
        self._update_keyword_selection()
        self._list.show_keywords(self._keywords, self._last_selected_kw)
        self.Refresh()

    def _get_search_criteria(self):
        return self._get_search_text(), self._use_doc.GetValue(), self._source_filter.GetValue()

    def _get_search_text(self):
        return self._search_control.GetValue().lower()

    def _update_keyword_selection(self):
        if not self._last_selected_kw in self._keywords and self._keywords:
            self._last_selected_kw = self._keywords[0]
        self._update_details()

    def _update_details(self):
        if self._last_selected_kw in self._keywords:
            self._details.SetPage(self._last_selected_kw.details)
        else:
            self._details.clear()


class _KeywordData(list):
    headers = ['Name', 'Source', 'Description']

    def __init__(self, keywords, sort_col=0, sort_up=True, search_criteria=None):
        self.extend(self._sort(keywords, sort_col, sort_up, search_criteria))

    def _sort(self, keywords, sort_col, sort_up, search_criteria=None):
        if search_criteria:
            return self._sort_by_search(keywords, search_criteria)
        return self._sort_by_attr(keywords, self.headers[sort_col].lower(),
                                  sort_up)

    def _sort_by_search(self, keywords, search_criteria):
        search_criteria = search_criteria.lower()
        starts_with = [kw for kw in keywords if kw.name.lower().startswith(search_criteria)]
        name_contains = [kw for kw in keywords if (search_criteria in kw.name.lower()
                                                   and kw not in starts_with)]
        doc_contains = [kw for kw in keywords if (search_criteria in kw.details.lower()
                                                  and kw not in starts_with
                                                  and kw not in name_contains)]
        result = []
        for to_sort in (starts_with, name_contains, doc_contains):
            result.extend(self._sort_by_attr(to_sort, self.headers[0].lower(), True))
        return result

    def _sort_by_attr(self, keywords, attr_name, sort_up):
        return sorted(keywords, cmp=self._get_comparator_for(attr_name),
                      reverse=not sort_up)

    def _get_comparator_for(self, atrr_name):
        return lambda kw, kw2: cmp(self._value_lowerer(kw, atrr_name),
                                   self._value_lowerer(kw2, atrr_name))

    def _value_lowerer(self, kw, attr_name):
        return getattr(kw, attr_name).lower()


class _KeywordList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, plugin):
        style = wx.LC_REPORT|wx.NO_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._plugin = plugin
        self._create_headers()
        self._link_attribute = self._create_link_attribute()
        self._image_list = self._create_image_list()
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def _create_headers(self):
        for col, title in enumerate(_KeywordData.headers):
            self.InsertColumn(col, title)
        self.SetColumnWidth(0, 250)

    def _create_link_attribute(self):
        attr = wx.ListItemAttr()
        attr.SetTextColour(wx.BLUE)
        attr.SetFont(context.Font().underlined)
        return attr

    def _create_image_list(self):
        imglist = wx.ImageList(16, 16)
        imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16, 16)))
        self.SetImageList(imglist, wx.IMAGE_LIST_SMALL)
        return imglist

    def show_keywords(self, keywords, kw_selection):
        self._keywords = keywords
        self.SetItemCount(len(self._keywords))
        if keywords:
            index = self._keywords.index(kw_selection)
            self.Select(index)
            self.Focus(index)

    def OnLeftUp(self, event):
        item, flags = self.HitTest(event.Position)
        kw = self._keywords[item]
        if kw.is_user_keyword() and (flags & wx.LIST_HITTEST_ONITEMICON):
            self._plugin.select_user_keyword_node(kw.item)

    def OnGetItemText(self, row, col):
        kw = self._keywords[row]
        return [kw.name, kw.source, kw.shortdoc][col]

    def OnGetItemImage(self, item):
        if self._keywords[item].is_user_keyword():
            return 0 # index in self._image_list
        return -1 # No image
