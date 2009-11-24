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
import sys
import unittest

from robot.utils.normalizing import _CASE_INSENSITIVE_FILESYSTEM

from robotide.application import DataModel
from robotide.model import cache
from robotide import context
from resources import COMPLEX_SUITE_PATH, VARS_SUITE_PATH, PATH_RESOURCE_NAME


COMPLEX_MODEL = DataModel(COMPLEX_SUITE_PATH)
COMPLEX_SUITE = COMPLEX_MODEL.suite
VARS_SUITE = DataModel(VARS_SUITE_PATH).suite

class APPMock(object):

    def import_new_resource(self, datafile, path):
        self.datafile = datafile
        self.path = path

APP_MOCK = APPMock()
context.APP = APP_MOCK


class TestGettingKeywords(unittest.TestCase):
    
    def setUp(self):
        self.suite = DataModel(VARS_SUITE_PATH).suite

    def test_own_user_keywords(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 
                              'My Test Setup', COMPLEX_SUITE.name)

    def test_own_keyword_for_content_assist(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(), 
                              'My Test Setup', '<this file>')

    def test_keywords_from_imports(self):
        for name, source in [('Resource UK', 'resource.html'), 
                             ('Another Resource UK', 'another_resource.html'),
                             ('File Should Exist', 'OperatingSystem')]:
            self._assert_contains(COMPLEX_SUITE.get_keywords(), name, source)

    def test_keywords_from_resource_in_python_path(self):
        for name, source in [('Path Resource UK', PATH_RESOURCE_NAME),
                             ('Lists Should Be Equal', 'Collections')]:
            self._assert_contains(COMPLEX_SUITE.get_keywords(), name, source)

    def test_keywords_from_spec_resource(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 
                              'Attributeless Keyword', 'Spec Resource')

    def test_keywords_from_spec_library(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Testlib Keyword', 'TestLib')

    def test_filtering_keywords_with_longnames(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(name='BuiltIn.Catenate'),
                              'Catenate', 'BuiltIn')
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(name='Catenate'),
                              'Catenate', 'BuiltIn')

    def test_changing_keywords_in_suite_affects_returned_keywords(self):
        COMPLEX_SUITE.keywords.new_keyword('New Keyword')
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 'New Keyword', COMPLEX_SUITE.name)

    def test_changing_keywords_in_resource_affects_returned_keywords(self):
        resource = COMPLEX_SUITE.get_resources()[0]
        resource.keywords.new_keyword('New UK')
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 'New UK', resource.name)

    def test_get_all_keywords(self):
        for name, source in [('My Test Setup', 'Everything'), 
                             ('Resource UK', 'resource.html'),
                             ('Another Resource UK', 'another_resource.html')]:
            self._assert_contains(COMPLEX_MODEL.get_all_keywords(), name, source)
        COMPLEX_SUITE.keywords.new_keyword('New Suite UK')
        self._assert_contains(COMPLEX_MODEL.get_all_keywords(), 'New Suite UK', 'Everything')

    def test_finding_keywords_from_libary_defined_as_variable(self):
        self._assert_contains(VARS_SUITE.get_keywords(), 'List Should Contain Value', 'Collections')

    def test_variables_in_import_settings_are_case_insensitive(self):
        self._assert_contains(VARS_SUITE.get_keywords(), 'File Should Exist', 'OperatingSystem')

    def test_variables_from_other_imports_can_be_used(self):
        self._assert_contains(VARS_SUITE.get_keywords(), 'Open Connection', 'Telnet')

    def test_added_resource_affects_found_keywords_in_kw_completion(self):
        self._robot_2_1_1_required()
        VARS_SUITE.settings.imports.new_resource('resources/resources2/even_more_resources.txt')
        self._assert_contains(VARS_SUITE.get_keywords(), 'Foo', 'even_more_resources.txt')

    def test_updated_resource_affects_found_keywords_in_kw_completion(self):
        self._robot_2_1_1_required()
        self.suite.settings.imports.new_resource('resources/resources2/resources.txt')
        self._assert_does_not_contain(self.suite.get_keywords(), 'Foo', 'even_more_resources.txt')
        self.suite.settings.imports[-1].set_str_value('resources/resources2/even_more_resources.txt')
        self._assert_contains(self.suite.get_keywords(), 'Foo', 'even_more_resources.txt')

    def test_removed_resource_affects_found_keywords_in_kw_completion(self):
        self.test_added_resource_affects_found_keywords_in_kw_completion()
        self.suite.settings.imports.pop(-1)
        self._assert_does_not_contain(self.suite.get_keywords(), 'Foo', 'even_more_resources.txt')

    def test_added_resource_path_is_normalized_in_case_insensitive_file_systems(self):
        self.suite.settings.imports.new_resource('Resources/Resources2/Even_More_Resources.txt')
        if _CASE_INSENSITIVE_FILESYSTEM:
            self._assert_contains(self.suite.get_keywords(), 'Foo', 'even_more_resources.txt')
        else:
            self._assert_does_not_contain(self.suite.get_keywords(), 'Foo', 'even_more_resources.txt')

    def test_added_library_affects_found_keywords_in_kw_completion(self):
        self.suite.settings.imports.new_library('Dialogs')
        self._assert_contains(self.suite.get_keywords(), 'Execute Manual Step', 'Dialogs')

    def test_updated_library_affects_found_keywords_in_kw_completion(self):
        self.suite.settings.imports.new_library('InvalidDialogs')
        self._assert_does_not_contain(self.suite.get_keywords(), 'Execute Manual Step', 'Dialogs')
        self.suite.settings.imports[-1].set_str_value('Dialogs')
        self._assert_contains(self.suite.get_keywords(), 'Execute Manual Step', 'Dialogs')

    def test_failed_library_affects_found_keywords_in_kw_completion(self):
        self.test_added_library_affects_found_keywords_in_kw_completion()
        self.suite.settings.imports.pop(-1)
        self._assert_does_not_contain(self.suite.get_keywords(), 'Execute Manual Step', 'Dialogs')

    def _assert_contains(self, keywords, name, source):
        for kw in keywords:
            if kw.name == name:
                if kw.source == source:
                    return
                raise AssertionError("Keyword '%s' had wrong source: '%s' != '%s'"
                                     % (kw.name, kw.source, source))
        raise AssertionError("Keyword '%s' not found in suite or resource\n"
                             "Imported libs: %s\n"
                             % (name, [lib for lib in cache.LIBRARYCACHE.libraries]))

    def _assert_does_not_contain(self, keywords, name, source):
        for kw in keywords:
            if kw.name == name and kw.source == source:
                raise AssertionError("Keyword '%s' found from source %s\n" % (name, source))

    def _robot_2_1_1_required(self):
        try:
            import robot.parsing.txtreader
        except ImportError:
            raise AssertionError("Robot 2.1.1 or newer required to run this test.")


class TestGettingVariablesFromAssistant(unittest.TestCase):

    def setUp(self):
        self.suite = DataModel(VARS_SUITE_PATH).suite

    def test_get_variables_for_suite(self):  
        self._assert_variable(COMPLEX_SUITE, '${SCALAR}')

    def test_get_variables_from_resource_files(self):
        for name in ['${SCALAR}', '@{LIST}', '${RESOURCE var}',
                     '@{RESOURCE 2 List VARIABLE}']:
            self._assert_variable(COMPLEX_SUITE, name)

    def test_finding_variables_from_variable_file(self):
        self._assert_variable(self.suite, '${var_from_file}')

    def test_finding_variables_from_variable_file_importes_in_resource(self):
        self._assert_variable(self.suite, '${var_from_resource_var_file}')

    def test_variables_are_resolved_before_passed_to_variable_files(self):
        self._assert_variable(self.suite, '${value}')

    def test_added_variable_file_affects_found_variables_in_variable_completion(self):
        self.suite.settings.imports.new_variables('resources/resources2/even_more_varz.py')
        self._assert_variable(self.suite, '${var_in_resource2}')

    def test_updated_variable_file_affects_found_variables_in_variable_completion(self):
        self.suite.settings.imports.new_variables('invalid.py')
        self._assert_variable_does_not_exist(self.suite, '${var_in_resource2}')
        self.suite.settings.imports[-1].set_str_value('resources/resources2/even_more_varz.py')
        self._assert_variable(self.suite, '${var_in_resource2}')

    def test_deleted_variable_file_affects_found_variables_in_variable_completion(self):
        self.suite.settings.imports.new_variables('resources/resources2/even_more_varz.py')
        self._assert_variable(self.suite, '${var_in_resource2}')
        self.suite.settings.imports.pop(-1)
        self._assert_variable_does_not_exist(self.suite, '${var_in_resource2}')

    def test_variable_file_in_pythonpath_affects_found_variables_in_variable_completion(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'robotdata', 'resources', 'resources2')
        sys.path.append(path)
        self.suite.settings.imports.new_variables('even_more_varz.py')
        self._assert_variable(self.suite, '${var_in_resource2}')

    def _assert_variable(self, suite, name):
        variables = [ var.name for var in suite.get_variables() ]
        if not name in variables:
            raise AssertionError("Variable '%s' not found in %s" % 
                                (name, variables))

    def _assert_variable_does_not_exist(self, suite, name):
        variables = [ var.name for var in suite.get_variables() ]
        if name in variables:
            raise AssertionError("Variable '%s' found in %s" % 
                                (name, variables))


if __name__ == '__main__':
    unittest.main()

