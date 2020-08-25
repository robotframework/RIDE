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

from wx._core import wxAssertionError

from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword)
from nose.tools import assert_equal
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.images import TreeImageList

from robotide.application import Project
from robotide.controller.filecontrollers import (TestDataDirectoryController,
                                                 ResourceFileController)

from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from resources import PYAPP_REFERENCE, FakeSettings

from robotide.ui import treeplugin as st
from robotide.ui import treenodehandlers as th
from robotide.publish import PUBLISHER
from robotide.namespace.namespace import Namespace
th.FakeDirectorySuiteHandler = th.FakeUserKeywordHandler = \
    th.FakeSuiteHandler = th.FakeTestCaseHandler = \
    th.FakeResourceHandler = th.TestDataDirectoryHandler
st.Editor = lambda *args: _FakeEditor()
from robotide.ui.treeplugin import Tree
Tree._show_correct_editor = lambda self, x: None
Tree.get_active_datafile = lambda self: None
# CallAfter does not work in unit tests
Tree._select = lambda self, node: self.SelectItem(node)
# wx needs to imported last so that robotide can select correct wx version.
import wx
from wx.lib.agw.aui import AuiManager


class _FakeMainFrame(wx.Frame):
    _editor_panel = None

    def publish(self, *args):
        pass


class _FakeImageList(wx.ImageList):
    def __init__(self):
        wx.ImageList.__init__(self, 16, 16)
        self._image = _FakeImage(self)

    def __getitem__(self, name):
        return self._image


class _FakeImage(object):
    def __init__(self, imglist):
        self.normal = self.expanded = \
            imglist.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER,
                                                 (16, 16)))


class _FakeEditor(object):
    view = close = lambda *args: None


class _BaseSuiteTreeTest(unittest.TestCase):

    def setUp(self):
        # frame = _FakeMainFrame(None)
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self._model = self._create_model()
        self._tree = Tree(self.frame, ActionRegisterer(AuiManager(self.frame),
            MenuBar(self.frame), ToolBar(self.frame), ShortcutRegistry(self.frame)))
        images = TreeImageList()
        self._tree._images = images
        self._tree.SetImageList(images)
        self._tree.populate(self._model)
        self._expand_all()

    def tearDown(self):
        PUBLISHER.unsubscribe_all()
        wx.CallAfter(wx.Exit)
        self.app.MainLoop()  # With this here, there is no Segmentation fault

    def _create_model(self):
        suite = self._create_directory_suite('/top_suite')
        suite.children = [self._create_file_suite('sub_suite_%d.txt' % i)
                          for i in range(3)]
        res = ResourceFile()
        res.source = 'resource.txt'
        res.keyword_table.keywords.append(UserKeyword(res, 'Resource Keyword'))
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        model = Project(
            Namespace(FakeSettings()), library_manager=library_manager)
        model._controller = TestDataDirectoryController(suite)
        rfc = ResourceFileController(res, project=model)
        model.resources.append(rfc)
        model.insert_into_suite_structure(rfc)
        return model

    def _create_directory_suite(self, source):
        return self._create_suite(TestDataDirectory, source, is_dir=True)

    def _create_file_suite(self, source):
        suite = self._create_suite(TestCaseFile, source)
        suite.testcase_table.tests = [TestCase(
            suite, '%s Fake Test %d' % (suite.name, i)) for i in range(5)]
        return suite

    def _create_suite(self, suite_class, source, is_dir=False):
        suite = suite_class()
        suite.source = source
        if is_dir:
            suite.directory = source
        suite.keyword_table.keywords = [
            UserKeyword(suite.keyword_table, '%s Fake UK %d' % (suite.name, i))
            for i in range(5)]
        return suite

    def _expand_all(self):
        for node in self._tree._datafile_nodes[1:]:
            self._tree._expand_and_render_children(node)

    def _get_selected_label(self):
        return self._tree.GetItemText(self._tree.GetSelection())

    def _get_node(self, label):
        node = self._tree._controller.find_node_with_label(
            self._tree._root, label)
        return node or self._tree._controller.find_node_with_label(
            self._tree._root, '*' + label)

    def _select_node(self, label):
        self._tree.SelectItem(self._get_node(label))


class TestPopulating(_BaseSuiteTreeTest):

    def test_suite_count_and_names(self):
        assert_equal(len(self._tree._datafile_nodes), 5)
        for idx, name in enumerate(['Top Suite'] +
                                   ['Sub Suite %d' % i for i in range(3)]):
            assert_equal(
                self._tree.GetItemText(self._tree._datafile_nodes[idx]), name)

    def test_file_suite_has_correct_subnodes(self):
        file_suite = self._tree._datafile_nodes[1]
        self._assert_children(file_suite, ['Sub Suite 0 Fake Test 0'])

    def _assert_children(self, parent, children):
        item, cookie = self._tree.GetFirstChild(parent)
        assert_equal(self._tree.GetItemText(item), children[0])
        for name in children[1:]:
            item, cookie = self._tree.GetNextChild(parent, cookie)
            assert_equal(self._tree.GetItemText(item), name)

class TestAddingItems(_BaseSuiteTreeTest):

    def test_adding_user_keyword(self):
        suite = self._model.data
        kw = suite.create_keyword('New Fake UK')
        self._tree.add_keyword(self._get_node(suite.name), kw)
        assert_equal(self._get_selected_label(), 'New Fake UK')

    def test_adding_test(self):
        suite = self._model.data.children[0]
        create_test = suite.create_test('New Fake Test')
        self._tree.add_test(self._get_node(suite.name), create_test)
        assert_equal(self._get_selected_label(), 'New Fake Test')


class TestNodeSearchAndSelection(_BaseSuiteTreeTest):

    def test_topsuite_node_should_be_selected_by_default(self):
        assert_equal(self._get_selected_label(), '')

    def test_searching_matching_uk_node(self):
        self._select_and_assert_selection(self._model.data.keywords[0].data)
        self._select_and_assert_selection(
            self._model.data.children[1].keywords[2].data)

    def _select_and_assert_selection(self, uk):
        self._tree.select_user_keyword_node(uk)
        assert_equal(self._get_selected_label(), uk.name)

    def test_get_active_suite_or_resource(self):
        exp = [('Top Suite Fake UK 2', 'Top Suite'),
               ('Sub Suite 1 Fake Test 1', 'Sub Suite 1'),
               ('Resource Keyword', 'Resource')]
        for node, parent_name in exp:
            self._select_node_and_assert_parent(node, parent_name)

    def _select_node_and_assert_parent(self, label, expected_parent_name):
        self._select_node(label)
        suite_or_resource = self._tree.get_selected_datafile()
        assert_equal(suite_or_resource.name, expected_parent_name)


class TestNodeRemoval(_BaseSuiteTreeTest):

    def test_removing_user_keyword(self):
        name = self._model.data.children[1].keywords[1].name
        root = self._tree._root
        count = self._tree.GetChildrenCount(self._tree._root)
        self._tree.Delete(
            self._tree._controller.find_node_with_label(root, name))
        assert_equal(count - 1, self._tree.GetChildrenCount(self._tree._root))


class TestRefreshingDataNode(_BaseSuiteTreeTest):

    def test_refreshing_suite(self):
        orig_node_lenght = len(self._tree._datafile_nodes)
        new_name = 'Modified name'
        suite = self._model.data.children[0]
        suite.tests[0].rename(new_name)
        self._tree.refresh_datafile(suite, None)
        self._expand_all()
        snode = self._get_node(suite.display_name)
        tnode = self._tree.GetFirstChild(snode)[0]
        assert_equal(self._tree.GetItemText(tnode), new_name)
        assert_equal(orig_node_lenght, len(self._tree._datafile_nodes))

    def test_refreshing_resource(self):
        orig_node_lenght = len(self._tree._datafile_nodes)
        new_name = 'Ninjaed Uk Name'
        resource = self._model.resources[0]
        resource.keywords[0].rename(new_name)
        self._tree.refresh_datafile(resource, None)
        self._expand_all()
        rnode = self._get_node(resource.display_name)
        knode = self._tree.GetFirstChild(rnode)[0]
        assert_equal(self._tree.GetItemText(knode), new_name)
        assert_equal(orig_node_lenght, len(self._tree._datafile_nodes))


if __name__ == '__main__':
    unittest.main()
