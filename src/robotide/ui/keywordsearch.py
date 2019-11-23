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

import wx
import os.path

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from functools import (total_ordering, cmp_to_key)
from robotide.controller.filecontrollers import (ResourceFileController,
                                                 TestCaseFileController)
from robotide.pluginapi import (Plugin, ActionInfo, RideOpenSuite,
        RideOpenResource, RideImportSetting, RideUserKeyword, RideNewProject)
from robotide.usages.UsageRunner import Usages
from robotide import utils
from robotide.widgets import (PopupMenuItem, ButtonWithHandler, Label, Font,
        HtmlWindow, ImageProvider)

ALL_KEYWORDS = '<all keywords>'
ALL_USER_KEYWORDS = '<all user keywords>'
ALL_LIBRARY_KEYWORDS = '<all library keywords>'


class KeywordSearch(Plugin):
    """A plugin for searching keywords based on name or documentation."""

    def __init__(self, app):
        Plugin.__init__(self, app)
        self.all_keywords = []
        self._criteria = _SearchCriteria()
        self.dirty = False

    def enable(self):
        action = ActionInfo('Tools', 'Search Keywords', self.OnSearch,
                            shortcut='F5',
                            doc='Search keywords from libraries and resources',
                            icon=ImageProvider().KW_SEARCH_ICON,
                            position=51)
        self.register_action(action)
        self.register_search_action('Search Keywords', self.show_search_for, ImageProvider().KW_SEARCH_ICON)
        self.subscribe(self.mark_dirty, RideOpenSuite, RideOpenResource,
                       RideImportSetting, RideUserKeyword, RideNewProject)
        self._dialog = KeywordSearchDialog(self.frame, self)
        self.tree.register_context_menu_hook(self._search_resource)

    def OnSearch(self, event):
        self._dialog.show_search_with_criteria()

    def mark_dirty(self, message):
        self.dirty = True

    def have_keywords_changed(self):
        if not self.dirty:
            return False
        self._update()
        return True

    def _update(self):
        self.dirty = False
        self.all_keywords = self.model.get_all_keywords()

    def search(self, pattern, search_docs, source_filter):
        self._criteria = _SearchCriteria(pattern, search_docs, source_filter)
        return self._search()

    def _search(self):
        return [ kw for kw in self.all_keywords if self._criteria.matches(kw) ]

    def _search_resource(self, item):
        if isinstance(item, (TestCaseFileController, ResourceFileController)):
            callable = lambda x: self._show_resource(os.path.basename(item.source))
            return [PopupMenuItem('Search Keywords', callable=callable)]
        return []

    def _show_resource(self, resource):
        self._dialog.show_search_with_criteria(source=resource)

    def show_search_for(self, pattern):
        self._dialog.show_search_with_criteria(pattern=pattern)

    def disable(self):
        self.unregister_actions()

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
        wx.Frame.__init__(self, parent, title="Search Keywords",
                          style=wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self._plugin = searcher
        self._create_components()
        self._make_bindings()
        self._sort_order = _SortOrder()
        self._last_selected_kw = None
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.CenterOnParent()

    def _create_components(self):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._add_search_control()
        self._add_keyword_list()
        self._add_keyword_details()
        self.SetSize((700,500))

    def _add_search_control(self):
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1)
        self._add_doc_filter(line1)
        self.Sizer.Add(line1, 0, wx.ALL, 3)
        line2 = self._horizontal_sizer()
        self._add_source_filter(line2)
        self.Sizer.Add(line2, 0, wx.ALL, 3)

    def _horizontal_sizer(self):
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer):
        sizer.Add(Label(self, label='Search term: '))
        self._search_control = wx.SearchCtrl(self, size=(200,-1),
                                             style=wx.TE_PROCESS_ENTER)
        sizer.Add(self._search_control)

    def _add_doc_filter(self, sizer):
        self._use_doc = wx.CheckBox(self, label='Search documentation')
        self._use_doc.SetValue(True)
        sizer.Add(self._use_doc)

    def _add_source_filter(self, sizer):
        sizer.Add(Label(self, label='Source: '))
        self._source_filter = wx.ComboBox(self, value=ALL_KEYWORDS, size=(300, -1),
                                          choices=self._get_sources(), style=wx.CB_READONLY)
        sizer.Add(self._source_filter)

    def _get_sources(self):
        sources = []
        for kw in self._plugin.all_keywords:
            if kw.source not in sources:
                sources.append(kw.source)
        return [ALL_KEYWORDS, ALL_USER_KEYWORDS, ALL_LIBRARY_KEYWORDS] + sorted(sources)

    def _add_keyword_list(self):
        self._list = _KeywordList(self, self._plugin)
        self._list.SetSize(self.Size)
        self._add_to_sizer(self._list)

    def _add_keyword_details(self):
        self._details = HtmlWindow(self)
        self._add_to_sizer(self._details)
        self._find_usages_button = ButtonWithHandler(self, 'Find Usages')
        self.Sizer.Add(self._find_usages_button, 0, wx.ALL, 3)

    def _add_to_sizer(self, component):
        self.Sizer.Add(component, 1, wx.EXPAND | wx.ALL, 3)

    def OnFindUsages(self, event):
        Usages(self._plugin.model, self._plugin.tree.highlight, self._last_selected_kw.name,  self._last_selected_kw).show()

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self._list)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch,
                  self._search_control)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self._search_control)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CHECKBOX, self.OnUseDocChange, self._use_doc)
        self.Bind(wx.EVT_COMBOBOX, self.OnSourceFilterChange, self._source_filter)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

    def OnColClick(self,event):
        col = event.GetColumn()
        if self._sort_order.is_sortable_column(col):
            self._sort_order.sort(col)
            self._populate_search()
        event.Skip()

    def OnActivate(self, event):
        if self._plugin.have_keywords_changed():
            self._update_sources()
            self._populate_search()

    def OnUseDocChange(self, event):
        self._populate_search()

    def OnSearch(self, event):
        self._sort_order.searched(self._get_search_text())
        self._populate_search()

    def OnSourceFilterChange(self, event):
        self._populate_search()

    def OnKey(self, event):
        # Needed for HtmlWindow callback
        pass

    def OnItemSelected(self, event):
        self._last_selected_kw = self._keywords[event.Index]
        self._update_details()

    def _update_sources(self):
        selection = self._source_filter.GetValue()
        self._source_filter.Clear()
        for source in self._get_sources():
            self._source_filter.Append(source)
        self._source_filter.SetValue(selection)
        if self._source_filter.GetValue() != selection:
            self._source_filter.SetValue(ALL_KEYWORDS)

    def OnClose(self, event):
        self.Hide()

    def _populate_search(self):
        self._keywords = _KeywordData(self._plugin.search(*self._get_search_criteria()),
                                      self._sort_order, self._get_search_text())
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
            self._find_usages_button.Enable()
        else:
            self._details.clear()
            self._find_usages_button.Disable()

    def show_search_with_criteria(self, pattern='', search_docs=True, source=ALL_KEYWORDS):
        self._update_widgets(pattern, search_docs, source)
        self._populate_search()
        self._show()
        self._search_control.SetFocus()

    def _update_widgets(self, pattern, search_docs, source):
        self._search_control.SetValue(pattern)
        self._use_doc.SetValue(search_docs)
        self._source_filter.SetValue(source)

    def _show(self):
        if not self.IsShown():
            self.Show()
        self.Raise()


class _SortOrder(object):

    def __init__(self):
        self.sort_up = True
        self.column = 0
        self.default_order = False

    def searched(self, term):
        self.__init__()
        if term:
            self.default_order = True

    def swap_direction(self):
        self.sort_up = not self.sort_up

    def is_sortable_column(self, col):
        return col < 2

    def sort(self, col):
        if self._has_been_sorted_by(col):
            self.swap_direction()
        else:
            self.sort_up = True
            self.column = col
        self.default_order = False

    def _has_been_sorted_by(self, col):
        return self.column == col and not self.default_order


class _KeywordData(list):
    headers = ['Name', 'Source', 'Description']

    def __init__(self, keywords, sort_order, search_criteria=None):
        self.extend(self._sort(keywords, sort_order, search_criteria))

    def _sort(self, keywords, sort_order, search_criteria=None):
        if sort_order.default_order:
            return self._sort_by_search(keywords, sort_order, search_criteria)
        return self._sort_by_attr(keywords, sort_order)

    def _sort_by_search(self, keywords, sort_order, search_criteria):
        search_criteria = search_criteria.lower()
        starts_with = [kw for kw in keywords if kw.name.lower().startswith(search_criteria)]
        name_contains = [kw for kw in keywords if (search_criteria in kw.name.lower()
                                                   and kw not in starts_with)]
        doc_contains = [kw for kw in keywords if (search_criteria in kw.details.lower()
                                                  and kw not in starts_with
                                                  and kw not in name_contains)]
        result = []
        for to_sort in (starts_with, name_contains, doc_contains):
            result.extend(self._sort_by_attr(to_sort, sort_order))
        return result

    def _sort_by_attr(self, keywords, sort_order):
        return sorted(keywords, key=cmp_to_key(self._get_comparator_for(
            self.headers[sort_order.column].lower())),
                      reverse=not sort_order.sort_up)

    @staticmethod
    def m_cmp(a, b):
        return (a > b) - (a < b)

    def _get_comparator_for(self, atrr_name):
        return lambda kw, kw2: self.m_cmp(self._value_lowerer(kw, atrr_name),
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
        attr.SetFont(Font().underlined)
        return attr

    def _create_image_list(self):
        imglist = wx.ImageList(16, 16)
        imglist.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16, 16)))
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
        if item == wx.NOT_FOUND:
            return
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
