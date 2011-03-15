from resources import PYAPP_REFERENCE
import unittest
import wx
import os
from mock import Mock
from robot.utils.asserts import assert_equals, assert_true

from robotide.controller import NewDatafile, DataController
from robotide.editor.editors import EditorCreator
from robotide.editor.editors import TestCaseFileEditor

DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR
TestCaseFileEditor._populate = lambda self: None


class FakePlugin(object):
    def __init__(self, editors, item):
        self._editors = editors
        self._item = item
    def get_selected_item(self):
        return self._item
    def get_editor(self, itemclass):
        return self._editors[itemclass]
    def subscribe(self, *args):
        pass
    def unsubscribe(self, *args):
        pass


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
        assert_equals(len(self._registered_editors), 6)

    def test_creating_editor_for_datafile_controller(self):
        plugin = self._datafile_plugin()
        editor = self.creator.editor_for(plugin, wx.Frame(None), None)
        assert_true(isinstance(editor, TestCaseFileEditor))

    def test_editor_is_recreated_when_controller_changes(self):
        p1 = self._datafile_plugin()
        p2 = self._datafile_plugin()
        e1 = self.creator.editor_for(p1, wx.Frame(None), None)
        e2 = self.creator.editor_for(p2, wx.Frame(None), None)
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

    def _datafile_controller(self):
        return DataController(NewDatafile(DATAPATH, False), None)
