#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

from robotide.controller.settingcontrollers import DocumentationController, \
    FixtureController, TagsController, TimeoutController, TemplateController
from robotide.controller.tablecontrollers import VariableTableController, \
    TestCaseTableController, KeywordTableController, ImportSettingsController, \
    MetadataListController, TestCaseController
from robotide.controller.basecontroller import WithUndoRedoStacks
from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile
from robotide import utils


def DataController(data, parent):
    return TestCaseFileController(data, parent) if isinstance(data, TestCaseFile) \
        else TestDataDirectoryController(data, parent)


class _DataController(WithUndoRedoStacks):

    def __init__(self, data, chief_controller=None):
        self._chief_controller = chief_controller
        self.data = data
        self.dirty = False
        self.children = self._children(data)
        self._stat = self._get_stat(self.source)

    def _get_stat(self, path):
        if path and os.path.isfile(path):
            stat = os.stat(path)
            return (stat.st_mtime, stat.st_size)
        return (0, 0)

    @property
    def name(self):
        return self.data.name

    @property
    def settings(self):
        return self._settings()

    def _settings(self):
        ss = self.data.setting_table
        return [DocumentationController(self, ss.doc),
                FixtureController(self, ss.suite_setup),
                FixtureController(self, ss.suite_teardown),
                FixtureController(self, ss.test_setup),
                FixtureController(self, ss.test_teardown),
                TagsController(self, ss.force_tags)]

    @property
    def variables(self):
        return VariableTableController(self, self.data.variable_table)

    @property
    def tests(self):
        return TestCaseTableController(self, self.data.testcase_table)

    @property
    def datafile(self):
        return self.data

    @property
    def all_datafiles(self):
        return self._chief_controller.datafiles

    @property
    def datafile_controller(self):
        return self

    @property
    def keywords(self):
        return KeywordTableController(self, self.data.keyword_table)

    @property
    def imports(self):
        return ImportSettingsController(self, self.data.setting_table)

    @property
    def metadata(self):
        return MetadataListController(self, self.data.setting_table)

    def execute(self, command):
        return command.execute(self)

    def has_been_modified_on_disk(self):
        return self._get_stat(self.source) != self._stat

    def mark_dirty(self):
        self.dirty = True

    def unmark_dirty(self):
        self.dirty = False
        self._stat = self._get_stat(self.source)

    def create_keyword(self, name, argstr=''):
        return self.keywords.new(name, argstr)

    def add_test_or_keyword(self, test_or_kw_ctrl):
        if isinstance(test_or_kw_ctrl, TestCaseController):
            self.tests.add(test_or_kw_ctrl)
            test_or_kw_ctrl._parent = self.tests
        else:
            self.keywords.add(test_or_kw_ctrl)
            test_or_kw_ctrl._parent = self.keywords

    def has_format(self):
        return True

    def get_format(self):
        if not self.source:
            return None
        return os.path.splitext(self.source)[1].replace('.', '')

    def set_format(self, format):
        base = os.path.splitext(self.source)[0]
        self.data.source = '%s.%s' % (base, format.lower())

    def is_same_format(self, format):
        if format and self.has_format():
            return format.lower() == self.get_format().lower()
        return False

    def save_with_new_format(self, format):
        self._chief_controller.change_format(self, format)

    def save_with_new_format_recursive(self, format):
        self._chief_controller.change_format_recursive(self, format)

    def validate_keyword_name(self, name):
        return self.keywords.validate_name(name)

    @property
    def source(self):
        return self.data.source

    @property
    def directory(self):
        return self.data.directory

    def is_directory_suite(self):
        return False

    def resource_import_modified(self, path):
        return self._chief_controller.resource_import_modified(os.path.join(self.directory, path))

    def notify_settings_changed(self):
        pass

    def iter_datafiles(self):
        # TODO: Not necessarily worthy of a generator
        yield self
        for child in self.children:
            for datafile in child.iter_datafiles():
                yield datafile

    def save(self):
        self._chief_controller.serialize_controller(self)

    def get_local_variables(self):
        return {}



class TestDataDirectoryController(_DataController):

    def _children(self, data):
        return [DataController(child, self._chief_controller) for child in data.children]

    def has_format(self):
        return self.data.initfile is not None

    def add_suite(self, source):
        if os.path.isdir(source):
            d = TestDataDirectory()
        else:
            d = TestCaseFile()
        d.source = source
        self.data.children.append(d)
        return DataController(d, self._chief_controller)

    @property
    def source(self):
        return self.data.initfile

    def set_format(self, format):
        self.data.initfile = os.path.join(self.data.source, '__init__.%s' % format.lower())
        self.mark_dirty()

    def new_datafile(self, datafile):
        self.children.append(DataController(datafile, self._chief_controller))
        return self.children[-1]

    def is_directory_suite(self):
        return True

    def reload(self):
        self.__init__(TestDataDirectory(source=self.directory), self._chief_controller)


class TestCaseFileController(_DataController):

    def _children(self, data):
        return []

    def _settings(self):
        ss = self.data.setting_table
        return _DataController._settings(self) + \
                [TagsController(self, ss.default_tags),
                 TimeoutController(self, ss.test_timeout),
                 TemplateController(self, ss.test_template)]

    def create_test(self, name):
        return self.tests.new(name)

    def validate_test_name(self, name):
        return self.tests.validate_name(name)

    def reload(self):
        self.__init__(TestCaseFile(source=self.source), self._chief_controller)


class ResourceFileController(_DataController):

    def _settings(self):
        return [DocumentationController(self, self.data.setting_table.doc)]

    def _children(self, data):
        return []

    def validate_name(self, name):
        for uk in self.data.keyword_table.keywords:
            if uk != name and utils.eq(uk.name, name):
                return 'User keyword with this name already exists.'
        return None

    def reload(self):
        self.__init__(ResourceFile(source=self.source), self._chief_controller)
