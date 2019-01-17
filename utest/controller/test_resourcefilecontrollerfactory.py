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
from robotide.controller.filecontrollers import ResourceFileControllerFactory


class ResourceFileControllerFactoryTestCase(unittest.TestCase):

    def setUp(self):
        namespace = lambda:0
        project = lambda:0
        self._resource_file_controller_factory = ResourceFileControllerFactory(namespace, project)

    def test_is_all_resource_imports_resolved(self):
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        self.assertTrue(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())
        self._resource_file_controller_factory.set_all_resource_imports_unresolved()
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        data = lambda:0
        data.source = 'source'
        data.directory = 'directory'
        self._resource_file_controller_factory.create(data)
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        resu = lambda:0
        self._resource_file_controller_factory._resources.append(resu)
        self._resource_file_controller_factory.remove(resu)
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())


if __name__ == '__main__':
    unittest.main()
