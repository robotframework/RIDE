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
            match = matcher.matches(test)
            if match:
                yield test, match
        for s in data.suites:
            for test, match in self._search(matcher, s):
                yield test, match


class TestSearchMatcher(object):

    def __init__(self, text):
        self._texts = text.lower().split()

    def matches(self, test):
        name = test.name.lower()
        tags = (str(tag).lower() for tag in test.tags)
        doc = test.documentation.value.lower()
        matches = []
        for text in self._texts:
            match = self._unit_match(text, name, tags, doc)
            if not match:
                return False
            matches += [match]
        return matches

    def _unit_match(self, text, name, tags, doc):
        if text in name:
            return TestSearchResult(text, name, super_over_number=1000)
        if any(text in tag for tag in tags):
            return TestSearchResult(text, name, super_over_number=10)
        if text in doc:
            return TestSearchResult(text, doc, super_over_number=1)
        return False


class TestSearchResult(object):

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


class _TestSearchListModel(ListModel):

    def __init__(self, tests):
        self._tests = sorted(tests, cmp=lambda x, y: cmp(x[1], y[1]))

    @property
    @overrides(ListModel)
    def count(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def item_text(self, row, col):
        test, match = self._tests[row]
        if col == 0:
            return test.name
        if col == 1:
            return u', '.join(unicode(t) for t in test.tags)
        return test.datafile_controller.longname

