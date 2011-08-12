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
from itertools import chain
from robotide.controller.basecontroller import WithUndoRedoStacks,\
    _BaseController
from robotide.controller.settingcontrollers import DocumentationController,\
    FixtureController, TimeoutController, TemplateController,\
    DefaultTagsController, ForceTagsController
from robotide.controller.tablecontrollers import VariableTableController, \
    TestCaseTableController, KeywordTableController, ImportSettingsController, \
    MetadataListController, TestCaseController
from robotide.publish import RideDataFileRemoved, RideInitFileRemoved
from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile
from robotide import utils
from robotide.publish.messages import RideDataChangedToDirty,\
    RideDataDirtyCleared, RideSuiteAdded, RideItemSettingsChanged
from robotide.controller.macrocontrollers import UserKeywordController

def DataController(data, chief, parent=None):
    return TestCaseFileController(data, chief, parent) if isinstance(data, TestCaseFile) \
        else TestDataDirectoryController(data, chief, parent)


class _FileSystemElement(object):

    def __init__(self, source):
        self._stat = self._get_stat(source)

    def _get_stat(self, path):
        if path and os.path.isfile(path):
            stat = os.stat(path)
            return (stat.st_mtime, stat.st_size)
        return (0, 0)

    def has_been_modified_on_disk(self):
        return self._get_stat(self.source) != self._stat

    def has_been_removed_from_disk(self):
        return self._stat != (0, 0) and not os.path.isfile(self.source)


class _DataController(_FileSystemElement, _BaseController, WithUndoRedoStacks):

    def __init__(self, data, chief_controller=None, parent=None):
        self._chief_controller = chief_controller
        self.parent = parent
        self.data = data
        _FileSystemElement.__init__(self, self.source)
        self.dirty = False
        self.children = self._children(data)
        self._variables_table_controller = None
        self._testcase_table_controller = None

    def _children(self, data):
        return []

    @property
    def name(self):
        return self.data.name

    @property
    def source(self):
        return self.data.source if self.data else None

    @property
    def short_source(self):
        return os.path.basename(self.data.source)

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
                self.force_tags]

    @property
    def _setting_table(self):
        return self.data.setting_table

    @property
    def force_tags(self):
        return ForceTagsController(self, self._setting_table.force_tags)

    @property
    def variables(self):
        if self._variables_table_controller is None:
            self._variables_table_controller = VariableTableController(self, self.data.variable_table)
        return self._variables_table_controller

    @property
    def tests(self):
        if self._testcase_table_controller is None:
            self._testcase_table_controller = TestCaseTableController(self, self.data.testcase_table)
        return self._testcase_table_controller

    @property
    def datafile(self):
        return self.data

    @property
    def datafiles(self):
        return chain([self], (df for df in self._chief_controller.datafiles if df != self))

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

    def update_namespace(self):
        if self._chief_controller is not None:
            self._chief_controller.update_namespace()

    def register_for_namespace_updates(self, listener):
        if self._chief_controller is not None:
            self._chief_controller.register_for_namespace_updates(listener)

    def unregister_namespace_updates(self, listener):
        if self._chief_controller is not None:
            self._chief_controller.unregister_namespace_updates(listener)

    def is_user_keyword(self, value):
        return self._chief_controller.is_user_keyword(self.datafile, value)

    def is_library_keyword(self, value):
        return self._chief_controller.is_library_keyword(self.datafile, value)

    def keyword_info(self, keyword_name):
        return self._chief_controller.keyword_info(self.data, keyword_name)

    def mark_dirty(self):
        if not self.dirty:
            self.dirty = True
            RideDataChangedToDirty(datafile=self).publish()

    def unmark_dirty(self):
        self._stat = self._get_stat(self.source)
        if self.dirty:
            self.dirty = False
            RideDataDirtyCleared(datafile=self).publish()

    def create_keyword(self, name, argstr=''):
        return self.keywords.new(name, argstr)

    def add_test_or_keyword(self, item):
        if isinstance(item, TestCaseController):
            self.tests.add(item)
            item.set_parent(self.tests)
        elif isinstance(item, UserKeywordController):
            self.keywords.add(item)
            item.set_parent(self.keywords)
        else:
            self.variables.add_variable(item.name, item.value, item.comment)

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
    def directory(self):
        return self.data.directory

    def is_directory_suite(self):
        return False

    def resource_import_modified(self, path):
        return self._chief_controller.resource_import_modified(path, self.directory)

    def notify_settings_changed(self):
        RideItemSettingsChanged(item=self).publish()

    def notify_steps_changed(self):
        for test in self.tests:
            test.notify_steps_changed()

    def iter_datafiles(self):
        yield self
        for child in self.children:
            for datafile in child.iter_datafiles():
                yield datafile

    def save(self):
        self._chief_controller.serialize_controller(self)

    def get_local_variables(self):
        return {}

    def is_inside_top_suite(self, res):
        return False


class DirectoryController(_FileSystemElement, _BaseController):

    def __init__(self, path, chief_controller):
        _FileSystemElement.__init__(self, path)
        self.directory = self.source = path
        self._chief_controller = chief_controller
        self.children = []
        self.data = None
        self.dirty = False
        self._dir_controllers = {}

    def is_directory_suite(self):
        return False

    def add_child(self, child):
        self.children.append(child)

    def iter_datafiles(self):
        yield self

    @property
    def display_name(self):
        return os.path.split(self.directory)[1]

    @property
    def default_dir(self):
        return self.directory

    def new_resource(self, path):
        return self._chief_controller.new_resource(path, parent=self)


class TestDataDirectoryController(_DataController, DirectoryController):

    def __init__(self, data, chief_controller=None, parent=None):
        _DataController.__init__(self, data, chief_controller, parent)
        self._dir_controllers = {}

    @property
    def default_dir(self):
        return self.data.source

    @property
    def display_name(self):
        return self.data.name

    def _children(self, data):
        return [DataController(child, self._chief_controller, self)
                for child in data.children]

    def add_child(self, controller):
        self.children.append(controller)

    def has_format(self):
        return self.data.initfile is not None

    @property
    def source(self):
        return self.data.initfile

    def set_format(self, format):
        self.data.initfile = os.path.join(self.data.source, '__init__.%s'
                                          % format.lower())
        self.mark_dirty()

    def new_datafile(self, datafile):
        self.data.children.append(datafile)
        datafile.parent = self.data
        self.children.append(DataController(datafile, self._chief_controller, self))
        return self.children[-1]

    def notify_suite_added(self, suite):
        RideSuiteAdded(parent=self, suite=suite).publish()

    def is_directory_suite(self):
        return True

    def reload(self):
        self.__init__(TestDataDirectory(source=self.directory).populate(),
                      self._chief_controller)

    def remove(self):
        path = self.source
        self.data.initfile = None
        self._stat = self._get_stat(None)
        self.reload()
        RideInitFileRemoved(path=path, datafile=self).publish()

    def remove_child(self, controller):
        if controller in self.children:
            self.children.remove(controller)
        else:
            for child in self.children:
                child.remove_child(controller)

    def is_inside_top_suite(self, ctrl):
        return ctrl.source.startswith(self.directory)

    def insert_to_test_data_directory(self, res):
        res_dir = os.path.dirname(res.source)
        if self._is_inside_test_data_directory(res_dir):
            return
        if res_dir in self._dir_controllers:
            self._dir_controllers[res_dir].add_child(res)
        else:
            target = self._find_closest_directory(res)
            if target is self:
                dir_ctrl = DirectoryController(res_dir, self._chief_controller)
                self._dir_controllers[res_dir] = dir_ctrl
                dir_ctrl.add_child(res)
                target.add_child(dir_ctrl)
            else:
                target.insert_to_test_data_directory(res)

    def _is_inside_test_data_directory(self, directory):
        return any(True for s in [self] + self.children
                   if s.is_directory_suite() and s.directory == directory)

    def _find_closest_directory(self, res):
        target = self
        for s in self.iter_datafiles():
            if not isinstance(s, DirectoryController):
                continue
            if res.source.startswith(s.directory):
                target = s
        return target


class TestCaseFileController(_DataController):

    def _settings(self):
        ss = self._setting_table
        sett = _DataController._settings(self)
        sett.insert(-1, TemplateController(self, ss.test_template))
        sett.insert(-1, TimeoutController(self, ss.test_timeout))
        return sett + [self.default_tags]

    @property
    def default_tags(self):
        return DefaultTagsController(self, self._setting_table.default_tags)

    def create_test(self, name):
        return self.tests.new(name)

    def validate_test_name(self, name):
        return self.tests.validate_name(name)

    def remove_child(self, controller):
        if controller is self:
            self.remove()

    def remove(self):
        self._chief_controller.remove_datafile(self)
        RideDataFileRemoved(path=self.source, datafile=self).publish()

    def reload(self):
        self.__init__(TestCaseFile(source=self.source).populate(),
                      self._chief_controller)

    def get_template(self):
        return self.data.setting_table.test_template


class ResourceFileController(_DataController):

    def __init__(self, data, chief_controller=None, parent=None):
        _DataController.__init__(self, data, chief_controller,
                                 parent or self._find_parent_for(chief_controller, data.source))
        if self.parent:
            self.parent.add_child(self)

    def _find_parent_for(self, chief_controller, source):
        if not chief_controller:
            return None
        dir = os.path.dirname(source)
        for ctrl in chief_controller.datafiles:
            if ctrl.is_directory_suite() and ctrl.directory == dir:
                return ctrl
        return None

    @property
    def display_name(self):
        _, tail = os.path.split(self.data.source)
        return tail

    def _settings(self):
        return [DocumentationController(self, self.data.setting_table.doc)]

    def validate_name(self, name):
        for uk in self.data.keyword_table.keywords:
            if uk != name and utils.eq(uk.name, name):
                return 'User keyword with this name already exists.'
        return None

    def reload(self):
        self.__init__(ResourceFile(source=self.source).populate(),
                      self._chief_controller)

    def remove(self):
        self._chief_controller.remove_resource(self)
        RideDataFileRemoved(path=self.source, datafile=self).publish()
