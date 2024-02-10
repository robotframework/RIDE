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
import sys
import unittest

import pytest

from utest.resources import datafilereader


class TestImports(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = datafilereader.construct_project(datafilereader.IMPORTS)
        suite = cls.project.data.suites[1]
        # print("DEBUG: testimports setup suite: %s\n" % str(cls.project.data.suites))
        cls.imports = [i for i in suite.imports]
        # print("DEBUG: cls.imports setup suite: %s\n" % (cls.imports))

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def _find_by_name(self, name, data_file=None):
        data_file = data_file or self
        # print("DEBUG: find by name: %s\n" % (data_file.imports))
        for i in data_file.imports:
            # print("DEBUG: find by name: loop %s\n" % (i.name))
            if i.name == name:
                print(i.name)
                return i
        # print("DEBUG: find by name: AssertError %s\n" % (name))
        raise AssertionError('No import found with name "%s"' % name)

    def _has_error(self, name):
        self.assertTrue(self._find_by_name(name).has_error(), 'Import "%s" should have error' % name)

    def _has_no_error(self, name, data_file=None):
        self.assertFalse(self._find_by_name(name, data_file).has_error(), 'Import "%s" should have no error' % name)

    def test_importing_existing_resource_has_no_error(self):
        self._has_no_error('res//existing.robot')

    def test_importing_existing_library_from_pythonpath_has_no_error(self):
        self._has_no_error('String')

    def test_importing_existing_library_with_path_has_no_error(self):
        self._has_no_error('libs//existing.py')

    def test_importing_none_existing_resource_has_error(self):
        self._has_error('res//none_existing.robot')

    def test_importing_none_existing_variable_file_has_error(self):
        self._has_error('vars//none_existing.py')

    def test_importing_none_existing_library_has_error(self):
        self._has_error('libs//none_existing.py')

    def test_importing_corrupted_library_has_error(self):
        self._has_error('libs//corrupted.py')

    def test_resource_import_with_variable_has_no_error(self):
        self._has_no_error('${RESU}')

    def test_library_import_with_variable_has_no_error(self):
        self._has_no_error('${LIB}')

    @pytest.mark.skipif(sys.version_info >= (3, 12), reason="This test fails in Python 3.12")
    def test_variable_import_has_no_error(self):
        self._has_no_error('vars/vars.py')

    def test_library_import_in_subsuite_init_file_with_relative_path_has_no_error(self):
        self._has_no_error('..//outer_lib.py', self.project.data.suites[0])


if __name__ == '__main__':
    unittest.main()
