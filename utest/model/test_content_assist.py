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

    def _should_contain(self, name, source):
        for item in COMPLEX_SUITE.content_assist_values():
            if item.name == name and item.source == source:
                return
        raise AssertionError('Item "%s" not found from %s' % (name, source))


class TestResolvingKeywordAndVariablesForContentAssist(_ContentAssistBaseTest):
    exp_data = [ ('Should Be Equal', 'BuiltIn'),
                 ('File Should Exist', 'OperatingSystem'),
                 ('Resource UK', 'resource.html'),
                 ('Resource2 UK', 'resource2.html'),
                 ('Resource3 UK', 'resource3.html'),
                 ('UK From Text Resource', 'resource.txt'),
                 ('Path Resource UK', PATH_RESOURCE_NAME),
                 ('Attributeless Keyword', 'LibSpecLibrary'),
                 #('Attributeless Keyword', 'Spec Resource'),
                 ('Testlib Keyword', 'TestLib'),
                 ('List Should Contain Value', 'Collections'),
                 ('Open Connection', 'Telnet'),
                 ('Get Mandatory', 'ArgLib'),
                 ('Longest', 'AnotherArgLib'),
               ]

    def test_content_assist_for(self):
        for name, source in [('My Test Setup', '<this file>')] + self.exp_data:
            self._should_contain(name, source)


class TestResolvingOwnKeywords(_ContentAssistBaseTest):

    def test_own_user_keywords(self):
        self._assert_contains(COMPLEX_SUITE.get_keywords(),
                              'My Test Setup', COMPLEX_SUITE.name)

    def test_filtering_keywords_with_longnames(self):
        self._assert_contains(COMPLEX_SUITE.content_assist_values(name='BuiltIn.Catenate'),
                              'Catenate', 'BuiltIn')
        self._assert_contains(COMPLEX_SUITE.content_assist_values(name='Catenate'),
                              'Catenate', 'BuiltIn')


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
        self._add_variable_import('../resources/more_resources/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')

    def test_updating_variable_file(self):
        self._add_variable_import('invalid.py')
        self._assert_variable_does_not_exist(COMPLEX_SUITE, '${var_in_resource2}')
        COMPLEX_SUITE.settings.imports[-1].set_str_value('../resources/more_resources/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')

    def test_deleting_variable_file(self):
        self._add_variable_import('../resources/more_resources/even_more_varz.py')
        self._assert_variable(COMPLEX_SUITE, '${var_in_resource2}')
        COMPLEX_SUITE.settings.imports.pop(-1)
        self._assert_variable_does_not_exist(COMPLEX_SUITE, '${var_in_resource2}')
        self._add_variable_import('../resources/more_resources/even_more_varz.py')

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
