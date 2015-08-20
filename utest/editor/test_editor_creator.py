import unittest
import wx
import os
from mock import Mock
from nose.tools import assert_equals, assert_true

from robotide.robotapi import Variable
from robotide.controller import DataController
from robotide.controller.robotdata import NewTestCaseFile
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorCreator
from robotide.editor.editors import TestCaseFileEditor, WelcomePage
from editor.fakeplugin import FakePlugin

from resources import PYAPP_REFERENCE


DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR
TestCaseFileEditor._populate = lambda self: None

class EditorCreatorTest(unittest.TestCase):

    def setUp(self):
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()

    def tearDown(self):
        if os.path.exists(DATADIR):
            os.rmdir(DATADIR)

    def _register(self, iclass, eclass):
        self._registered_editors[iclass] = eclass

    def test_registering_editors_for_model_objects(self):
        assert_equals(len(self._registered_editors), len(self.creator._EDITORS))

    def test_creating_editor_for_datafile_controller(self):
        plugin = self._datafile_plugin()
        editor = self._editor_for(plugin)
        assert_true(isinstance(editor, TestCaseFileEditor))

    def _editor_for(self, plugin):
        return self.creator.editor_for(plugin, wx.Frame(None), None)

    def test_creating_editor_with_variable(self):
        plugin = self._variable_plugin()
        editor = self._editor_for(plugin)
        assert_true(isinstance(editor, TestCaseFileEditor))

    def test_creating_welcome_page_when_no_item(self):
        plugin = self._no_item_selected_plugin()
        editor = self._editor_for(plugin)
        assert_true(isinstance(editor, WelcomePage))

    def test_same_welcome_page_editor_instance_is_returned_if_called_multiple_times(self):
        plugin = self._no_item_selected_plugin()
        editor = self._editor_for(plugin)
        editor2 = self._editor_for(plugin)
        assert_equals(editor, editor2)

    def test_same_testcasefile_editor_instance_is_returned_if_called_multiple_times(self):
        plugin = self._variable_plugin()
        editor = self._editor_for(plugin)
        editor2 = self._editor_for(plugin)
        assert_equals(editor, editor2)

    def test_editor_is_recreated_when_controller_changes(self):
        p1 = self._datafile_plugin()
        p2 = self._datafile_plugin()
        e1 = self._editor_for(p1)
        e2 = self._editor_for(p2)
        assert_true(e1 is not e2)

    def test_editor_is_destroyed_when_new_is_created(self):
        ed = self._datafile_editor()
        ed.destroy = Mock()
        self._datafile_editor()
        assert_true(ed.destroy.called)

    def _datafile_editor(self):
        return self.creator.editor_for(self._datafile_plugin(),
                                       wx.Frame(None), None)

    def _datafile_plugin(self):
        return FakePlugin(self._registered_editors,
                          self._datafile_controller())

    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)

    def _datafile_controller(self):
        return DataController(NewTestCaseFile(DATAPATH), None)
