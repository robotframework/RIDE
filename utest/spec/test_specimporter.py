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
from robotide.spec.specimporter import SpecImporterPlugin
from robotide.utils import overrides


class PartiallyMockedSpecImporter(SpecImporterPlugin):

    def __init__(self, is_valid_path):
        self.__is_valid_path = is_valid_path
        self.spec_stored = False
        self.namespace_update_executed = False

    @overrides(SpecImporterPlugin)
    def _get_path_to_library_spec(self):
        return 'somepath.xml'

    @overrides(SpecImporterPlugin)
    def _is_valid_path(self, path):
        return self.__is_valid_path

    @overrides(SpecImporterPlugin)
    def _store_spec(self, path):
        self.spec_stored = True

    @overrides(SpecImporterPlugin)
    def _execute_namespace_update(self):
        self.namespace_update_executed = True


class TestSpecImporter(unittest.TestCase):

    def test_execute_spec_importer(self):
        spec_importer = PartiallyMockedSpecImporter(True)
        spec_importer.execute_spec_import()
        self.assertTrue(spec_importer.spec_stored)
        self.assertTrue(spec_importer.namespace_update_executed)

    def test_execute_spec_importer_with_invalid_path(self):
        spec_importer = PartiallyMockedSpecImporter(False)
        spec_importer.execute_spec_import()
        self.assertFalse(spec_importer.spec_stored)
        self.assertFalse(spec_importer.namespace_update_executed)


if __name__ == '__main__':
    unittest.main()
