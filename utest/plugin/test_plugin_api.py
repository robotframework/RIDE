#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import unittest

from robotide.pluginapi import Plugin
from robotide.namespace import Namespace
from robotide.spec.iteminfo import ItemInfo
from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import data_controller
from utest.resources import FakeApplication
from robotide.spec.librarymanager import LibraryManager


class ContentAssistPlugin(Plugin):

    def _get_content_assist_values(self, item, value):
        assert item.name == None
        assert value == 'given'
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
        controller = data_controller(TestCaseFile(), None)
        for val in self.app.namespace.get_suggestions_for(controller, 'given'):
            if val.name == name:
                return
        raise AssertionError()


if __name__ == '__main__':
    unittest.main()

