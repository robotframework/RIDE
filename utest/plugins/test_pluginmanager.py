import unittest

import os
from robot.utils.asserts import assert_equal, assert_true, assert_false
from robotide.application.pluginmanager import PluginLoader


PLUGIN1_ID='test.plugin1'
PLUGIN2_ID='test.plugin2'
PLUGIN_DIR = "./test_plugins"


class _FakeModel(object):
    suite = None

class _FakeUIObject(object):
    FindMenu = Insert = InsertSeparator = Append = Connect =\
        lambda *args: None
    GetMenu = lambda s, x: _FakeUIObject()
    GetMenuItemCount = lambda s: 1

class _FakeManager(object):

    get_model = lambda s: _FakeModel()
    subscribe = lambda s, x, y: None
    get_menu_bar = lambda s: _FakeUIObject()
    get_notebook = lambda s: _FakeUIObject()
    get_frame = lambda s: _FakeUIObject()
    create_menu_item = lambda *args: None


class TestPluginLoader(unittest.TestCase):

    def setUp(self):
        self.pm = PluginLoader(manager=_FakeManager(),
                                dirs=[os.path.join(os.path.dirname(__file__), PLUGIN_DIR)])
    
    def test_activate_all(self):
        """This test loads and activates all plugins that it finds.

           This test depends expects two valid plugins to be in the 
           test_plugins directory. There should also be at least one
           non-plugin file in that directory too.
        """
        assert_equal(len(self.pm.plugins), 0)
        self.pm.load_plugins()
        assert_equal(len(self.pm.plugins), 7)
        assert_equal(self.pm.plugins[PLUGIN1_ID].id, "test.plugin1")
        assert_equal(self.pm.plugins[PLUGIN1_ID].name, "Test Plugin 1")
        assert_false(self.pm.plugins[PLUGIN1_ID].active, "expected %s to be active but it is not")
        assert_equal(self.pm.plugins[PLUGIN2_ID].id, "test.plugin2")
        assert_equal(self.pm.plugins[PLUGIN2_ID].name, "Test Plugin 2")
        assert_true(self.pm.plugins[PLUGIN2_ID].active, "expected %s to be active but it is not")

    def test_finding_core_plugins(self):
        self.pm.load_plugins()
        assert_true(self.pm.plugins['releasenotes'].active)


if __name__ == '__main__':
    unittest.main()
