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
        self._texts = text.lower().split()
        self._tags_only = tags_only

    def matches(self, test):
        name = test.name.lower() if not self._tags_only else ()
        tags = [unicode(tag).lower() for tag in test.tags]
        doc = test.documentation.value.lower() if not self._tags_only else ()
        matches = []
        for text in self._texts:
            match = self._unit_match(text, name, tags, doc)
            if not match:
                return False
            matches += [match]
        return matches

    def _unit_match(self, text, name, tags, doc):
        if text in name:
            return NameMatchingResult(text, name)
        if any(text in tag for tag in tags):
            return TagMatchingResult(text, [tag for tag in tags if text in tag][0])
        if text in doc:
            return DocMatchingResult(text, doc)
        return False


class SearchResult(object):

    def __init__(self, matching_search_string, string, super_over_number):
        self._matching_search_string = matching_search_string
        self._string = string
        self._over_number = self._calculate_over_number()
        self._super_over_number = super_over_number

    def _calculate_over_number(self):
        if self._matching_search_string == self._string:
            return 100000
        if self._matching_search_string in self._string.split():
            return 1000
        if self._string.startswith(self._matching_search_string):
            return 100
        return 12

    def __cmp__(self, other):
        if self._super_over_number != other._super_over_number:
            return cmp(other._super_over_number, self._super_over_number)
        if self._over_number != other._over_number:
            return cmp(other._over_number, self._over_number)
        return cmp(self._string, other._string)

    def __repr__(self):
        return '"%s":%d' % (self._string, self._over_number)


def NameMatchingResult(search_string, name):
    return SearchResult(search_string, name, 3)

def TagMatchingResult(search_string, tag_match):
    return SearchResult(search_string, tag_match, 2)

def DocMatchingResult(search_string, doc_match):
    return SearchResult(search_string, doc_match, 1)

