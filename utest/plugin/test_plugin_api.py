import unittest
from nose.tools import assert_equals

from robotide.pluginapi import Plugin
from robotide.namespace import Namespace
from robotide.spec.iteminfo import ItemInfo
from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import DataController

from resources import FakeApplication
from robotide.spec.librarymanager import LibraryManager


class ContentAssistPlugin(Plugin):

    def _get_content_assist_values(self, item, value):
        assert_equals(item.name, None)
        assert_equals(value, 'given')
        return [ItemInfo('foo', 'test', 'quux')]


class TestContentAssistHook(unittest.TestCase):

    def test_hook_suggestions_are_included(self):
        self.app = FakeApplication()
        self.app.namespace = Namespace(self.app.settings)
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        library_manager.start()
        self.app.namespace.set_library_manager(library_manager)
        pl = ContentAssistPlugin(self.app, name='test')
        pl.register_content_assist_hook(pl._get_content_assist_values)
        self._assert_contains('foo')
        library_manager.stop()

    def _assert_contains(self, name):
        controller = DataController(TestCaseFile(), None)
        for val in self.app.namespace.get_suggestions_for(controller, 'given'):
            if val.name == name:
                return
        raise AssertionError()
