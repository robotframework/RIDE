import unittest

import os
from robot.utils.asserts import assert_equal
from robotide.plugins.loader import PluginLoader


PLUGIN1_NAME='Example Plugin 1'
PLUGIN2_NAME='Example Plugin 2'
PLUGIN_DIR = "./test_plugins"


class _FakeModel(object):
    suite = None

class _FakeUIObject(object):
    Enable = InsertSeparator = Append = Connect = lambda *args: None
    Insert = FindMenu = GetMenuBar = GetMenu = lambda *args: _FakeUIObject()
    GetMenuItemCount = lambda s: 1
    notebook = property(lambda *args: _FakeUIObject())

class _FakeApplication(object):

    frame = _FakeUIObject()
    model = _FakeModel()
    get_model = lambda s: _FakeModel()
    subscribe = lambda s, x, y: None
    get_menu_bar = lambda s: _FakeUIObject()
    get_notebook = lambda s: _FakeUIObject()
    get_frame = lambda s: _FakeUIObject()
    create_menu_item = lambda *args: None


class TestablePluginLoader(PluginLoader):
    def _get_plugin_dirs(self):
        return [os.path.join(os.path.dirname(__file__), PLUGIN_DIR)]


class TestPluginLoader(unittest.TestCase):

    def test_plugin_loading(self):
        loader = TestablePluginLoader(_FakeApplication())
        assert_equal(len(loader.plugins), 6)
        self._assert_plugin_loaded(loader, PLUGIN1_NAME)
        self._assert_plugin_loaded(loader, PLUGIN2_NAME)
        self._assert_plugin_loaded(loader, 'Release Notes')

    def _assert_plugin_loaded(self, loader, name):
        for p in loader.plugins:
            if p.name == name:
                return
        raise AssertionError("Plugin '%s' not loaded" % name)


if __name__ == '__main__':
    unittest.main()
