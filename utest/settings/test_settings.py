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
import os

from robotide.preferences import settings
from robotide.preferences.settings import Settings, SectionError,\
    ConfigurationError, initialize_settings, SettingsMigrator
from robotide.preferences.configobj import UnreprError

from resources.setting_utils import TestSettingsHelper


class TestInvalidSettings(TestSettingsHelper):

    def test_no_settings_exists(self):
        self.assertEqual(self.settings._config_obj, {})

    def test_setting_name_with_space(self):
        self.settings['name with space'] = 0
        settings = Settings(self.user_settings_path)
        self.assertEqual(settings['name with space'], 0)

    def test_invalid_settings(self):
        self._write_settings('invalid syntax = foo')
        with self.assertRaises(ConfigurationError):
            settings = Settings(self.user_settings_path)


class TestSettingTypes(TestSettingsHelper):

    def test_writing_string_setting(self):
        self._test_settings_types({'string': 'value'})

    def test_writing_unicode_setting(self):
        self._test_settings_types(
            {'unicode_string': u'non-ascii character \xe4'})

    def test_writing_list_setting(self):
        self._test_settings_types(
            {'unicode_string': [1, 'string', u'non-ascii character \xe4']})

    def test_writing_tuple_setting(self):
        self._test_settings_types(
            {'unicode_string': (1, 'string', u'non-ascii character \xe4')})

    def test_writing_dictionary_setting(self):
        self._test_settings_types({'dictionary': {'a': 1, 'b': 2, 'c': 3}})

    def test_writing_none_setting(self):
        self._test_settings_types({'none': None})

    def test_writing_boolean_setting(self):
        self._test_settings_types({'boolean': True})

    def test_writing_multiline_string_setting(self):
        multiline = u"""Multi line string
with non-ascii chars \xe4
and quotes "foo" 'bar'
and even triple quotes \"\"\" '''
"""
        self._test_settings_types({'multiline': multiline})

    def test_multiple_settings(self):
        multiline = u"""Multi line string
with non-ascii chars \xe4
and quotes "foo" 'bar'
and even triple quotes \"\"\" '''
"""
        self._test_settings_types(
            {'multiline': multiline, 'string': u'some', 'bool': False,
             'int': 1, 'float': 2.4})

    def _test_settings_types(self, expected):
        for key, value in expected.items():
            self.settings[key] = value
        self.assertEqual(expected, self._read_settings()._config_obj)


class TestSettings(TestSettingsHelper):

    def test_changing_settings_with_setitem(self):
        self._create_settings_with_defaults()
        self.settings['foo'] = 'new value'
        self._check_content({'foo': 'new value', 'hello': 'world'})

    def test_getting_settings_with_getitem(self):
        self._create_settings_with_defaults()
        self.assertEqual('bar', self.settings['foo'])

    def _create_settings_with_defaults(self):
        self._write_settings(
            "foo = 'bar'\nhello = 'world'", self.user_settings_path)
        self.default = {'foo': 'bar', 'hello': 'world'}
        self.settings = Settings(self.user_settings_path)

    def test_set(self):
        self._create_settings_with_defaults()
        self.settings.set('foo', 'new value')
        self._check_content({'foo': 'new value', 'hello': 'world'})

    def test_set_with_non_existing_value(self):
        self._create_settings_with_defaults()
        self.settings.set('zip', 2)
        self._check_content({'foo': 'bar', 'hello': 'world', 'zip': 2})

    def test_set_without_autosave(self):
        self._create_settings_with_defaults()
        self.settings.set('foo', 'new value', autosave=False)
        self._check_content(self.default, check_self_settings=False)
        expected = {'foo': 'new value', 'hello': 'world'}
        self.assertEqual(self.settings._config_obj, expected)
        self.settings.save()
        self._check_content(expected)

    def test_set_without_override_when_settings_does_not_exist(self):
        self.settings.set('foo', 'new value', override=False)
        self._check_content({'foo': 'new value'})

    def test_set_without_override_when_settings_exists(self):
        self._create_settings_with_defaults()
        self.settings.set('foo', 'new value', override=False)
        self._check_content(self.default)

    def test_set_values(self):
        self._create_settings_with_defaults()
        self.settings.set_values({'foo': 'new value', 'int': 1})
        self._check_content({'foo': 'new value', 'hello': 'world', 'int': 1})

    def test_set_values_without_autosave(self):
        self._create_settings_with_defaults()
        self.settings.set_values(
            {'foo': 'new value', 'int': 1}, autosave=False)
        expected = {'foo': 'new value', 'hello': 'world', 'int': 1}
        self.assertEqual(self.settings._config_obj, expected)
        self._check_content(self.default, check_self_settings=False)
        self.settings.save()
        self._check_content(expected)

    def test_set_values_without_override(self):
        self._create_settings_with_defaults()
        self.settings.set_values({'foo': 'not set', 'new item': 'is set'},
                                 override=False)
        self.default['new item'] = 'is set'
        self._check_content(self.default)

    def test_set_values_with_none(self):
        self._create_settings_with_defaults()
        self.settings.set_values(None)
        self._check_content(self.default)

    def test_set_defaults(self):
        self.settings.set_defaults(foo='bar', zip=3)
        self._check_content({'foo': 'bar', 'zip': 3})

    def test_set_defaults_when_some_values_already_exists(self):
        self._create_settings_with_defaults()
        self.settings.set_defaults(foo='value', zip=3)
        self._check_content({'foo': 'bar', 'hello': 'world', 'zip': 3})


SETTINGS_CONTENT = """
# Main comment
string = 'REPLACE_STRING'
int = 13
float = 1.5
# Main comment 2
boolean = True

[Section 1]
# Section 1 comment

list = [1, 2]
robot = 'REPLACE_ROBOT'
tuple = (1, 2)

# Section 1 comment 2

[Section 2]

list = [2, 1]
# Comment again
tuple = (2, 1)

# Which also may be several lines
"""


class TestSettingsFileContent(TestSettingsHelper):

    def test_settings_file_content_stay(self):
        self._write_settings(SETTINGS_CONTENT)
        settings = Settings(self.user_settings_path)
        settings['string'] = 'new value'
        settings['Section 1']['robot'] = 'New Robot'
        expected = SETTINGS_CONTENT.replace('REPLACE_STRING', 'new value')
        expected = expected.replace('REPLACE_ROBOT', 'New Robot')
        self.assertEqual(self._read_settings_file_content(), expected)


class TestSections(TestSettingsHelper):

    def test_add_section(self):
        self.settings.add_section('Plugin 1')
        self.assertEqual(self.settings['Plugin 1']._config_obj, {})

    def test_add_section_returns_section(self):
        self.assertEqual(
            self.settings.add_section('Plugin 1')._config_obj, {})

    def test_add_section_with_default_values(self):
        section = self.settings.add_section('Plugin 1', a='b', one='2')
        self.assertEqual(section._config_obj, {'a': 'b', 'one': '2'})
        self.assertEqual(self._read_settings()['Plugin 1']._config_obj,
                          {'a': 'b', 'one': '2'})

    def test_add_section_should_not_fail_if_section_already_exists(self):
        self.settings.add_section('Plugin 1')
        self.settings.add_section('Plugin 1')
        self.settings['Plugin 1']['foo'] = 'bar'
        self.assertEqual(self.settings.add_section('Plugin 1')._config_obj,
                          {'foo': 'bar'})

    def test_add_section_should_fail_if_item_with_same_name_already_exists(
            self):
        self.settings['Plugin 1'] = 123
        self.assertRaises(SectionError, self.settings.add_section, 'Plugin 1')

    def test_set_should_fail_if_section_with_same_name_already_exists(self):
        self.settings.add_section('Plugin 1')
        self.assertRaises(SectionError, self.settings.set, 'Plugin 1', 123)

    def test_set_overriding_section_with_other_section(self):
        self.settings.add_section('Plugin 1', foo='bar', hello='world')
        section = self.settings.add_section('Plugin 2', zip=2)
        self.settings.set('Plugin 1', section)
        self.assertEqual(self.settings['Plugin 1']._config_obj, {'zip': 2})
        self.assertEqual(
            self._read_settings()['Plugin 1']._config_obj, {'zip': 2})

    def test_set_updating_section_with_other_section(self):
        self.settings.add_section('Plugin 1', foo='bar', hello='world')
        section = self.settings.add_section(
            'Plugin 2', foo='new value', zip=2)
        self.settings.set('Plugin 1', section, override=False)
        expected = {'foo': 'bar', 'hello': 'world', 'zip': 2}
        self.assertEqual(self.settings['Plugin 1']._config_obj, expected)
        self.assertEqual(
            self._read_settings()['Plugin 1']._config_obj, expected)

    def test_add_sub_section(self):
        self.settings.add_section('Plugin 1')
        self.settings['Plugin 1'].add_section('Plugin 1.1')
        self.assertEqual(
            self.settings['Plugin 1']['Plugin 1.1']._config_obj, {})

    def test_add_settings_to_sub_section(self):
        self.settings.add_section('Plugin 1')
        self.settings['Plugin 1'].add_section('Plugin 1.1')
        self.settings['Plugin 1']['Plugin 1.1']['foo'] = 'bar'
        self.assertEqual(self.settings['Plugin 1']['Plugin 1.1']._config_obj,
                          {'foo': 'bar'})

    def test_using_section_separately_and_saving(self):
        self.settings.add_section('Plugin 1')
        plugin_settings = self.settings['Plugin 1']
        plugin_settings['foo'] = 'bar'
        plugin_settings.save()
        self.assertEqual(self._read_settings()['Plugin 1']._config_obj,
                          {'foo': 'bar'})

    def test_set_values_to_section(self):
        defaults = {'foo': 'bar', 'hello': 'world'}
        self.settings.add_section('Plugin 1')
        self.settings['Plugin 1'].set_values(defaults)
        self.assertEqual(
            self._read_settings()['Plugin 1']._config_obj, defaults)


class TestInitializeSettings(TestSettingsHelper):

    def setUp(self):
        self._orig_dir = settings.SETTINGS_DIRECTORY
        self.settings_dir = os.path.join(os.path.dirname(__file__), 'ride')
        # print("DEBUG: Settings dir init %s" % self.settings_dir)
        settings.SETTINGS_DIRECTORY = self.settings_dir
        self._init_settings_paths()
        self._write_settings("foo = 'bar'\nhello = 'world'\n",
                             self.settings_path)
        self.user_settings_path = os.path.join(self.settings_dir, 'user.cfg')

    def tearDown(self):
        settings.SETTINGS_DIRECTORY = self._orig_dir
        self._remove_path(self.user_settings_path)
        self._remove_path((self.user_settings_path+'_old_broken'))
        os.removedirs(self.settings_dir)

    def test_initialize_settings_creates_directory(self):
        initialize_settings(self.settings_path, 'user.cfg')
        self.assertTrue(os.path.exists(self.settings_dir))

    def test_initialize_settings_copies_settings(self):
        initialize_settings(self.settings_path, 'user.cfg')
        self.assertTrue(os.path.exists(self.settings_dir))

    def test_initialize_settings_does_merge_when_settings_exists(self):
        os.mkdir(self.settings_dir)
        self._write_settings(
            "foo = 'bar'\nhello = 'world'\n", self.settings_path)
        # print("DEBUG: test_settings test_initialize_settings_does_merge_when_settings_exists wrote file! %s" % self.settings_path)
        # unittest.skip("DEBUG")
        self._write_settings("foo = 'new value'\nhello = 'world'\n",
                             self.user_settings_path)
        initialize_settings(self.settings_path, 'user.cfg')
        self._check_content(
            {'foo': 'new value', 'hello': 'world',
             SettingsMigrator.SETTINGS_VERSION: 8}, False)

    def test_initialize_settings_raises_exception_when_invalid_user_settings(
            self):
        os.mkdir(self.settings_dir)
        self._write_settings("foo = 'bar'\nhello = 'world'\n",
                             self.settings_path)
        self._write_settings("invalid = invalid", self.user_settings_path)
        with self.assertRaises(tuple([ConfigurationError, UnreprError])):
            initialize_settings(self.settings_path, 'user.cfg')
            self._check_content({'foo': 'bar', 'hello': 'world', 'settings_version': 8}, False)

    def test_initialize_settings_replaces_corrupted_settings_with_defaults(
            self):
        os.mkdir(self.settings_dir)
        self._write_settings("dlskajldsjjw2018032")
        defaults = self._read_file(self.settings_path)
        with self.assertRaises(ConfigurationError):
            settings = self._read_file(initialize_settings(self.settings_path, 'user.cfg'))
            self.assertEqual(defaults, settings)

    def _read_file(self, path):
        with open(path, 'r') as o:
            return o.read()


class TestMergeSettings(TestSettingsHelper):

    def setUp(self):
        self._init_settings_paths()
        self._write_settings("foo = 'bar'\nhello = 'world'\n",
                             self.settings_path)

    def test_merge_when_no_user_settings(self):
        SettingsMigrator(self.settings_path, self.user_settings_path).merge()
        self._check_content({'foo': 'bar', 'hello': 'world'}, False)

    def test_merge_when_user_settings_are_changed(self):
        self._write_settings("foo = 'new value'\nhello = 'world'\n",
                             self.user_settings_path)
        SettingsMigrator(self.settings_path, self.user_settings_path).merge()
        self._check_content({'foo': 'new value', 'hello': 'world'}, False)

    def test_merge_when_new_settings_in_defaults(self):
        self._write_settings("foo = 'bar'\nhello = 'world'\nnew = 'value'\n",
                             self.settings_path)
        self._write_settings("foo = 'new value'\nhello = 'world'\n",
                             self.user_settings_path)
        SettingsMigrator(self.settings_path, self.user_settings_path).merge()
        self._check_content(
            {'foo': 'new value', 'hello': 'world', 'new': 'value'}, False)

    def test_merge_fails_reasonably_when_settings_file_is_read_only(self):
        try:
            SettingsMigrator(self.settings_path, self.read_only_path).merge()
        except RuntimeError as e:
            self.assertTrue(str(e).startswith('Could not open'))
        else:
            raise AssertionError('merging read-only file succeeded')


if __name__ == "__main__":
    unittest.main()
