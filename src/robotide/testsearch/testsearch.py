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
from robot.utils import MultiMatcher
from robotide.action import ActionInfo
from robotide.pluginapi import Plugin
from robotide.testsearch.testsdialog import TestsDialog
from robotide.widgets import ImageProvider


class TestSearchPlugin(Plugin):
    """A plugin for searching tests based on name, tags and documentation"""
    HEADER = 'Search Tests'

    def enable(self):
        self.register_action(ActionInfo('Tools', self.HEADER, self.show_empty_search, shortcut='F3', doc=self.__doc__))
        self.register_search_action(self.HEADER, self.show_search_for, ImageProvider().TEST_SEARCH_ICON, default=True)
        self._dialog = None

    def show_search_for(self, text):
        if self._dialog is None:
            self._create_tests_dialog()
        self._dialog.set_search_model(text, self._search(TestSearchMatcher(text, self._dialog.tags_only), self.frame._controller.data))
        self._dialog.set_focus_to_default_location()

    def _create_tests_dialog(self):
        self._dialog = TestsDialog(search_handler=self.show_search_for)
        self._dialog.add_selection_listener(self._selected)
        self._dialog.Bind(wx.EVT_CLOSE, self._dialog_closed)
        self._dialog.Show()

    def _dialog_closed(self, event):
        self._dialog = None
        event.Skip()

    def show_empty_search(self, event):
        self.show_search_for('')

    def _selected(self, selection):
        test, match_location = selection
        wx.CallAfter(self.tree.select_node_by_data, test)

    def _search(self, matcher, data):
        for test in data.tests:
            match = matcher.matches(test)
            if match:
                yield test, match
        for s in data.suites:
            for test, match in self._search(matcher, s):
                yield test, match


class TestSearchMatcher(object):

    def __init__(self, text, tags_only=False):
        self._text_matcher = MultiMatcher(text.split())
        self._tags_only = tags_only

    def matches(self, test):
        if self._matches(test):
            return SearchResult(self._text_matcher, test)
        return False

    def _matches(self, test):
        name = test.name.lower() if not self._tags_only else ''
        if self._text_matcher.match(name):
            return True
        if any(self._text_matcher.match(unicode(tag)) for tag in test.tags):
            return True
        doc = test.documentation.value.lower() if not self._tags_only else ''
        if self._text_matcher.match(doc):
            return True
        return False


class SearchResult(object):

    def __init__(self, matcher, test):
        self._matcher = matcher
        self._test = test

    def __cmp__(self, other):
        names = self._compare(self._is_name_match(), other._is_name_match())
        if names:
            return names
        if self._is_name_match() and other._is_name_match():
            return cmp(self._test.name, other._test.name)
        tags = self._compare(self._is_tag_match(), other._is_tag_match())
        if tags:
            return tags
        if self._is_tag_match() and other._is_tag_match():
            return cmp([unicode(tag) for tag in self._test.tags], [unicode(tag) for tag in other._test.tags])
        return 0

    def _compare(self, my_result, other_result):
        if my_result and not other_result:
            return -1
        if not my_result and other_result:
            return 1
        return 0

    def _is_name_match(self):
        return self._matcher.match(self._test.name.lower())

    def _is_tag_match(self):
        return any(self._matcher.match(unicode(tag)) for tag in self._test.tags)

    def __repr__(self):
        return self._test.name
