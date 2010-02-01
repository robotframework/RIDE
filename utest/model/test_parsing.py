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

from robotide.namespace import Namespace
from robotide.model.files import InitFile, ResourceFile
from robotide.robotapi import TestSuiteData, ResourceFileData
from robot.utils.asserts import assert_equals
from resources import SUITEPATH, RESOURCE_PATH, PATH_RESOURCE_NAME

DATA = TestSuiteData(SUITEPATH)


class TestParsing(unittest.TestCase):

    def setUp(self):
        self.suite = InitFile(DATA, Namespace())
        self.file_suite = self.suite.suites[0]
        self.test = self.file_suite.tests[0]
        self.uk = self.file_suite.keywords[1]

    def test_test_suite_parsing(self):
        assert_equals(self.file_suite.name, 'Everything')
        assert_equals(self.file_suite.longname, 'Testsuite.Everything')
        assert_equals(self.file_suite.settings.doc.get_str_value(),
                      'This test data file is used in *RobotIDE* ' +
                      '_integration_ tests.')
        assert_equals(self.file_suite.settings.default_tags.value,
                      ['regeression'])
        assert_equals(self.file_suite.settings.force_tags.value, ['ride'])
        for fixture, exp_value in [('suite_setup', ['My Suite Setup']),
                                    ('suite_teardown', ['My Suite Teardown',
                                                        '${scalar}', '@{LIST}']),
                                    ('test_setup', ['My Test Setup']),
                                    ('test_teardown', ['My Test Teardown']) ]:
            assert_equals(getattr(self.file_suite.settings, fixture).value,
                                  exp_value)
        assert_equals(self.file_suite.settings.test_timeout.value,
                      ['10 seconds', 'No tarrying allowed'])

    def test_resource_parsing(self):
        res = ResourceFile(ResourceFileData(RESOURCE_PATH), Namespace())
        assert_equals(res.name, 'resource.html')
        assert_equals(res.longname, 'resource')

    def test_test_case_parsing(self):
        assert_equals(self.test.name, 'My Test')
        assert_equals(self.test.longname, 'Testsuite.Everything.My Test')
        assert_equals(self.test.doc, 'This is _test_ *case* documentation')
        s = self.test.settings
        assert_equals(s.tags.value, ['test 1'])
        assert_equals(s.setup.value, ['My Overriding Test Setup'])
        assert_equals(s.teardown.value, ['My Overriding Test Teardown'])
        assert_equals(s.timeout.value, ['2 seconds', "I'm in a great hurry"])

    def test_user_keyword_parsing(self):
        assert_equals(self.uk.name, 'My Suite Teardown')
        assert_equals(self.uk.longname,
                      'Testsuite.Everything.My Suite Teardown')
        assert_equals(self.uk.doc, 'This is *user* _keyword_ documentation')
        assert_equals(self.uk.settings.args.value,
                      ['${scalar arg}', '${default arg}=default', '@{list arg}'])
        assert_equals(self.uk.settings.return_value.value, ['Success'])
        assert_equals(self.uk.settings.timeout.value,
                      ['1 second', "I'm faster than you"])

    def test_variables_parsing(self):
        assert_equals(len(self.file_suite.variables), 5)
        assert_equals(self.file_suite.variables.get_name_and_value(0),
                      ('${SCALAR}', 'value'))


class TestFindingImports(unittest.TestCase):

    def setUp(self):
        self.suite = InitFile(DATA, Namespace()).suites[0]

    def test_resource_imports(self):
        assert_equals(self.suite.get_resources()[0].name, 'resource.html')
        assert_equals(self.suite.get_resources()[0].longname, 'resource')

    def test_nested_resource_imports(self):
        assert_equals(self.suite.get_resources()[0].get_resources()[0].name,
                      'resource2.html')

    def test_resource_from_python_path(self):
        assert_equals(self.suite.get_resources()[1].name, PATH_RESOURCE_NAME)

    def test_resource_from_xml(self):
        assert_equals(self.suite.get_resources()[2].name, 'Spec Resource')


class TestFindingImportsWithVariables(unittest.TestCase):

    def setUp(self):
        self.suite = InitFile(DATA, Namespace()).suites[0]

    def test_finding_resource_import_with_variable(self):
        assert_equals(self.suite.get_resources()[3].name,
                      'another_resource.html')

    def test_finding_resource_file_with_variable_in_path(self):
        assert_equals(self.suite.get_resources()[4].name, 'resource4.html')

    def test_finding_variable_file_with_variable_in_path(self):
        assert_equals(self.suite._get_variable_file_variables()[4].name,
                      '${varfrommorevarz}')


if __name__  == '__main__':
    unittest.main()

