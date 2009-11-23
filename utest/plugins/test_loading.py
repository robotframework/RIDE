import os
import unittest

from robotide.application.pluginloader import PluginLoader
from robotide.application.releasenotes import ReleaseNotesPlugin
ReleaseNotesPlugin.auto_show = lambda *args: None

from plugin_resources import FakeApplication


class TestablePluginLoader(PluginLoader):
    def _get_plugin_dirs(self):
        return [os.path.join(os.path.dirname(__file__), 'plugins_for_loader')]

class TestPluginLoader(unittest.TestCase):

    def test_plugin_loading(self):
        loader = TestablePluginLoader(FakeApplication(), '.', [])
        self._assert_plugin_loaded(loader, 'Example Plugin 1')
        self._assert_plugin_loaded(loader, 'Example Plugin 2')
        self._assert_plugin_loaded(loader, 'Example Plugin 3')
        self._assert_plugin_loaded(loader, 'Release Notes')

    def _assert_plugin_loaded(self, loader, name):
        for p in loader.plugins:
            if p.name == name:
                return
        raise AssertionError("Plugin '%s' not loaded" % name)


if __name__ == "__main__":
    unittest.main()
