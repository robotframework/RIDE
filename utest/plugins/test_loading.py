import os
import unittest

from robotide.application.pluginloader import PluginLoader
from robotide.editor import Colorizer

from plugin_resources import FakeApplication


class TestPluginLoader(unittest.TestCase):

    def test_plugin_loading(self):
        plugins_dir = [os.path.join(os.path.dirname(__file__), 'plugins_for_loader')]
        loader = PluginLoader(FakeApplication(), plugins_dir, [Colorizer])
        self._assert_plugin_loaded(loader, 'Example Plugin 1')
        self._assert_plugin_loaded(loader, 'Example Plugin 2')
        self._assert_plugin_loaded(loader, 'Example Plugin 3')
        self._assert_plugin_loaded(loader, 'Colorizer')

    def _assert_plugin_loaded(self, loader, name):
        for p in loader.plugins:
            if p.name == name:
                return
        raise AssertionError("Plugin '%s' not loaded" % name)


if __name__ == "__main__":
    unittest.main()
