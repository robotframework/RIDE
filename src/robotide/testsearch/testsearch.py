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
from robotide.pluginapi import Plugin
from robotide.testsearch.testsdialog import TestsDialog
from robotide.utils import overrides
from robotide.widgets import ImageProvider
from robotide.widgets.list import ListModel


class TestSearchPlugin(Plugin):
    """A plugin for searching tests based on name, tags and documentation"""
    HEADER = 'Search Tests'

    def enable(self):
        self.register_search_action(self.HEADER, self.show_search_for, ImageProvider().TEST_SEARCH_ICON, default=True)

    def show_search_for(self, text):
        d = TestsDialog(text, _TestSearchListModel(self._search(TestSearchMatcher(text), self.frame._controller.data)))
        d.add_selection_listener(self._selected)
        d.Show()
        d.set_focus_to_first_match()

    def _selected(self, selection):
        test, match_location = selection
        wx.CallAfter(self.tree.select_node_by_data, test)

    def _search(self, matcher, data):
        for test in data.tests:
            match = matcher._matches(test)
            if match:
                yield test, match
        for s in data.suites:
            for test, match in self._search(matcher, s):
                yield test, match


class TestSearchMatcher(object):

    def __init__(self, text):
        self._text = text.lower()

    def matches(self, test):
        if self._text in test.name.lower():
            return 'Name match'
        if any(self._text in str(tag).lower() for tag in test.tags):
            return 'Tag match'
        if self._text in test.settings[0].value.lower():
            return 'Documentation match'
        return False


class _TestSearchListModel(ListModel):

    def __init__(self, tests):
        self._tests = sorted(tests, cmp=self._comparator)

    def _comparator(self, first, second):
        if first[1] == second[1]:
            return cmp(first[0], first[1])
        if first[1] == 'Name match':
            return -1
        if second[1] == 'Name match':
            return 1
        if first[1] == 'Tag match':
            return -1
        return 1

    @property
    @overrides(ListModel)
    def count(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def item_text(self, row, col):
        test, match_location = self._tests[row]
        if col == 0:
            return test.longname
        return match_location

