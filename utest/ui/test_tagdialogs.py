import unittest
import mock

from robotide.ui.tagdialogs import ViewAllTagsDialog

from robotide.robotapi import (TestDataDirectory, TestCaseFile, ResourceFile,
                               TestCase, UserKeyword, robotide)
from nose.tools import assert_equals
from robotide.spec.librarymanager import LibraryManager
from robotide.ui.images import TreeImageList
from robotide.ui.mainframe import ActionRegisterer
from robotide.ui.actiontriggers import MenuBar, ToolBar, ShortcutRegistry
from robotide.ui.notebook import NoteBook

from robotide.application import Project
from robotide.controller.filecontrollers import (TestDataDirectoryController,
                                                 ResourceFileController)

from robotide import utils
from resources import PYAPP_REFERENCE, FakeSettings, FakeApplication
# import utest.resources

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


class _ViewAllTagsDialog(ViewAllTagsDialog):

    def __init__(self, frame, controller):
        style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN\
            | wx.FRAME_FLOAT_ON_PARENT
        self.frame = frame
        self.tree = self.frame.tree
        # print("DEBUG: init calling super\n")
        super(_ViewAllTagsDialog, self).__init__(self, self.frame)
        self._tags_list = utils.NormalizedDict()
        self._results = utils.NormalizedDict()
        self.itemDataMap = []
        self.sort_state = (0, 1)
        # print("DEBUG: Leaving init _ViewAllTagsDialog\n")

    def _search_for_tags(self):
        self._tags_list = {"tag-11":[1,2], "tag-02":[3], "tag-12":[4,8], "tag-2":[5,6,7], "tag-3":[9],
                           "tag-21":[10,11,12], "tag-12":[13], "tag-22":[10], "tag-1":[14], "tag-03":[15]}
        isreversed = (self.sort_state[1] != 1)
        self._results = sorted(self._tags_list.items(),
                               key=lambda item: item[0].lower,
                               reverse=isreversed)
        print("DEBUG: _search_for_tags {0}\n".format(self._results))

    def _execute(self):
        #self._clear_search_results()
        self._search_for_tags()

        self.tagged_test_cases = list()
        self.unique_tags = 0

        idx = 0
        for tag_name, tests in self._results:
            model_entry = idx
            self.tagged_test_cases += tests
            # Mapping the lists model entry with the model for sorting.
            self.itemDataMap.insert(model_entry, (self.tag_name_for_sort(tag_name), len(tests)) )
            self.unique_tags += 1
            idx += 1

        self.itemDataMap.sort(key=lambda item: item[0], reverse=self.sort_state[1])

    def show_dialog(self):
        self._execute()
        print("DEBUG: Unique tags {0}\n".format(self.unique_tags))
        print("DEBUG: _tags_list {0}\n".format(self.itemDataMap))

    def ShowDialog(self):
        self._tagsdialog._search_for_tags()
        self._tagsdialog._execute()
        self._tagsdialog.ShowModal()
        self._tagsdialog.Destroy()

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
        #frame = _FakeMainFrame()
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.tree = Tree(self.frame, ActionRegisterer(
            MenuBar(self.frame), ToolBar(self.frame), ShortcutRegistry(self.frame)))
        self.frame.Show()
        # print("DEBUG: setup tagsdialog\n")
        self._tagsdialog = _ViewAllTagsDialog(self.frame,self.frame)
        # print("DEBUG: Leaving setup\n")
        self._model = self._create_model()

    def tearDown(self):
        PUBLISHER.unsubscribe_all()
        wx.CallAfter(wx.Exit)
        self.app.MainLoop()

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
            suite, '%s Fake Test %d' % (suite.name, i)) for i in range(15)]
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
        self._tagsdialog.show_dialog()
        assert_equals(self._tagsdialog.sort_state, (0, 1))
        # self.ShowDialog()
        self._tagsdialog.show_dialog()

    def test_sort_tags_descending(self):
        assert_equals(self._tagsdialog.sort_state, (0, 1))
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (0, 0))
        self._tagsdialog.show_dialog()

    
if __name__ == '__main__':
    unittest.main()
