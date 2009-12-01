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

from robotide.application.pluginloader import PluginLoader
from robotide.editor import Colorizer

from resources import FakeApplication 


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
