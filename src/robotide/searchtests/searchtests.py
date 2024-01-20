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

from functools import (total_ordering, cmp_to_key)
import builtins
import wx

from .. import robotapi
from ..action import ActionInfo
from ..pluginapi import Plugin
from ..publish import RideOpenTagSearch
from .dialogsearchtests import TestsDialog
from ..widgets import ImageProvider

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


@total_ordering
class TestSearchPlugin(Plugin):
    __doc__ = _("""A plugin for searching tests based on name, tags and documentation""")
    __test__ = False
    HEADER = _('Search Tests')
    _selection = None
    _dialog = None

    def enable(self):
        self.register_action(ActionInfo(
            _('Tools'), self.HEADER, self.show_empty_search,
            shortcut='F3', doc=self.__doc__,
            icon=ImageProvider().TEST_SEARCH_ICON, position=50))
        self.register_search_action(
            self.HEADER, self.show_search_for,
            ImageProvider().TEST_SEARCH_ICON, default=True)
        self.subscribe(self.show_tag_search, RideOpenTagSearch)
        self._dialog = None

    def show_search_for(self, text):
        if self._dialog is None:
            self._create_tests_dialog()
        self._dialog.set_search_model(
            text, self._search_results(TestSearchMatcher(text)))
        self._dialog.set_focus_to_default_location()

    def show_search_for_tag_patterns(self, includes, excludes):
        matcher = TagSearchMatcher(includes, excludes)
        self._dialog.set_tag_search_model(
            includes, excludes, self._search_results(matcher))
        self._dialog.set_focus_to_default_location()

    def show_tag_search(self, message):
        if self._dialog is None:
            self._create_tests_dialog()
        self.show_search_for_tag_patterns(message.includes, message.excludes)
        self._dialog.select_page(1)

    def _create_tests_dialog(self):
        self._dialog = TestsDialog(
            fuzzy_search_handler=self.show_search_for,
            tag_search_handler=self.show_search_for_tag_patterns,
            add_to_selected_handler=self._add_to_selected)
        self._dialog.add_selection_listener(self._selected)
        self._dialog.Bind(wx.EVT_CLOSE, self._dialog_closed)
        self._selected_timer = wx.Timer(self._dialog)
        self._dialog.Bind(wx.EVT_TIMER, self._do_with_selection)
        self._dialog.Show()

    def _add_to_selected(self, tests):
        self.tree.SelectTests(tests)

    def _dialog_closed(self, event):
        self._dialog = None
        event.Skip()

    def show_empty_search(self, event):
        __ = event
        self.show_search_for('')

    def _do_with_selection(self, evt=None):
        _ = evt
        test, _ = self._selection
        if test:
            self.tree.select_node_by_data(test)
            self._dialog.set_focus_to_default_location(test)

    def _selected(self, selection):
        self._selection = selection
        self._selected_timer.Start(400, True)

    def _search_results(self, matcher):
        current_suite = self.frame.controller.data
        if not current_suite:
            return []
        result = self._search(matcher, current_suite)
        return sorted(result, key=cmp_to_key(lambda x, y:
                                             self.m_cmp(x[1], y[1])))

    def _search(self, matcher, data):
        for test in data.tests:
            match = matcher.matches(test)
            if match:
                yield test, match
        for s in data.suites:
            for test, match in self._search(matcher, s):
                yield test, match

    def disable(self):
        self.unregister_actions()

    @staticmethod
    def m_cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return self.name.lower() < other.name.lower()


class TagSearchMatcher(object):

    def __init__(self, includes, excludes):
        self._tag_pattern_includes = robotapi.TagPatterns(
            includes.split()) if includes.split() else None
        self._tag_pattern_excludes = robotapi.TagPatterns(excludes.split())

    def matches(self, test):
        # Comments in Tests section are saved, but should not be visible
        if test.name.startswith('#'):
            return False
        tags = [str(tag) for tag in test.tags]
        if self._matches(tags):
            return test.longname
        return False

    def _matches(self, tags):
        return (self._tag_pattern_includes is None or
                self._tag_pattern_includes.match(tags)) and \
            not self._tag_pattern_excludes.match(tags)


class TestSearchMatcher(object):
    __test__ = False

    def __init__(self, text):
        self._texts = text.split()
        self._texts_lower = [t.lower() for t in self._texts]

    def matches(self, test):
        if self._matches(test):
            return SearchResult(self._texts, self._texts_lower, test)
        return False

    def _matches(self, test):
        name = test.name.lower()
        # Comments in Tests section are saved, but should not be visible
        if name.startswith('#'):
            return False
        if self._match_in(name):
            return True
        if any(self._match_in(str(tag).lower()) for tag in test.tags):
            return True
        doc = test.documentation.value.lower()
        if self._match_in(doc):
            return True
        return False

    def _match_in(self, text):
        return any(word in text for word in self._texts_lower)


class SearchResult(object):

    def __init__(self, original_search_terms, search_terms_lower, test):
        self._original_search_terms = original_search_terms
        self._search_terms_lower = search_terms_lower
        self.test = test
        self.__total_matches = None
        self.__tags = None

    # This is ignored on Python 3
    """
    def __cmp__(self, other):
    """
    def _helper_cmp_(self, other):
        totals, other_totals = self.total_matches(), other.total_matches()
        if totals != other_totals:
            return self.m_cmp(other_totals, totals)
        names = self._compare(
            self.is_name_match(), other.is_name_match(),
            self.test.name, other.test.name)
        if names:
            return names
        tags = self._compare(
            self.is_tag_match(), other.is_tag_match(),
            self.tags(), other.tags())
        if tags:
            return tags
        return self.m_cmp(self.test.name, other.test.name)

    def _compare(self, my_result, other_result, my_cmp, other_cmp):
        if my_result and not other_result:
            return -1
        if not my_result and other_result:
            return 1
        if my_result and other_result:
            return self.m_cmp(my_cmp, other_cmp)
        return 0

    def total_matches(self):
        if not self.__total_matches:
            self.__total_matches = sum(
                1 for word in self._search_terms_lower
                if word in self.test.name.lower()
                or any(word in t for t in self.tags())
                or word in self.test.documentation.value.lower())
        return self.__total_matches

    def _match_in(self, text):
        return any(word in text for word in self._search_terms_lower)

    def is_name_match(self):
        return self._match_in(self.test.name.lower())

    def is_tag_match(self):
        return any(self._match_in(t) for t in self.tags())

    def tags(self):
        if self.__tags is None:
            self.__tags = [str(tag).lower() for tag in self.test.tags]
        return self.__tags

    def __repr__(self):
        return self.test.name

    @staticmethod
    def m_cmp(a, b):
        return (a > b) - (a < b)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return self._helper_cmp_(other) == -1

    def __le__(self, other):
        return self._helper_cmp_(other) <= 0

    def __gt__(self, other):
        return self._helper_cmp_(other) == 1

    def __ge__(self, other):
        return self._helper_cmp_(other) >= 0
