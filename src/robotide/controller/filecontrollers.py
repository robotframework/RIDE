#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

from robotide.publish import (RideDataFileRemoved, RideInitFileRemoved,
        RideDataChangedToDirty, RideDataDirtyCleared, RideSuiteAdded,
        RideItemSettingsChanged)
from robotide.publish.messages import RideDataFileSet
from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile
from robotide import utils

from .basecontroller import WithUndoRedoStacks, _BaseController, WithNamespace
from .macrocontrollers import UserKeywordController
from .robotdata import NewTestCaseFile, NewTestDataDirectory
from .settingcontrollers import (DocumentationController, FixtureController,
        TimeoutController, TemplateController, DefaultTagsController,
        ForceTagsController)
from .tablecontrollers import (VariableTableController, TestCaseTableController,
        KeywordTableController, ImportSettingsController,
        MetadataListController, TestCaseController)


def DataController(data, chief, parent=None):
    return TestCaseFileController(data, chief, parent) if isinstance(data, TestCaseFile) \
        else TestDataDirectoryController(data, chief, parent)


class _FileSystemElement(object):

    def __init__(self, filename, directory):
        self.filename = filename
        self.directory = directory
        self._stat = self._get_stat(filename)

    def _get_stat(self, path):
        if path and os.path.isfile(path):
            stat = os.stat(path)
            return stat.st_mtime, stat.st_size
        return 0, 0

    def refresh_stat(self):
        self._stat = self._get_stat(self.filename)

    def has_been_modified_on_disk(self):
        return self._get_stat(self.filename) != self._stat

    def has_been_removed_from_disk(self):
        return self._stat != (0, 0) and not os.path.isfile(self.filename)

    @property
    def basename(self):
        return os.path.splitext(os.path.basename(self.filename))[0]

    @property
    def source(self):
        """Deprecated, use ``filename`` or ``directory`` instead."""
        # Todo: remove when backwards compatibility with plugin API can break
        return self.filename or self.directory


class _DataController(_BaseController, WithUndoRedoStacks, WithNamespace):

    def __init__(self, data, chief_controller=None, parent=None):
        self._chief_controller = chief_controller
        if chief_controller:
            self._set_namespace_from(chief_controller)
            self._resource_file_controller_factory =\
                chief_controller.resource_file_controller_factory
        else:
            self._resource_file_controller_factory = None
        self.parent = parent
        self.set_datafile(data)
        self.dirty = False
        self.children = self._children(data)

    def set_datafile(self, datafile):
        self.data = datafile
        self._variables_table_controller = None
        self._testcase_table_controller = None
        self._keywords_table_controller = None
        self._imports = None
        RideDataFileSet(item=self).publish()

    def _children(self, data):
        return []

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
            self._variables_table_controller = \
                    VariableTableController(self, self.data.variable_table)
        return self._variables_table_controller

    @property
    def tests(self):
        if self._testcase_table_controller is None:
            self._testcase_table_controller = \
                    TestCaseTableController(self, self.data.testcase_table)
        return self._testcase_table_controller

    @property
    def datafile(self):
        return self.data

    @property
    def datafiles(self):
        return chain([self], (df for df in self._chief_controller.datafiles
                              if df != self))

    @property
    def datafile_controller(self):
        return self

    @property
    def keywords(self):
        if self._keywords_table_controller is None:
            self._keywords_table_controller = \
                    KeywordTableController(self, self.data.keyword_table)
        return self._keywords_table_controller

    @property
    def imports(self):
        if not self._imports:
            self._imports = ImportSettingsController(self, self.data.setting_table,
                                    self._resource_file_controller_factory)
        return self._imports

    @property
    def metadata(self):
        return MetadataListController(self, self.data.setting_table)

    def is_user_keyword(self, value):
        return WithNamespace.is_user_keyword(self, self.datafile, value)

    def is_library_keyword(self, value):
        return WithNamespace.is_library_keyword(self, self.datafile, value)

    def keyword_info(self, keyword_name):
        return WithNamespace.keyword_info(self, self.data, keyword_name)

    def mark_dirty(self):
        if not self.dirty:
            self.dirty = True
            RideDataChangedToDirty(datafile=self).publish()

    def unmark_dirty(self):
        self.refresh_stat()
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
        if not self.filename:
            return None
        return os.path.splitext(self.filename)[1].replace('.', '')

    def set_format(self, format):
        self.data.source = utils.replace_extension(self.filename, format)
        self.filename = self.data.source

    def is_same_format(self, format):
        if format and self.has_format():
            return format.lower() == self.get_format().lower()
        return False

    def set_basename(self, basename):
        old_file = self.filename
        self.data.source = os.path.join(self.directory, '%s.%s' % (basename, self.get_format()))
        self.filename = self.data.source
        self.save()
        if old_file != self.filename:
            self.remove_from_filesystem(old_file)

    def remove_from_filesystem(self, path=None):
        os.remove(path or self.filename)

    def save_with_new_format(self, format):
        self._chief_controller.change_format(self, format)

    def save_with_new_format_recursive(self, format):
        self._chief_controller.change_format_recursive(self, format)

    def validate_keyword_name(self, name):
        return self.keywords.validate_name(name)

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
        self._chief_controller.save(self)

    def get_local_variables(self):
        return {}

    def is_inside_top_suite(self, res):
        return False


class DirectoryController(_FileSystemElement, _BaseController):

    def __init__(self, path, chief_controller):
        _FileSystemElement.__init__(self, path, path)
        self.directory = path
        self.settings = self.tests = self.keywords = ()
        self._chief_controller = chief_controller
        self.children = []
        self.data = None
        self.imports = ()
        self.datafile = None
        self.dirty = False
        self._dir_controllers = {}

    def is_directory_suite(self):
        return False

    def is_same_format(self, other):
        return True

    def add_child(self, child):
        self.children.append(child)

    def iter_datafiles(self):
        yield self
        for child in self.children:
            for datafile in child.iter_datafiles():
                yield datafile

    @property
    def display_name(self):
        return os.path.split(self.directory)[1]

    @property
    def name(self):
        return self.display_name

    @property
    def default_dir(self):
        return self.directory

    def new_resource(self, path):
        return self._chief_controller.new_resource(path, parent=self)

    def keyword_info(self, name):
        return None

    def insert_to_test_data_directory(self, res):
        res_dir = os.path.dirname(res.filename)
        if res_dir in self._dir_controllers:
            self._dir_controllers[res_dir].add_child(res)
        else:
            target = self._find_closest_directory(res)
            if target is self:
                self._create_target_dir_controller(res, res_dir, target)
            else:
                target.insert_to_test_data_directory(res)

    def _find_closest_directory(self, res):
        target = self
        for s in self.iter_datafiles():
            if not isinstance(s, DirectoryController):
                continue
            if res.filename.startswith(s.directory):
                target = s
        return target

    def _create_target_dir_controller(self, res, res_dir, target):
        for dirname in res_dir[len(self.directory):].split(os.sep):
            if not dirname:
                continue
            target_dir = os.path.join(target.directory, dirname)
            dir_ctrl = DirectoryController(target_dir, self._chief_controller)
            target._dir_controllers[target.directory] = dir_ctrl
            target.add_child(dir_ctrl)
            if target_dir == res_dir:
                dir_ctrl.add_child(res)
                return
            target = dir_ctrl
        self.add_child(res)


class TestDataDirectoryController(_DataController, DirectoryController):

    def __init__(self, data, chief_controller=None, parent=None):
        dir_ = data.directory
        dir_ = os.path.abspath(dir_) if isinstance(dir_, basestring) else dir_
        _FileSystemElement.__init__(self, self._filename(data), dir_)
        _DataController.__init__(self, data, chief_controller, parent)
        self._dir_controllers = {}

    def _filename(self, data):
        return data.initfile

    @property
    def default_dir(self):
        return self.data.source

    @property
    def display_name(self):
        return self.data.name

    @property
    def longname(self):
        if self.parent:
            return self.parent.longname + '.' + self.display_name
        return self.display_name

    @property
    def suites(self):
        return [child for child in self.children if
                    isinstance(child, TestDataDirectoryController) or
                    isinstance(child, TestCaseFileController)]

    def _children(self, data):
        return [DataController(child, self._chief_controller, self)
                for child in data.children]

    def add_child(self, controller):
        self.children.append(controller)

    def has_format(self):
        return self.data.initfile is not None

    def set_format(self, format):
        self.data.initfile = os.path.join(self.data.source, '__init__.%s'
                                          % format.lower())
        self.filename = self.data.initfile

    def new_test_case_file(self, path):
        return self._new_data_controller(NewTestCaseFile(path))

    def new_test_data_directory(self, path):
        return self._new_data_controller(NewTestDataDirectory(path))

    def _new_data_controller(self, datafile):
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
        path = self.filename
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
        return ctrl.filename.startswith(self.directory)

    def insert_to_test_data_directory(self, res):
        if self._is_inside_test_data_directory(os.path.dirname(res.filename)):
            return
        DirectoryController.insert_to_test_data_directory(self, res)

    def _is_inside_test_data_directory(self, directory):
        return any(True for s in [self] + self.children
                   if s.is_directory_suite() and s.directory == directory)


class TestCaseFileController(_FileSystemElement, _DataController):

    def __init__(self, data, chief_controller=None, parent=None):
        _FileSystemElement.__init__(self, data.source if data else None, data.directory)
        _DataController.__init__(self, data, chief_controller, parent)

    def _settings(self):
        ss = self._setting_table
        sett = _DataController._settings(self)
        sett.insert(-1, TemplateController(self, ss.test_template))
        sett.insert(-1, TimeoutController(self, ss.test_timeout))
        return sett + [self.default_tags]

    @property
    def longname(self):
        if self.parent:
            return self.parent.longname + '.' + self.name
        return self.name

    @property
    def suites(self):
        return ()

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
        RideDataFileRemoved(path=self.filename, datafile=self).publish()

    def reload(self):
        self.__init__(TestCaseFile(source=self.filename).populate(),
                      self._chief_controller)

    def get_template(self):
        return self.data.setting_table.test_template


class ResourceFileControllerFactory(object):

    def __init__(self, namespace):
        self._resources = []
        self._namespace = namespace

    @property
    def resources(self):
        return self._resources

    def find(self, data):
        return self._find_with_source(data.source)

    def _find_with_source(self, source):
        for other in self.resources:
            if other.filename == source:
                return other
        return None

    def find_with_import(self, import_):
        resource_model = self._namespace.find_resource_with_import(import_)
        if not resource_model:
            return None
        res = self.find(resource_model)
        return res

    def create(self, data, chief_controller=None, parent=None):
        rfc = ResourceFileController(data, chief_controller, parent)
        self.resources.append(rfc)
        return rfc

    def remove(self, controller):
        self._resources.remove(controller)


class ResourceFileController(_FileSystemElement, _DataController):

    def __init__(self, data, chief_controller=None, parent=None):
        _FileSystemElement.__init__(self, data.source if data else None, data.directory)
        _DataController.__init__(self, data, chief_controller,
                                 parent or self._find_parent_for(chief_controller, data.source))
        if self.parent:
            self.parent.add_child(self)

    def _find_parent_for(self, chief_controller, source):
        if not chief_controller:
            return None
        dir = os.path.dirname(source)
        for ctrl in chief_controller.datafiles:
            if ctrl.is_directory_suite() and self._to_os_style(ctrl.directory) == dir:
                return ctrl
        return None

    def _to_os_style(self, path):
        return path.replace('/', os.sep)

    @property
    def display_name(self):
        _, tail = os.path.split(self.data.source)
        return tail

    def set_format(self, format):
        self._modify_file_name(lambda: _DataController.set_format(self, format),
                               lambda imp: imp.change_format(format))

    def set_basename(self, basename):
        self._modify_file_name(lambda: _DataController.set_basename(self, basename),
                               lambda imp: imp.unresolve())

    def set_basename_and_modify_imports(self, basename):
        old = self.filename
        self._modify_file_name(lambda: _DataController.set_basename(self, basename),
                               lambda imp: imp.change_name(os.path.basename(old), os.path.basename(self.filename)))

    def remove_static_imports_to_this(self):
        name = os.path.basename(self.filename)
        for resource_import in self.get_where_used():
            if resource_import.name.endswith(name):
                resource_import.remove()

    def _modify_file_name(self, modification, notification):
        old = self.filename
        modification()
        for resource_import in self.get_where_used():
            notification(resource_import)
        self._namespace.resource_filename_changed(old, self.filename)

    def _settings(self):
        return [DocumentationController(self, self.data.setting_table.doc)]

    def validate_name(self, name):
        for uk in self.data.keyword_table.keywords:
            if uk != name and utils.eq(uk.name, name):
                return 'User keyword with this name already exists.'
        return None

    def reload(self):
        self.__init__(ResourceFile(source=self.filename).populate(),
                      self._chief_controller)

    def remove(self):
        self._chief_controller.remove_resource(self)
        RideDataFileRemoved(path=self.filename, datafile=self).publish()

    def get_where_used(self):
        for imp in self._all_imports():
            if imp.get_imported_controller() is self:
                yield imp

    def _all_imports(self):
        for df in self.datafiles:
            for imp in df.imports:
                yield imp
