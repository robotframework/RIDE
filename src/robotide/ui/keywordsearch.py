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

import builtins
import os.path
from functools import (cmp_to_key)

import wx
from wx import Colour
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from .. import utils
from ..controller.filecontrollers import ResourceFileController, TestCaseFileController
from ..pluginapi import Plugin
from ..action import ActionInfo
from ..publish.messages import RideOpenSuite, RideOpenResource, RideImportSetting, RideUserKeyword, RideNewProject
from ..usages.UsageRunner import Usages
from ..widgets import PopupMenuItem, ButtonWithHandler, Label, Font, HtmlWindow, ImageProvider, RIDEDialog

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

ALL_KEYWORDS = _('<all keywords>')
ALL_USER_KEYWORDS = _('<all user keywords>')
ALL_LIBRARY_KEYWORDS = _('<all library keywords>')

SEARCH_KW = _('Search Keywords')


class KeywordSearch(Plugin):
    __doc__ = _("""A plugin for searching keywords based on name or documentation.""")

    def __init__(self, app):
        Plugin.__init__(self, app)
        self.all_keywords = []
        self._criteria = _SearchCriteria()
        self.dirty = False
        self._dialog = None

    def enable(self):
        action = ActionInfo(_('Tools'), SEARCH_KW, self.on_search,
                            shortcut='F5',
                            doc=_('Search keywords from libraries and resources'),
                            icon=ImageProvider().KW_SEARCH_ICON,
                            position=51)
        self.register_action(action)
        self.register_search_action(_('Search Keywords'), self.show_search_for, ImageProvider().KW_SEARCH_ICON)
        self.subscribe(self.mark_dirty, RideOpenSuite, RideOpenResource,
                       RideImportSetting, RideUserKeyword, RideNewProject)
        self._dialog = KeywordSearchDialog(self.frame, self)
        self.tree.register_context_menu_hook(self._search_resource)

    def on_search(self, event):
        __ = event
        self._dialog.show_search_with_criteria()

    def mark_dirty(self, message):
        _ = message
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
        return [kw for kw in self.all_keywords if self._criteria.matches(kw)]

    def _search_resource(self, item):
        if isinstance(item, (TestCaseFileController, ResourceFileController)):
            def _callable(arg=None):
                self._show_resource(os.path.basename(item.source))
            return [PopupMenuItem(SEARCH_KW,'Search Keywords', ccallable=_callable)]
        return []

    def _show_resource(self, resource):
        self._dialog.show_search_with_criteria(source=resource)

    def show_search_for(self, pattern):
        self._dialog.show_search_with_criteria(pattern=pattern)

    def disable(self):
        self.unregister_actions()
        self.unsubscribe_all()


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

    @staticmethod
    def _contains(string, pattern):
        return utils.normalize(pattern) in utils.normalize(string)


class KeywordSearchDialog(RIDEDialog):

    def __init__(self, parent, searcher):
        RIDEDialog.__init__(self, title=SEARCH_KW, parent=parent, size=(650, 400),
                            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self._plugin = searcher
        self._create_components()
        self._make_bindings()
        self._sort_order = _SortOrder()
        self._last_selected_kw = None
        self.CenterOnParent()

    def _create_components(self):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._add_search_control()
        self._add_keyword_list()
        self._add_keyword_details()
        self.SetSize((700, 500))

    def _add_search_control(self):
        line1 = self._horizontal_sizer()
        self._add_pattern_filter(line1)
        self._add_doc_filter(line1)
        self.Sizer.Add(line1, 0, wx.ALL, 3)
        line2 = self._horizontal_sizer()
        self._add_source_filter(line2)
        self.Sizer.Add(line2, 0, wx.ALL, 3)

    @staticmethod
    def _horizontal_sizer():
        return wx.BoxSizer(wx.HORIZONTAL)

    def _add_pattern_filter(self, sizer):
        sizer.Add(Label(self, label=_('Search term: ')))
        self._search_control = wx.SearchCtrl(self, size=(200, -1), style=wx.TE_PROCESS_ENTER)
        self._search_control.SetBackgroundColour(Colour(self.color_secondary_background))
        self._search_control.SetForegroundColour(Colour(self.color_secondary_foreground))
        sizer.Add(self._search_control)

    def _add_doc_filter(self, sizer):
        self._use_doc = wx.CheckBox(self, label=_('Search documentation'))
        self._use_doc.SetValue(True)
        sizer.Add(self._use_doc)

    def _add_source_filter(self, sizer):
        sizer.Add(Label(self, label=_('Source: ')))
        self._source_filter = wx.ComboBox(self, value=ALL_KEYWORDS, size=(300, -1),
                                          choices=self._get_sources(), style=wx.CB_READONLY)
        self._source_filter.SetBackgroundColour(Colour(self.color_secondary_background))
        self._source_filter.SetForegroundColour(Colour(self.color_secondary_foreground))
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
        self._find_usages_button = ButtonWithHandler(self, _('Find Usages'), handler=self.on_find_usages)
        self._find_usages_button.SetBackgroundColour(Colour(self.color_secondary_background))
        self._find_usages_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.Sizer.Add(self._find_usages_button, 0, wx.ALL, 3)
        self._results_text = wx.StaticText(self, -1, _('Results: %d') % 0)
        self.Sizer.Add(self._results_text, 0, wx.ALL, 3)

    def _add_to_sizer(self, component):
        self.Sizer.Add(component, 1, wx.EXPAND | wx.ALL, 3)

    def on_find_usages(self, event):
        __ = event
        Usages(self._plugin.model, self._plugin.tree.highlight, self._last_selected_kw.name,
               self._last_selected_kw).show()

    def _make_bindings(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected, self._list)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.on_search,
                  self._search_control)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_search, self._search_control)
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHECKBOX, self.on_use_doc_change, self._use_doc)
        self.Bind(wx.EVT_COMBOBOX, self.on_source_filter_change, self._source_filter)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_click)

    def on_col_click(self, event):
        col = event.GetColumn()
        if self._sort_order.is_sortable_column(col):
            self._sort_order.sort(col)
            self._populate_search()
        event.Skip()

    def on_activate(self, event):
        __ = event
        if self._plugin.have_keywords_changed():
            self._update_sources()
            self._populate_search()

    def on_use_doc_change(self, event):
        __ = event
        self._populate_search()

    def on_search(self, event):
        __ = event
        self._sort_order.searched(self._get_search_text())
        self._populate_search()

    def on_source_filter_change(self, event):
        self.on_use_doc_change(event)

    def on_key(self, event):
        # Needed for HtmlWindow callback
        pass

    def on_item_selected(self, event):
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

    def on_close(self, event):
        __ = event
        self.Hide()

    def _populate_search(self):
        self._keywords = _KeywordData(self._plugin.search(*self._get_search_criteria()),
                                      self._sort_order, self._get_search_text())
        self._update_keyword_selection()
        self._list.show_keywords(self._keywords, self._last_selected_kw)
        self._results_text.SetLabel(_('Results: %d') % len(self._keywords))
        self.Refresh()

    def _get_search_criteria(self):
        return self._get_search_text(), self._use_doc.GetValue(), self._source_filter.GetValue()

    def _get_search_text(self):
        return self._search_control.GetValue().lower()

    def _update_keyword_selection(self):
        if self._keywords and self._last_selected_kw not in self._keywords:
            self._last_selected_kw = self._keywords[0]
        self._update_details()

    def _update_details(self):
        if self._last_selected_kw in self._keywords:
            self._details.set_content(self._last_selected_kw.details)
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

    @staticmethod
    def is_sortable_column(col):
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
    headers = [_('Name'), _('Source'), _('Description')]
    headers_attr = ['Name', 'Source', 'Description']  # Non-translated names

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
            self.headers_attr[sort_order.column].lower())),
                      reverse=not sort_order.sort_up)

    @staticmethod
    def m_cmp(a, b):
        return (a > b) - (a < b)

    def _get_comparator_for(self, atrr_name):
        return lambda kw, kw2: self.m_cmp(self._value_lowerer(kw, atrr_name),
                                          self._value_lowerer(kw2, atrr_name))

    @staticmethod
    def _value_lowerer(kw, attr_name):
        return getattr(kw, attr_name).lower()


class _KeywordList(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, plugin):
        style = wx.LC_REPORT | wx.NO_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VIRTUAL
        wx.ListCtrl.__init__(self, parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
        self.SetBackgroundColour(Colour(parent.color_background))
        self.SetForegroundColour(Colour(parent.color_foreground))
        self._keywords = None
        self._plugin = plugin
        self._create_headers()
        self._link_attribute = self._create_link_attribute()
        self._image_list = self._create_image_list()
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

    def _create_headers(self):
        for col, title in enumerate(_KeywordData.headers):
            self.InsertColumn(col, title)
            self.SetBackgroundColour(Colour(self.GetParent().color_background))
            self.SetForegroundColour(Colour(self.GetParent().color_foreground))
        self.SetColumnWidth(0, 250)

    @staticmethod
    def _create_link_attribute():
        if wx.VERSION < (4, 1, 0):
            attr = wx.ListItemAttr()
        else:
            attr = wx.ItemAttr()
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
        self.SetBackgroundColour(Colour(self.GetParent().color_secondary_background))
        self.SetForegroundColour(Colour(self.GetParent().color_secondary_foreground))
        if keywords:
            index = self._keywords.index(kw_selection)
            self.Select(index)
            self.Focus(index)

    def on_left_up(self, event):
        item, flags = self.HitTest(event.Position)
        if item == wx.NOT_FOUND:
            return
        kw = self._keywords[item]
        if kw.is_user_keyword() and (flags & wx.LIST_HITTEST_ONITEMICON):
            self._plugin.select_user_keyword_node(kw.item)

    def OnGetItemText(self, row, col):  # Overrides wx method
        kw = self._keywords[row]
        return [kw.name, kw.source, kw.shortdoc][col]

    def OnGetItemImage(self, item):  # Overrides wx method
        if self._keywords[item].is_user_keyword():
            return 0  # index in self._image_list
        return -1  # No image
