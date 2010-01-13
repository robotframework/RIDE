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
from resources import COMPLEX_SUITE_PATH, PATH_RESOURCE_NAME


COMPLEX_MODEL = DataModel(COMPLEX_SUITE_PATH)
COMPLEX_SUITE = COMPLEX_MODEL.suite


class APPMock(object):

    def import_new_resource(self, datafile, path):
        self.datafile = datafile
        self.path = path

APP_MOCK = APPMock()
context.APP = APP_MOCK


class _ContentAssistBaseTest(unittest.TestCase):

    def _assert_contains(self, keywords, name, source):
        for kw in keywords:
            if kw.name == name:
                if kw.source == source:
                    return
                raise AssertionError("Keyword '%s' had wrong source: '%s' != '%s'"
                                     % (kw.name, kw.source, source))
        raise AssertionError("Keyword '%s' not found in suite or resource\n"
                             "Imported libs: %s\n"
                             % (name, [lib for lib in
                                       cache.LIBRARYCACHE.libraries]))

    def _assert_does_not_contain(self, keywords, name, source):
        for kw in keywords:
            if kw.name == name and kw.source == source:
                raise AssertionError("Keyword '%s' found from source %s\n" % 
                                     (name, source))

    def _assert_variable(self, suite, name):
        variables = [ var.name for var in suite.get_variables_for_content_assist() ]
        if not name in variables:
            raise AssertionError("Variable '%s' not found in %s" % 
                                (name, variables))

    def _assert_variable_does_not_exist(self, suite, name):
        variables = [ var.name for var in suite.get_variables_for_content_assist() ]
        if name in variables:
            raise AssertionError("Variable '%s' found in %s" % 
                                (name, variables))


class TestResolvingOwnKeywords(_ContentAssistBaseTest):

    def test_own_user_keywords(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 
                              'My Test Setup', COMPLEX_SUITE.name)

    def test_own_keyword_for_content_assist(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(), 
                              'My Test Setup', '<this file>')

    def test_filtering_keywords_with_longnames(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(name='BuiltIn.Catenate'),
                              'Catenate', 'BuiltIn')
        self._assert_contains(COMPLEX_SUITE.get_keywords_for_content_assist(name='Catenate'),
                              'Catenate', 'BuiltIn')


class TestResolvingKeywordsFromImports(_ContentAssistBaseTest):

    def test_keywords_from_imports(self):
        for name, source in [('Resource UK', 'resource.html'),
                             ('Resource2 UK', 'resource2.html'),
                             ('UK From Text Resource', 'resource.txt'),
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

    def test_spec_file_name_is_case_sensitive(self):
        self._assert_does_not_contain(COMPLEX_SUITE.get_keywords(),
                                      'Open Browser', 'seleniumlibrary')


class TestResolvingKeywordsFromImportsWithVariables(_ContentAssistBaseTest):

    def test_libary_defined_as_variable(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'List Should Contain Value', 'Collections')

    def test_variables_in_import_settings_are_case_insensitive(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'File Should Exist', 'OperatingSystem')

    def test_variables_from_other_imports_can_be_used(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Open Connection', 'Telnet')


class TestModifyingDataAffectReturnedKeywords(_ContentAssistBaseTest):

    def tearDown(self):
        COMPLEX_SUITE.keywords.pop(-1)

    def test_changing_keywords_in_suite(self):
        COMPLEX_SUITE.keywords.new_keyword('New Keyword')
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 'New Keyword',
                              COMPLEX_SUITE.name)

    def test_changing_keywords_in_resource(self):
        resource = COMPLEX_SUITE.get_resources()[0]
        resource.keywords.new_keyword('New UK')
        self._assert_contains(COMPLEX_SUITE.get_keywords(), 'New UK', resource.name)

    def test_get_all_keywords(self):
        for name, source in [('My Test Setup', 'Everything'), 
                             ('Resource UK', 'resource.html'),
                             ('Another Resource UK', 'another_resource.html')]:
            self._assert_contains(COMPLEX_MODEL.get_all_keywords(), name, source)
        COMPLEX_SUITE.keywords.new_keyword('New Suite UK')
        self._assert_contains(COMPLEX_MODEL.get_all_keywords(), 'New Suite UK',
                              'Everything')


class TestModifyingImportsAffectsResolvedKeywords(_ContentAssistBaseTest):

    def tearDown(self):
        COMPLEX_SUITE.settings.imports.pop(-1)

    def test_adding_resource(self):
        self._robot_2_1_1_required()
        COMPLEX_SUITE.settings.imports.new_resource('../resources/resources2/even_more_resources.txt')
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Foo', 'even_more_resources.txt')

    def test_updating_resource(self):
        self._robot_2_1_1_required()
        COMPLEX_SUITE.settings.imports.new_resource('../resources/resources2/resources.txt')
        self._assert_does_not_contain(COMPLEX_SUITE.get_keywords(),
                                      'Foo', 'even_more_resources.txt')
        COMPLEX_SUITE.settings.imports[-1].set_str_value('../resources/resources2/even_more_resources.txt')
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Foo', 'even_more_resources.txt')

    def test_removing_resource(self):
        self.test_adding_resource()
        COMPLEX_SUITE.settings.imports.pop(-1)
        self._assert_does_not_contain(COMPLEX_SUITE.get_keywords(),
                                      'Foo', 'even_more_resources.txt')
        # Hack, restore global state
        self.test_adding_resource()

    def test_added_resource_path_is_normalized_in_case_insensitive_file_systems(self):
        COMPLEX_SUITE.settings.imports.new_resource('../Resources/Resources2/Even_More_Resources.txt')
        if _CASE_INSENSITIVE_FILESYSTEM:
            self._assert_contains(COMPLEX_SUITE.get_keywords(),
                                  'Foo','even_more_resources.txt')
        else:
            self._assert_does_not_contain(COMPLEX_SUITE.get_keywords(),
                                          'Foo', 'even_more_resources.txt')

    def test_adding_library(self):
        COMPLEX_SUITE.settings.imports.new_library('Dialogs')
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Execute Manual Step', 'Dialogs')

    def test_updating_library(self):
        COMPLEX_SUITE.settings.imports.new_library('InvalidDialogs')
        self._assert_does_not_contain(COMPLEX_SUITE.get_keywords(),
                                      'Execute Manual Step', 'Dialogs')
        COMPLEX_SUITE.settings.imports[-1].set_str_value('Dialogs')
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'Execute Manual Step', 'Dialogs')

    def _robot_2_1_1_required(self):
        try:
            import robot.parsing.txtreader
        except ImportError:
            raise AssertionError("Robot 2.1.1 or newer required to run this test.")


class TestResolvingVariables(_ContentAssistBaseTest):

    def test_get_variables_for_suite(self):  
        self._assert_variable(COMPLEX_SUITE, '${SCALAR}')

    def test_variables_for_user_keyword_contain_arguments(self):
        kw = COMPLEX_SUITE.keywords[1]
        self._assert_variable(kw, '${scalar arg}')

    def test_get_variables_from_resource_files(self):
        for name in ['${SCALAR}', '@{LIST}', '${RESOURCE var}',
                     '@{RESOURCE 2 List VARIABLE}']:
            self._assert_variable(COMPLEX_SUITE, name)

    def test_finding_variables_from_variable_file(self):
        self._assert_variable(COMPLEX_SUITE, '${var_from_file}')

    def test_finding_variables_from_variable_file_importes_in_resource(self):
        self._assert_variable(COMPLEX_SUITE, '${var_from_resource_var_file}')

    def test_variables_are_resolved_before_passed_to_variable_files(self):
        self._assert_variable(COMPLEX_SUITE, '${value}')


class TestModifyingImportsAffectResolvedVariables(_ContentAssistBaseTest):

    def tearDown(self):
        COMPLEX_SUITE.settings.imports.pop(-1)

    def test_adding_variable_file(self):
        self._add_variable_import('../resources/resources2/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')

    def test_updating_variable_file(self):
        self._add_variable_import('invalid.py')
        self._assert_variable_does_not_exist(COMPLEX_SUITE, '${var_in_resource2}')
        COMPLEX_SUITE.settings.imports[-1].set_str_value('../resources/resources2/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')

    def test_deleting_variable_file(self):
        self._add_variable_import('../resources/resources2/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')
        COMPLEX_SUITE.settings.imports.pop(-1)
        self._assert_variable_does_not_exist(COMPLEX_SUITE, '${var_in_resource2}')
        self._add_variable_import('../resources/resources2/even_more_varz.py')

    def test_adding_variable_file_in_pythonpath(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'resources',
                            'robotdata', 'resources', 'resources2')
        sys.path.append(path)
        self._add_variable_import('even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')

    def _add_variable_import(self, name):
        COMPLEX_SUITE.settings.imports.new_variables(name)


if __name__ == '__main__':
    unittest.main()
