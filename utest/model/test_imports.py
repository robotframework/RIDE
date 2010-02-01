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

import unittest
from robot.utils.asserts import assert_equals

from robotide.model.tables import ImportSettings
from robotide.model.files import _TestSuiteFactory
from robotide.robotapi import TestSuiteData
from robotide.namespace import Namespace
from robotide import context

from resources import COMPLEX_SUITE_PATH


class APPMock(object):
    def import_new_resource(self, datafile, path):
        self.datafile = datafile
        self.path = path

context.APP = APPMock()
PARSED_DATA = TestSuiteData(COMPLEX_SUITE_PATH)
EVEN_MORE_PATH = '../resources/more_resources/even_more_resources.txt'


class _ParsedImport(object):
    """Imitates import setting in test data parsed by RF."""
    def __init__(self, name, item):
        self.name = name
        self._item = item

class _ImportItem(object):
    def __init__(self, value):
        self.value = value


class TestAutomaticHandlingOfFileSeparatorVariable(unittest.TestCase):
    """'${/}' should be converted to '/' in import setting names, since RF
    supports the latter both in Windows and Linux.
    """
    def setUp(self):
        self._imports = ImportSettings(datafile=None, data=
                [_ParsedImport('Library', _ImportItem(['${/}some${/}path'])),
                 _ParsedImport('Resource', _ImportItem(['..${/}resources'])),
                 _ParsedImport('Variables', _ImportItem(['vars${/}first.py',
                                                         'arg${/}value']))
                 ])

    def test_path_separator_variable_is_replaces(self):
        assert_equals(self._imports[0].name, '/some/path')
        assert_equals(self._imports[1].name, '../resources')
        assert_equals(self._imports[2].name, 'vars/first.py')

    def test_variable_is_not_replaced_in_arguments(self):
        assert_equals(self._imports[2].args, ['arg${/}value'])


class TestResolvingKeywords(unittest.TestCase):

    def setUp(self):
        self.imports = _TestSuiteFactory(PARSED_DATA, Namespace()).imports

    def test_normal_library_import(self):
        self._should_contain_keyword('File Should Exist', 'OperatingSystem')

    def test_library_import_defined_as_variable(self):
        self._should_contain_keyword('Create Dictionary', 'Collections')

    def test_variables_from_resource_files_may_be_used_to_import_libs(self):
        self._should_contain_keyword('File Should Exist', 'OperatingSystem')

    def test_variables_from_variable_files_may_be_used_to_import_libs(self):
        self._should_contain_keyword('Execute Command', 'Telnet')

    def test_library_imported_in_resource(self):
        self._should_contain_keyword('Longest', 'AnotherArgLib')

    def test_library_taking_arguments(self):
        self._should_contain_keyword('Get Mandatory', 'ArgLib')

    def test_library_spec_file(self):
        self._should_contain_keyword('Attributeless Keyword',
                                     'LibSpecLibrary')

    def test_library_imports_are_case_insensitive(self):
        self._should_not_contain_keyword('Open Connection', 'SeleniumLibrary')

    def test_adding_library(self):
        self.imports.new_library('Dialogs')
        self._should_contain_keyword('Execute Manual Step', 'Dialogs')

    def test_updating_library(self):
        self.imports.new_library('InvalidDialogs')
        self._should_not_contain_keyword('Execute Manual Step', 'Dialogs')
        self.imports[-1].set_str_value('Dialogs')
        self._should_contain_keyword('Execute Manual Step', 'Dialogs')

    def test_resource_file(self):
        self._should_contain_keyword('Resource UK', 'resource.html')

    def test_chained_resource_file(self):
        self._should_contain_keyword('Resource2 UK', 'resource2.html')
        self._should_contain_keyword('Resource3 UK', 'resource3.html')
        self._should_contain_keyword('UK From Text Resource', 'resource.txt')

    def test_resource_import_with_variables(self):
        self._should_contain_keyword('Another Resource UK',
                                     'another_resource.html')

    def test_vars_from_resources_are_used_to_resolve_resource_imports(self):
        self._should_contain_keyword('Resource4 UK', 'resource4.html')

    def test_resource_in_pythonpath(self):
        self._should_contain_keyword('Path Resource UK', 'PathResource.html')

    def test_resource_spec_file(self):
        self._should_contain_keyword('Attributeless Keyword',
                                     'Spec Resource')

    def test_adding_resource_import(self):
        self.imports.new_resource(EVEN_MORE_PATH)
        self._should_contain_keyword('Foo', 'even_more_resources.txt')

    def test_updating_resource_import(self):
        self.imports.new_resource('invalid/path')
        self.imports[-1].set_str_value(EVEN_MORE_PATH)

    def test_removing_resource_import(self):
        self.test_adding_resource_import()
        self.imports.pop(-1)
        self._should_not_contain_keyword('Foo', 'even_more_resources.txt')

    def test_path_is_normalized_in_case_insensitive_file_systems(self):
        from robot.utils.normalizing import _CASE_INSENSITIVE_FILESYSTEM
        path = '../Resources/More_ResourceS/Even_More_Resources.txt'
        self.imports.new_resource(path)
        if _CASE_INSENSITIVE_FILESYSTEM:
            self._should_contain_keyword('Foo','even_more_resources.txt')
        else:
            self._should_not_contain_keyword('Foo', 'even_more_resources.txt')

    def _should_contain_keyword(self, name, source):
        if not self._contains(self.imports.get_keywords(), name, source):
            raise AssertionError('Keyword "%s" not found' % name)

    def _should_not_contain_keyword(self, name, source):
        if self._contains(self.imports.get_keywords(), name, source):
            raise AssertionError('Keyword "%s" found' % name)

    def _contains(self, items, name, source):
        for it in items:
            if it.name == name and it.source == source:
                return True
        return False


class TestResolvingVariables(unittest.TestCase):

    def setUp(self):
        self.imports = _TestSuiteFactory(PARSED_DATA, Namespace()).imports

    def test_vars_from_resource_files(self):
        for name, source in [('${RESOURCE var}', 'resource.html'),
                             ('@{RESOURCE 2 List VARIABLE}', 'resource2.html')]:
            self._should_contain_variable(name, source)

    def test_variable_file(self):
        self._should_contain_variable('${var_from_file}', 'varz.py')

    def test_variable_file_in_resource(self):
        self._should_contain_variable('${var_from_resource_var_file}', 'res_var_file.py')

    def test_variables_are_resolved_before_passed_to_variable_files(self):
        self._should_contain_variable('${value}', 'dynamic_varz.py')

    def _should_contain_variable(self, name, source):
        if not self._contains(self.imports.get_variables(), source, name):
            raise AssertionError('Variable "%s" not found' % name)

    def _contains(self, items, exp_source, exp_name):
        for source, name in items:
            if name == exp_name and source == exp_source:
                return True
        return False


if __name__ == '__main__':
    unittest.main()

