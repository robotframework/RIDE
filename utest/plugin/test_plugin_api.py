import unittest
from robot.utils.asserts import assert_equals

from robotide.pluginapi import Plugin
from robotide.namespace import Namespace
from robotide.spec.iteminfo import _ItemInfo
from robotide.robotapi import TestCaseFile

from resources import FakeApplication


class ContentAssistPlugin(Plugin):

    def _get_content_assist_values(self, item, value):
        assert_equals(item.name, None)
        assert_equals(value, 'given')
        return [_ItemInfo('foo', 'test', 'quux')]


class TestContentAssistHook(unittest.TestCase):

    def test_(self):
        self.app = FakeApplication()
        self.app.namespace = Namespace()
        pl = ContentAssistPlugin(self.app, name='test')
        pl.register_content_assist_hook(pl._get_content_assist_values)
        self._assert_contains('foo')

    def _assert_contains(self, name):
        for val in self.app.namespace.get_suggestions_for(TestCaseFile(), 'given'):
            if val.name == name:
                return
        raise AssertionError()
