#  Copyright 2008 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import unittest
from robot.utils.asserts import assert_true, assert_false

import robotide.context
class _Log(object):
    def __init__(self):
        self.log = ''
    def error(self, msg):
        self.log += msg

LOGGER = _Log()
robotide.context.LOG = LOGGER


from robotide.application.pluginloader import PluginLoader
from robotide.editor.gridcolorizer import Colorizer

from resources import FakeApplication, FakeSettings

robotide.application.pluginconnector.SETTINGS = FakeSettings()


class TestPluginLoader(unittest.TestCase):
    expected_plugins = ['Example Plugin 1', 'Example Plugin 2',
                        'Example Plugin 3', 'Colorizer']

    def setUp(self):
        plugins_dir = [os.path.join(os.path.dirname(__file__), 'plugins_for_loader')]
        app = FakeApplication()
        self.loader = PluginLoader(app, plugins_dir, [Colorizer])
        app.get_plugins = lambda: self.loader.plugins

    def tearDown(self):
        for p in self.loader.plugins:
            p.disable()

    def test_plugin_loading(self):
        for name in self.expected_plugins:
            self._assert_plugin_loaded(name)
        assert_false(LOGGER.log)

    def _assert_plugin_loaded(self, name):
        for p in self.loader.plugins:
            if p.name == name:
                return
        raise AssertionError("Plugin '%s' not loaded" % name)

    def test_plugins_are_not_enabled_when_loaded(self):
        for p in self.loader.plugins:
            assert_false(p.enabled)

    def test_plugins_can_be_enabled(self):
        self.loader.enable_plugins()
        for p in self.loader.plugins:
            assert_true(p.enabled, 'Plugin %s was not enabled' % p.name)

    def test_plugins_can_disable_other_plugins(self):
        self.loader.enable_plugins()
        self._get_plugin_by_name('Example Plugin 2')._plugin.turn_off('Example Plugin 1')
        assert_false(self._get_plugin_by_name('Example Plugin 1').enabled)

    def _get_plugin_by_name(self, name):
        for p in self.loader.plugins:
            if p.name == name:
                return p
        return None


if __name__ == "__main__":
    unittest.main()
