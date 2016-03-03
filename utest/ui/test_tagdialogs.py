import unittest

from robotide.ui.tagdialogs import ViewAllTagsDialog

from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword)
from nose.tools import assert_equals
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.images import TreeImageList

from robotide.application import Project
from robotide.controller.filecontrollers import (TestDataDirectoryController,
                                                 ResourceFileController)

from robotide.ui.actiontriggers import MenuBar, ToolBar, ShortcutRegistry
from robotide.ui.mainframe import ActionRegisterer
from resources import PYAPP_REFERENCE, FakeSettings

from robotide.ui import tree as st
from robotide.ui import treenodehandlers as th
from robotide.publish import PUBLISHER
from robotide.namespace.namespace import Namespace
th.FakeDirectorySuiteHandler = th.FakeUserKeywordHandler = \
    th.FakeSuiteHandler = th.FakeTestCaseHandler = \
    th.FakeResourceHandler = th.TestDataDirectoryHandler
st.Editor = lambda *args: _FakeEditor()
from robotide.ui.tree import Tree
Tree._show_correct_editor = lambda self, x: None
Tree.get_active_datafile = lambda self: None
# CallAfter does not work in unit tests
Tree._select = lambda self, node: self.SelectItem(node)
# wx needs to imported last so that robotide can select correct wx version.
import wx


class _FakeMainFrame(wx.Frame):
    _editor_panel = None

    def __init__(self):
        self._tree = None

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


class ViewAllTagsDialog(wx.Frame, object):
    sort_state = (0, 1)

    def __init__(self, controller, frame):
        pass

    def _search_for_tags(self):
        pass

    def _execute(self):
        pass

    def OnColClick(self):
        """
        Simulates clicking on Column (tag name or count), and toggle the
        sorting order.
        """
        if self.sort_state[0] == 0:
            self.sort_state = (0, (0 if self.sort_state[1] == 1 else 1))
        else:
            self.sort_state = (1, (0 if self.sort_state[1] == 1 else 1))






class _BaseSuiteTreeTest(unittest.TestCase):

    def setUp(self):
        frame = _FakeMainFrame()
        self._model = self._create_model()
        self._tagsdialog = ViewAllTagsDialog(frame, None)
        self._tagsdialog._search_for_tags()
        self._tagsdialog._execute()

    def tearDown(self):
        PUBLISHER.unsubscribe_all()

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


class TestSortTags(_BaseSuiteTreeTest):

    def test_sort_tags_ascending(self):
        assert_equals(self._tagsdialog.sort_state, (0, 1))

    def test_sort_tags_descending(self):
        assert_equals(self._tagsdialog.sort_state, (0, 1))
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (0, 0))

if __name__ == '__main__':
    unittest.main()
