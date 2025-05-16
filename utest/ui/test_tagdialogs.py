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

import unittest
import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True) # Avoid failing unit tests in system without X11
import wx
from wx.lib.agw.aui import AuiManager
from functools import total_ordering
from robotide.ui.tagdialogs import ViewAllTagsDialog

from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword)
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.application import Project
from robotide.controller.filecontrollers import (TestDataDirectoryController,
                                                 ResourceFileController)
from robotide import utils
from utest.resources import FakeSettings, FakeEditor
from robotide.ui import treeplugin as st
from robotide.ui import treenodehandlers as th
from robotide.publish import PUBLISHER
from robotide.ui.treeplugin import Tree
from robotide.namespace.namespace import Namespace

th.FakeDirectorySuiteHandler = th.FakeUserKeywordHandler = \
    th.FakeSuiteHandler = th.FakeTestCaseHandler = \
    th.FakeResourceHandler = th.TestDataDirectoryHandler
st.Editor = lambda *args: FakeEditor()
Tree._show_correct_editor = lambda self, x: None
Tree.get_active_datafile = lambda self: None
Tree._select = lambda self, node: self.SelectItem(node)

app = wx.App()

"""
class _FakeMainFrame(wx.Frame):
    _editor_panel = None

    def __init__(self):
        self._frame = wx.Frame(None)
        splitter = wx.SplitterWindow(self._frame, style=wx.SP_LIVE_UPDATE)
        self._application = FakeApplication()
        #self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.notebook = NoteBook(splitter, self._application)
        mb = MenuBar(self._frame)
        self.toolbar = ToolBar(self._frame)
        self.actions = ActionRegisterer(mb, self.toolbar,
                                        ShortcutRegistry(self))
        self.tree = None

    def publish(self, *args):
        pass
"""

#TODO Improve Code and remove DEBUG


@total_ordering
class _SortableD(utils.NormalizedDict):

    def __init__(self, initial=None, ignore=(), caseless=True, spaceless=True):
        self._data = {}
        self._keys = {}
        self._initial = initial
        self._ignore = ignore
        self._caseless = caseless
        self._spaceless = spaceless
        self._normalize = utils._normalize
        super(utils.NormalizedDict)

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return self._keys[0].lower() < other._keys[0].lower()

    def __repr__(self):
        return self.__str__()

    # def __iter__(self):
    #    return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def __iter__(self):
        return (self._keys[norm_key] for norm_key in sorted(self._keys))

    def iteritems(self):
        """Returns an iterator over the (key,data) items of the tags"""
        return self._keys.items()


class _ViewAllTagsDialog(ViewAllTagsDialog):

    def __init__(self, frame, controller):
        style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN\
            | wx.FRAME_FLOAT_ON_PARENT
        self.frame = frame
        self.controller = controller.controller
        super(_ViewAllTagsDialog, self).__init__(self, self.frame)
        self.model = controller
        self._results = _SortableD()  # utils.NormalizedDict()
        self.itemDataMap = []
        self.sort_state = (0, 1)

    def _search_for_tags(self):
        unique_tags = _SortableD()  # dict()  # utils.NormalizedDict() # DEBUG
        for i in self.model.suite.children:
            # print(f"DEBUG: _search_for_tags suite {i.name}")
            for test in i.testcase_table.tests:
                # print(f"DEBUG: _search_for_tags test {test.name}")
                try:
                    for tag in getattr(test.tags, 'tags').split("    "):
                        # print(f"DEBUG: _search_for_tags tag {tag}")
                        if tag is None or len(str(tag).strip()) == 0:
                            continue
                        else:
                            tag_name = str(tag)
                        # print(f"DEBUG: _search_for_tags tag_name {tag_name}")
                        if tag_name in unique_tags.keys():
                            # print(f"DEBUG: _search_for_tags unique_tags {unique_tags[tag_name]} {tag_name=} {tag=}")
                            unique_tags[tag_name].append(test)
                        else:
                            # print(f"DEBUG: _search_for_tags unique_tags {unique_tags} {tag_name=} {tag=}")
                            unique_tags[tag_name] = [test]
                except AttributeError:
                    pass
        isreversed = (self.sort_state[0] == 0 and self.sort_state[1] == 0)
        print(f"DEBUG: _search_for_tags isreversed {isreversed} unique {unique_tags.items()}")
        self._results = sorted(unique_tags.items(),
                               key=lambda item: len(item[0]),
                               reverse=isreversed)
        # self._results = sorted(unique_tags.items(),
        #                        key=lambda item: item[0].lower,
        #                        reverse=isreversed)

    def _execute(self):
        self._clear_search_results()
        self._search_for_tags()

        print(f"DEBUG: results after search tests {self._results}")

        self.tagged_test_cases = list()
        self.unique_tags = 0

        idx = 0
        for tag_name, tests in self._results:
            model_entry = idx
            self.tagged_test_cases += tests
            # Mapping the lists model entry with the model for sorting.
            self.itemDataMap.insert(model_entry,
                                    (self._tag_name_for_sort(tag_name),
                                     len(tests)))
            self.unique_tags += 1
            idx += 1
        isreversed = (self.sort_state[1] == 0)
        self.itemDataMap.sort(key=lambda item: item[self.sort_state[0]],
                              reverse=isreversed)

    def show_dialog(self):
        # print("DEBUG: Unique tags {0}\n".format(self.unique_tags))
        # print("DEBUG: _tags_list {0}\n".format(self.itemDataMap))
        self.ShowDialog()
        # pass

    def ShowDialog(self):
        # self._search_for_tags()
        self._execute()
        wx.CallLater(1000, self.Close)
        self.ShowModal()
        # self.Destroy()

    def _clear_search_results(self):
        self._results = {}
        self.itemDataMap = []

    def on_col_click(self, event):
        """
        Simulates clicking on Column (tag name or count), and toggle the
        sorting order.
        """
        _ = event
        if self.sort_state[0] == 0:
            self.sort_state = (0, (0 if self.sort_state[1] == 1 else 1))
        else:
            self.sort_state = (1, (0 if self.sort_state[1] == 1 else 1))
        self._execute()


class _BaseSuiteTreeTest(unittest.TestCase):

    def setUp(self):
        settings = FakeSettings()
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
            MenuBar(self.frame), ToolBar(self.frame),
            ShortcutRegistry(self.frame)), settings)
        # self.frame.Show()
        self._tags_list = utils.NormalizedDict()
        self._tags_list = {"tag-11": [1, 2], "tag-02": [3],
                           "tag-12": [4, 8, 12], "tag-2": [5, 6, 7],
                           "tag-3": [9], "tag-21": [10, 11, 12],
                           "tag-22": [10], "tag-1": [14], "tag-03": [15],
                           "a-01-a2": [1], "08-b": [2],
                           "3-2-1-tag-2c": [3, 6, 8],
                           "8-B-1": [3, 4, 5], "2-b": [7, 3],
                           "a-1-a3": [8, 9, 10, 11], "3-2-03-tag-2a": [12],
                           "a-01-a03": [1], "b-1-a01": [2], "b-01-a01": [15]}
        self.model = self._create_model()
        self._tagsdialog = _ViewAllTagsDialog(self.frame, self.model)
        # self._tagsdialog.show_dialog()

    def tearDown(self):
        PUBLISHER.unsubscribe_all()
        # wx.CallAfter(
        self.app.ExitMainLoop()
        # self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.app.Destroy()
        self.app = None
        # app.MainLoop()  # With this here, there is no Segmentation fault

    def _create_model(self):
        suite = self._create_directory_suite('/top_suite')
        suite.children = [self._create_file_suite('sub_suite_%d.robot' % i)
                          for i in range(3)]
        res = ResourceFile()
        res.source = 'resource.robot'
        res.keyword_table.keywords.append(UserKeyword(res, 'Resource Keyword', ['en']))
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        model = Project(
            Namespace(FakeSettings()), library_manager=library_manager)
        model.controller = TestDataDirectoryController(suite)
        rfc = ResourceFileController(res, project=model)
        model.resources.append(rfc)
        model.insert_into_suite_structure(rfc)
        return model

    def _create_directory_suite(self, source):
        return self._create_suite(TestDataDirectory, source, is_dir=True)

    def _create_file_suite(self, source):
        suite = self._create_suite(TestCaseFile, source)
        suite.testcase_table.tests = [TestCase(
            suite, '%s Fake Test %d' % (suite.name, i)) for i in range(16)]
        # Initialization of Tags
        count = 0
        for i in suite.testcase_table.tests:
            newtag = ""
            for key, test in self._tags_list.items():
                newtag += key + "    " if count in test else ""
                # print(f"DEBUG: _create_file_suite newtag: {newtag}")
                if len(newtag):
                    setattr(i.tags, 'tags', "{0}".format(newtag))
            count += 1
        return suite

    def _create_suite(self, suite_class, source, is_dir=False):
        suite = suite_class()
        suite.source = source
        if is_dir:
            suite.directory = source
        suite.keyword_table.keywords = [
            UserKeyword(suite.keyword_table, '%s Fake UK %d' % (suite.name, i), ['en'])
            for i in range(5)]
        return suite


# @pytest.mark.skip('SKIPPED Since fix in lowercase block_kws')
class TestSortTags(_BaseSuiteTreeTest):

    def test_sort_tags_ascending_count(self):
        self._tagsdialog.sort_state = (1, 0)
        self._tagsdialog.on_col_click(None)
        assert self._tagsdialog.sort_state == (1, 1)
        reference = [[[u'b-', 1, u'-a', 1], 3], [[u'tag-', 3], 3],
                     [[3, u'-', 2, u'-', 3, u'-tag-', 2, u'a'], 3],
                     [[u'tag-', 1], 3], [[u'tag-', 22], 3], [[u'tag-', 3], 3],
                     [[u'tag-', 2], 3], [[u'b-', 1, u'-a', 1], 3],
                     [[8, u'-b'], 3], [[u'a-', 1, u'-a', 3], 3],
                     [[u'a-', 1, u'-a', 2], 3], [[u'tag-', 11], 6],
                     [[2, u'-b'], 6], [[u'tag-', 21], 9], [[u'tag-', 2], 9],
                     [[u'tag-', 12], 9],
                     [[3, u'-', 2, u'-', 1, u'-tag-', 2, u'c'], 9],
                     [[8, u'-b-', 1], 9], [[u'a-', 1, u'-a', 3], 12]]
        cref = list(j for i, j in reference)
        dref = list(j for i, j in self._tagsdialog.itemDataMap)
        print("cref = {0}\ndref = {1}\n".format(cref, dref))
        assert dref == cref
        # self._tagsdialog.show_dialog()

    def test_sort_tags_descending_count(self):
        self._tagsdialog.sort_state = (1, 1)
        self._tagsdialog.on_col_click(None)
        assert self._tagsdialog.sort_state == (1, 0)
        reference = [[[u'a-', 1, u'-a', 3], 12], [[u'tag-', 21], 9],
                 [[u'tag-', 2], 9], [[u'tag-', 12], 9],
                 [[3, u'-', 2, u'-', 1, u'-tag-', 2, u'c'], 9],
                 [[8, u'-b-', 1], 9], [[u'tag-', 11], 6], [[2, u'-b'], 6],
                 [[u'tag-', 3], 3], [[u'b-', 1, u'-a', 1], 3],
                 [[3, u'-', 2, u'-', 3, u'-tag-', 2, u'a'], 3],
                 [[u'tag-', 1], 3], [[u'tag-', 22], 3], [[u'tag-', 3], 3],
                 [[u'tag-', 2], 3], [[u'b-', 1, u'-a', 1], 3],
                 [[8, u'-b'], 3], [[u'a-', 1, u'-a', 3], 3],
                 [[u'a-', 1, u'-a', 2], 3]]
        cref = list(j for i, j in reference)
        dref = list(j for i, j in self._tagsdialog.itemDataMap)
        # print("cref = {0}\ndref = {1}\n".format(cref, dref))
        assert dref == cref
        # self._tagsdialog.show_dialog()

    def test_sort_tags_ascending_value(self):
        self._tagsdialog.sort_state = (0, 0)
        self._tagsdialog.on_col_click(None)
        assert self._tagsdialog.sort_state == (0, 1)
        reference = [[[u'', 2, u'-b'], 6],
                     [[u'', 3, u'-', 2, u'-', 1, u'-tag-', 2, u'c'], 9],
                     [[u'', 3, u'-', 2, u'-', 3, u'-tag-', 2, u'a'], 3],
                     [[u'', 8, u'-b'], 3], [[u'', 8, u'-b-', 1, u''], 9],
                     [[u'a-', 1, u'-a', 2, u''], 3],
                     [[u'a-', 1, u'-a', 3, u''], 3],
                     [[u'a-', 1, u'-a', 3, u''], 12],
                     [[u'b-', 1, u'-a', 1, u''], 3],
                     [[u'b-', 1, u'-a', 1, u''], 3], [[u'tag-', 1, u''], 3],
                     [[u'tag-', 2, u''], 3], [[u'tag-', 2, u''], 9],
                     [[u'tag-', 3, u''], 3], [[u'tag-', 3, u''], 3],
                     [[u'tag-', 11, u''], 6], [[u'tag-', 12, u''], 9],
                     [[u'tag-', 21, u''], 9], [[u'tag-', 22, u''], 3]]
        tref = list(i for i, j in reference)
        dref = list(i for i, j in self._tagsdialog.itemDataMap)
        # print("tref = {0}\ndref = {1}\n".format(tref, dref))
        assert dref == tref
        # self._tagsdialog.show_dialog()

    def test_sort_tags_descending_value(self):
        self._tagsdialog.sort_state = (0, 1)
        # self.ShowDialog()
        self._tagsdialog.on_col_click(None)
        assert self._tagsdialog.sort_state == (0, 0)
        reference = [[[u'tag-', 22, u''], 3], [[u'tag-', 21, u''], 9],
                     [[u'tag-', 12, u''], 9], [[u'tag-', 11, u''], 6],
                     [[u'tag-', 3, u''], 3], [[u'tag-', 3, u''], 3],
                     [[u'tag-', 2, u''], 9], [[u'tag-', 2, u''], 3],
                     [[u'tag-', 1, u''], 3], [[u'b-', 1, u'-a', 1, u''], 3],
                     [[u'b-', 1, u'-a', 1, u''], 3],
                     [[u'a-', 1, u'-a', 3, u''], 12],
                     [[u'a-', 1, u'-a', 3, u''], 3],
                     [[u'a-', 1, u'-a', 2, u''], 3],
                     [[u'', 8, u'-b-', 1, u''], 9], [[u'', 8, u'-b'], 3],
                     [[u'', 3, u'-', 2, u'-', 3, u'-tag-', 2, u'a'], 3],
                     [[u'', 3, u'-', 2, u'-', 1, u'-tag-', 2, u'c'], 9],
                     [[u'', 2, u'-b'], 6]]
        tref = list(i for i, j in reference)
        dref = list(i for i, j in self._tagsdialog.itemDataMap)
        # print("tref = {0}\ndref = {1}\n".format(tref, dref))
        assert dref == tref
        # self._tagsdialog.show_dialog()


if __name__ == '__main__':
    unittest.main()
    app.Destroy()
