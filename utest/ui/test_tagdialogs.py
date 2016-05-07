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


class _ViewAllTagsDialog(ViewAllTagsDialog):

    def __init__(self,  frame, controller):
        style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN\
            | wx.FRAME_FLOAT_ON_PARENT
        self.frame = frame
        # self.tree = self.frame.tree
        self._controller = controller._controller
        # print("DEBUG: init calling super\n")
        super(_ViewAllTagsDialog, self).__init__(self, self.frame) #, self._controller)
        self.model = controller
        self._results = utils.NormalizedDict()
        self.itemDataMap = []
        self.sort_state = (0, 1)
        # print("DEBUG: model {0}\n".format(self.model._controller.display_name))
        # for i in self.model._controller.__dict__:
        #     print("DEBUG model {0}\n".format(i))
        # print("DEBUG: Leaving init _ViewAllTagsDialog\n")

    def _search_for_tags(self):
        unique_tags = utils.NormalizedDict()
        # self._tags = utils.NormalizedDict()
        # self._test_cases = []
        for i in self.model.suite.children: #testcase_table.tests:
            # print("DEBUG child {0}\n".format(i.name))
            for test in i.testcase_table.tests:
                # print("DEBUG test {0}\n".format(test.name))
                try:
                    for tag in getattr(test.tags, 'tags').split("    "):
                        # print("DEBUG: _search_for_tags tag {0}\n".format(tag))
                        if tag is None or len(unicode(tag).strip()) == 0:
                            continue
                        else:
                            tag_name = unicode(tag)
                        if tag_name in unique_tags:
                            unique_tags[tag_name].append(test)
                            # self._tags[tag_name].append(tag)
                        else:
                            unique_tags[tag_name] = [test]
                            # self._tags[tag_name] = [tag]
                except AttributeError:
                    pass
        isreversed = (self.sort_state[0] == 0 and self.sort_state[1] == 0)
        # self.total_test_cases = len(self._test_cases)
        self._results = sorted(unique_tags.items(),
                               key=lambda item: item[0].lower,
                               reverse=isreversed)

        #print("DEBUG: _search_for_tags {0}\n".format(self._results))

    def _execute(self):
        self._clear_search_results()
        self._search_for_tags()

        self.tagged_test_cases = list()
        self.unique_tags = 0

        idx = 0
        for tag_name, tests in self._results:
            model_entry = idx
            self.tagged_test_cases += tests
            # Mapping the lists model entry with the model for sorting.
            self.itemDataMap.insert(model_entry, (self._tag_name_for_sort(tag_name), len(tests)) )
            self.unique_tags += 1
            idx += 1
        isreversed = (self.sort_state[1] == 0)
        self.itemDataMap.sort(key=lambda item: item[self.sort_state[0]], reverse=isreversed)

    def show_dialog(self):
        # self._execute()
        print("DEBUG: Unique tags {0}\n".format(self.unique_tags))
        print("DEBUG: _tags_list {0}\n".format(self.itemDataMap))

    def ShowDialog(self):
        self._tagsdialog._search_for_tags()
        self._tagsdialog._execute()
        self._tagsdialog.ShowModal()
        self._tagsdialog.Destroy()

    def _clear_search_results(self):
        # self.selected_tests = list()
        self._results = {}
        self.itemDataMap = []

    def OnColClick(self):
        """
        Simulates clicking on Column (tag name or count), and toggle the
        sorting order.
        """
        if self.sort_state[0] == 0:
            self.sort_state = (0, (0 if self.sort_state[1] == 1 else 1))
        else:
            self.sort_state = (1, (0 if self.sort_state[1] == 1 else 1))
        self._execute()


class _BaseSuiteTreeTest(unittest.TestCase):

    def setUp(self):
        #frame = _FakeMainFrame()
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.frame.tree = Tree(self.frame, ActionRegisterer(
            MenuBar(self.frame), ToolBar(self.frame), ShortcutRegistry(self.frame)))
        self.frame.Show()
        self._tags_list = utils.NormalizedDict()
        self._tags_list = {"tag-11": [1, 2], "tag-02": [3], "tag-12": [4, 8, 13],
                           "tag-2": [5, 6, 7], "tag-3": [9],
                           "tag-21": [10, 11, 12], "tag-13": [13],
                           "tag-22": [10], "tag-1": [14], "tag-03": [15]}
        """
        self._tags_list = {"tag-a": [1], "tag-b": [2],
                           "tag-c": [3, 6, 8],
                           "tag-C": [3, 4, 5], "tag-B": [7, 3],
                           "tag-f": [8, 9, 10, 11], "tag-A": [12],
                           "tag-h": [1], "tag-i": [2], "tag-j": [15]}
        """
        self.model = self._create_model()
        # print("DEBUG: setup tagsdialog\n")
        self._tagsdialog = _ViewAllTagsDialog( self.frame, self.model)
        # print("DEBUG: Leaving setup\n")

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
            suite, '%s Fake Test %d' % (suite.name, i)) for i in range(16)]
        # Initialization of Tags
        count = 0
        for i in suite.testcase_table.tests:
            # Basic Tags
            # setattr(i.tags, 'tags', "tag-{0}{1}".format(count, ("    odd" if ((count % 2) == 0) else "" )))
            # OK print("DEBUG test {0} {1}\n".format(i.name, getattr(i.tags,'tags')))
            #if count != 0:
            #if suite.name == "Sub Suite 2":
            #    prefix = "02" if (count % 2) == 0 else "2"
            #    #print("DEBUG tags_list prefix {0}=at {1}\n".format(prefix, count))
            #else:
            #   prefix = ""
            newtag = ""
            for key, test in self._tags_list.iteritems():
                newtag += key + "    " if count in test else "" #.get(count)
                if len(newtag):
                    setattr(i.tags, 'tags', "{0}".format(newtag))
                # print("DEBUG tags_list {0}={1}\n".format(count, newtag))
            #else:
            #    setattr(i.tags, 'tags', "zero") # Test 0 must have tags attribute
            count += 1
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

    def test_sort_tags_ascending_count(self):
        self._tagsdialog.sort_state = (1, 0)
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (1, 1))
        reference = [((u'tag-', 2), 3), ((u'tag-', 3), 3), ((u'tag-', 1), 3), ((u'tag-', 13), 3), ((u'tag-', 3), 3), ((u'tag-', 22), 3), ((u'tag-', 11), 6), ((u'tag-', 12), 9), ((u'tag-', 21), 9), ((u'tag-', 2), 9)]
        cref = list(j for i, j in reference)
        # reference = [((u'tag-j', 0), 3), ((u'tag-i', 0), 3),
        #             ((u'tag-h', 0), 3), ((u'tag-a', 0), 6),
        #             ((u'tag-b', 0), 9), ((u'tag-f', 0), 12),
        #             ((u'tag-c', 0), 18)]
        dref = list(j for i, j in self._tagsdialog.itemDataMap)
        #print("cref = {0}\ndref = {1}\n".format(cref, dref))
        assert_equals(dref, cref)
        self._tagsdialog.show_dialog()

    def test_sort_tags_descending_count(self):
        self._tagsdialog.sort_state = (1, 1)
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (1, 0))
        reference = [((u'tag-', 21), 9), ((u'tag-', 2), 9), ((u'tag-', 12), 9), ((u'tag-', 11), 6), ((u'tag-', 3), 3), ((u'tag-', 1), 3), ((u'tag-', 13), 3), ((u'tag-', 3), 3), ((u'tag-', 22), 3), ((u'tag-', 2), 3)]
        cref = list(j for i, j in reference)
        dref = list(j for i, j in self._tagsdialog.itemDataMap)
        #print("cref = {0}\ndref = {1}\n".format(cref, dref))
        assert_equals(dref, cref)
        self._tagsdialog.show_dialog()

    def test_sort_tags_ascending_value(self):
        self._tagsdialog.sort_state = (0, 0)
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (0, 1))
        reference = [((u'tag-', 1), 3), ((u'tag-', 2), 3), ((u'tag-', 2), 9), ((u'tag-', 3), 3), ((u'tag-', 3), 3), ((u'tag-', 11), 6), ((u'tag-', 12), 9), ((u'tag-', 13), 3), ((u'tag-', 21), 9), ((u'tag-', 22), 3)]
        tref = list(i for i, j in reference)
        dref = list(i for i, j in self._tagsdialog.itemDataMap)
        #print("tref = {0}\ndref = {1}\n".format(tref, dref))
        assert_equals(dref, tref)
        self._tagsdialog.show_dialog()

    def test_sort_tags_descending_value(self):
        self._tagsdialog.sort_state = (0, 1)
        # self.ShowDialog()
        self._tagsdialog.OnColClick()
        assert_equals(self._tagsdialog.sort_state, (0, 0))
        reference = [((u'tag-', 22), 3), ((u'tag-', 21), 9), ((u'tag-', 13), 3), ((u'tag-', 12), 9), ((u'tag-', 11), 6), ((u'tag-', 3), 3), ((u'tag-', 3), 3), ((u'tag-', 2), 9), ((u'tag-', 2), 3), ((u'tag-', 1), 3)]
        #reference = [((u'tag-j', 0), 3), ((u'tag-i', 0), 3), ((u'tag-h', 0), 3), ((u'tag-f', 0), 12), ((u'tag-c', 0), 18), ((u'tag-b', 0), 9), ((u'tag-a', 0), 6)]
        tref = list(i for i, j in reference)
        dref = list(i for i, j in self._tagsdialog.itemDataMap)
        #print("tref = {0}\ndref = {1}\n".format(tref, dref))
        assert_equals(dref, tref)
        self._tagsdialog.show_dialog()

if __name__ == '__main__':
    unittest.main()
