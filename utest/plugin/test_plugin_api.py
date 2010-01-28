import unittest
from robotide.pluginapi import Plugin
from robotide.namespace import Namespace, ContentAssistItem

from resources import FakeApplication, FakeSuite


class ContentAssistPlugin(Plugin):

    def _get_content_assist_values(self):
        return [ContentAssistItem('test', 'foo')]


class TestContentAssistHook(unittest.TestCase):

    def test_(self):
        self.app = FakeApplication()
        self.app.namespace = Namespace()
        pl = ContentAssistPlugin(self.app, name='test')
        pl.register_content_assist_hook(pl._get_content_assist_values)
        self._assert_contains('foo')

    def _assert_contains(self, name):
        for val in self.app.namespace.content_assist_values(FakeSuite()):
            if val.name == name:
                return
        raise AssertionError()



