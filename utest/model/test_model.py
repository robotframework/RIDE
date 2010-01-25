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
import tempfile
import os

from robotide.model.tcuk import TestCase, UserKeyword
from robotide.model.files import TestSuiteFactory, ResourceFileFactory

from resources import MockSerializer, FakeSuite, FakeTestCase, FakeUserKeyword, \
    COMPLEX_SUITE_PATH

from robot.utils.asserts import assert_false, assert_true, assert_equals,\
    assert_not_equals


DIRPATH = os.path.join(tempfile.gettempdir(), 'ride_model_utest_dir')
if not os.path.exists(DIRPATH):
    os.mkdir(DIRPATH)
FILEPATH = os.path.join(DIRPATH, 'tests.tsv')
RESOURCEPATH = os.path.join(DIRPATH, 'resource.tsv')
INITPATH = os.path.join(DIRPATH, '__init__.tsv')


class TestModifiedOnDiskWithFileSuite(unittest.TestCase):

    def setUp(self):
        open(FILEPATH, 'w').write('*Test Cases*\nRide Unit Test\tNo Operation\n')

    def test_mtime(self):
        suite = FakeSuite(path=FILEPATH)
        assert_false(suite.has_been_modified_on_disk())
        os.utime(FILEPATH, (1,1))
        assert_true(suite.has_been_modified_on_disk())

    def test_size_change(self):
        os.utime(FILEPATH, None)
        suite = FakeSuite(path=FILEPATH)
        open(FILEPATH, 'a').write('#Ninja edit\n')
        assert_true(suite.has_been_modified_on_disk())

    def test_reload(self):
        suite = TestSuiteFactory(FILEPATH)
        assert_equals(len(suite.tests), 1)
        open(FILEPATH, 'a').write('Second Test\tLog\tHello World!\n')
        suite.reload_from_disk()
        assert_equals(len(suite.tests), 2)
        assert_equals(suite.tests[-1].name, 'Second Test')

    def test_overwrite(self):
        suite = TestSuiteFactory(FILEPATH)
        os.utime(FILEPATH, (1,1))
        assert_true(suite.has_been_modified_on_disk())
        suite.serialize(force=True)
        assert_false(suite.has_been_modified_on_disk())


class TestModifiedOnDiskWithDirectorySuite(unittest.TestCase):

    def setUp(self):
        open(FILEPATH, 'w').write('*Test Cases*\nRide Unit Test\tNo Operation\n')
        open(INITPATH, 'w').write('*Settings*\nDocumentation\tRide unit testing file\n')

    def test_reload_with_directory_suite(self):
        suite = TestSuiteFactory(DIRPATH)
        orig_doc = suite.settings.doc.get_str_value()
        open(INITPATH, 'a').write('...\tAdded more documentation')
        suite.reload_from_disk()
        s = suite.settings
        assert_not_equals(orig_doc, s.doc.get_str_value())
        assert_true(s.doc.get_str_value().endswith('Added more documentation'))

    def test_mtime_with_directory_suite(self):
        suite = FakeSuite(path=INITPATH)
        assert_false(suite.has_been_modified_on_disk())
        os.utime(INITPATH, (1,1))
        assert_true(suite.has_been_modified_on_disk())


class TestModifiedOnDiskWithresource(unittest.TestCase):

    def setUp(self):
        open(RESOURCEPATH, 'w').write('*Keywords*\nUnit Test Keyword\tNo Operation\n')

    def test_reload_with_resource(self):
        resource = ResourceFileFactory(RESOURCEPATH)
        assert_equals(len(resource.keywords), 1)
        open(RESOURCEPATH, 'a').write('Ninjaed Keyword\tLog\tI am taking over!\n')
        resource.reload_from_disk()
        assert_equals(len(resource.keywords), 2)
        assert_equals(resource.keywords[-1].name, 'Ninjaed Keyword')


class TestCreatingNewTestCase(unittest.TestCase):

    def setUp(self):
        self.suite = FakeSuite()
        self.test = TestCase(self.suite, name='TestCase')

    def test_name(self):
        assert_equals(self.test.name, 'TestCase')

    def test_settings(self):
        s = self.test.settings
        assert_equals(s.doc.value, [])
        assert_equals(s.timeout.value, None)
        assert_equals(s.setup.value, None)
        assert_equals(s.teardown.value, None)
        assert_equals(s.tags.value, None)

    def test_keyword_list(self):
        assert_equals(len(self.test.keywords), 0)


class TestTestCaseCopy(unittest.TestCase):

    def setUp(self):
        self.suite = FakeSuite()
        self.test = FakeTestCase(self.suite)
        self.test.settings.setup.set_str_value('My Setup|arg')
        self.copy = self.test.copy('Copy')

    def test_name(self):
        assert_equals(self.copy.name, 'Copy')

    def test_settings(self):
        orig, copied = self.copy.settings.setup, self.test.settings.setup
        assert_equals(orig.value, copied.value)
        assert_false(orig is copied)

    def test_keyword_list(self):
        assert_equals(len(self.copy.keywords), 1)


class TestCreatingNewUserKeyword(unittest.TestCase):

    def setUp(self):
        self.suite = FakeSuite()
        self.uk = UserKeyword(self.suite, name='UserKeyword')

    def test_name(self):
        assert_equals(self.uk.name, 'UserKeyword')

    def test_settings(self):
        assert_equals(self.uk.doc, '')
        assert_equals(self.uk.settings.timeout.value, None)
        assert_equals(self.uk.settings.return_value.value, [])
        assert_equals(self.uk.settings.args.value, [])

    def test_keyword_list(self):
        assert_equals(len(self.uk.keywords), 0)

    def test_serializing(self):
        serializer = MockSerializer()
        self.uk.serialize(serializer)
        assert_equals(serializer.record, ['Start UK: UserKeyword', 'End UK'])


class TestUserKeywordCopy(unittest.TestCase):

    def setUp(self):
        self.suite = FakeSuite()
        uk = FakeUserKeyword(self.suite)
        self.copy = uk.copy('Copy')

    def test_name(self):
        assert_equals(self.copy.name, 'Copy')

    def test_settings(self):
        assert_equals(self.copy.settings.args.value, ['${scalar}'])
        assert_equals(self.copy.doc, 'Some doc')
        assert_equals(self.copy.settings.timeout.value, None)

    def test_keyword_list(self):
        assert_equals(len(self.copy.keywords), 1)


class TestVariables(unittest.TestCase):
    suite = TestSuiteFactory(COMPLEX_SUITE_PATH)

    def test_equals_sign_is_removed_in_parsing(self):
        assert_equals(self.suite.variables.get_name_and_value(0), ('${SCALAR}', 'value'))

    def test_modifying(self):
        self.suite.variables.set_name_and_value(0, '${SCALAR}', 'new value')
        assert_equals(self.suite.variables.get_name_and_value(0), ('${SCALAR}', 'new value'))

    def test_handling_equals_sign(self):
        self.suite.variables.set_name_and_value(0, '${SCALAR} =', 'new value')
        assert_equals(self.suite.variables.get_name_and_value(0), ('${SCALAR}', 'new value'))


if __name__ == '__main__':
    unittest.main()
