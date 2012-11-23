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

    HEADER = 'Search Tests'

    def enable(self):
        self.register_search_action(self.HEADER, self.show_search_for, ImageProvider().TEST_SEARCH_ICON, default=True)

    def show_search_for(self, text):
        d = TestsDialog(text, _TestSearchListModel(self._search(text.lower(), self.frame._controller.data)))
        d.add_selection_listener(self._selected)
        d.Show()
        d.set_focus_to_first_match()

    def _selected(self, test):
        wx.CallAfter(self.tree.select_node_by_data, test)

    def _search(self, text, data):
        for test in data.tests:
            if self._matches(text, test):
                yield test
        for s in data.suites:
            for test in self._search(text, s):
                yield test

    def _matches(self, text, test):
        if text in test.name.lower():
            return True
        if text in (str(tag).lower() for tag in test.tags):
            return True
        if text in test.settings[0].value.lower():
            return True
        return False

class _TestSearchListModel(ListModel):

    def __init__(self, tests):
        self._tests = list(tests)

    @property
    @overrides(ListModel)
    def count(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def item_text(self, row, col):
        return self._tests[row].longname

