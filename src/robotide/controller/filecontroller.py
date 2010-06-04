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

from robotide.robotapi import TestCaseFile
from robot.parsing.datareader import DataRow
from robot.parsing.populator import UserKeywordPopulator

from robotide.controller.settingcontroller import (DocumentationController,
        FixtureController, TagsController, TimeoutController, TemplateController,
        ArgumentsController, MetadataController, ImportController)


def DataController(data):
    return TestCaseFileController(data) if isinstance(data, TestCaseFile) \
        else TestDataDirectoryController(data)


class _DataController(object):

    def __init__(self, data):
        self.data = data
        self.dirty = False
        self.children = self._children(data)

    @property
    def settings(self):
        return self._settings()

    def _settings(self):
        ss = self.data.setting_table
        return [DocumentationController(self, ss.doc),
                FixtureController(self, ss.suite_setup, 'Suite Setup'),
                FixtureController(self, ss.suite_teardown, 'Suite Teardown'),
                FixtureController(self, ss.test_setup, 'Test Setup'),
                FixtureController(self, ss.test_teardown, 'Test Teardown'),
                TagsController(self, ss.force_tags, 'Force Tags'),
                ]

    @property
    def variables(self):
        return VariableTableController(self.data.variable_table)

    @property
    def tests(self):
        return TestCaseTableController(self, self.data.testcase_table)

    @property
    def datafile(self):
        return self.data

    @property
    def keywords(self):
        return KeywordTableController(self, self.data.keyword_table)

    @property
    def imports(self):
        return ImportSettingsController(self.data.setting_table)

    @property
    def metadata(self):
        return MetadataListController(self.data.setting_table)

    def has_been_modified_on_disk(self):
        return False

    def mark_dirty(self):
        self.dirty = True


class TestDataDirectoryController(_DataController):

        def _children(self, data):
            return [DataController(child) for child in data.children]


class TestCaseFileController(_DataController):

    def _children(self, data):
        return []

    def _settings(self):
        ss = self.data.setting_table
        return _DataController._settings(self) + \
                [TimeoutController(self, ss.test_timeout, 'Test Timeout'),
                 TemplateController(self, ss.test_template, 'Test Template')]



class _TableController(object):
    def __init__(self, parent_controller, table):
        self._parent = parent_controller
        self._table = table

    def mark_dirty(self):
        self._parent.mark_dirty()

    @property
    def dirty(self):
        return self._parent.dirty

    @property
    def datafile(self):
        return self._parent.datafile


class VariableTableController(object):
    def __init__(self, variables):
        self._variables = variables
    def __iter__(self):
        return iter(VariableController(v) for v in self._variables)
    @property
    def datafile(self):
        return self._variables.parent


class VariableController(object):
    def __init__(self, var):
        self._var = var
        self.name = var.name
        self.value= var.value


class MetadataListController(object):
    def __init__(self, setting_table):
        self._table = setting_table
    def __iter__(self):
        return iter(MetadataController(m) for m in self._table.metadata)
    @property
    def datafile(self):
        return self._table.parent


class TestCaseTableController(_TableController):
    def __iter__(self):
        return iter(TestCaseController(t) for t in self._table)


class TestCaseController(object):
    def __init__(self, test):
        self.data = self._test = test

    @property
    def settings(self):
        return [DocumentationController(self, self._test.doc),
                FixtureController(self, self._test.setup, 'Setup'),
                FixtureController(self, self._test.teardown, 'Teardown'),
                TagsController(self, self._test.tags, 'Tags'),
                TimeoutController(self, self._test.timeout, 'Timeout'),
                TemplateController(self, self._test.template, 'Template')]

    @property
    def name(self):
        return self._test.name

    @property
    def datafile(self):
        return self._test.parent.parent

    @property
    def steps(self):
        return self._test.steps

    def mark_dirty(self):
        self._parent.mark_dirty()


class KeywordTableController(_TableController):
    def __iter__(self):
        return iter(UserKeywordController(self, kw) for kw in self._table)


class UserKeywordController(object):
    def __init__(self, parent_controller, kw):
        self._parent = parent_controller
        self.data = self._kw = kw

    @property
    def settings(self):
        return [DocumentationController(self, self._kw.doc),
                ArgumentsController(self, self._kw.args, 'Arguments'),
                TimeoutController(self, self._kw.timeout, 'Timeout'),
                # TODO: Wrong class, works right though
                ArgumentsController(self, self._kw.return_, 'Return Value')]

    @property
    def name(self):
        return self._kw.name

    @property
    def datafile(self):
        return self._parent.datafile

    @property
    def steps(self):
        return self._kw.steps

    def mark_dirty(self):
        self._parent.mark_dirty()

    @property
    def dirty(self):
        return self._parent.dirty

    def parse_steps_from_rows(self, rows):
        self._kw.steps = []
        pop = UserKeywordPopulator(lambda name: self._kw)
        for r in rows:
            r = DataRow([''] + r)
            pop.add(r)
        pop.populate()


class ImportSettingsController(object):
    def __init__(self, setting_table):
        self._table = setting_table
    def __iter__(self):
        return iter(ImportController(imp) for imp in self._table.imports)
    @property
    def datafile(self):
        return self._table.parent
