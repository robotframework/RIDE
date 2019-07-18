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

import os
import sys
import stat
from itertools import chain
import shutil
import robotide.controller.ctrlcommands
try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess
from robotide.controller.dataloader import ExcludedDirectory, TestData

from robotide.publish import (RideDataFileRemoved, RideInitFileRemoved,
        RideDataChangedToDirty, RideDataDirtyCleared, RideSuiteAdded,
        RideItemSettingsChanged)
from robotide.publish.messages import RideDataFileSet, RideOpenResource
from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile
from robotide import utils

from .basecontroller import WithUndoRedoStacks, _BaseController, WithNamespace, ControllerWithParent
from .macrocontrollers import UserKeywordController
from .robotdata import NewTestCaseFile, NewTestDataDirectory
from robotide.utils import overrides
from .settingcontrollers import (DocumentationController, FixtureController,
        TimeoutController, TemplateController, DefaultTagsController,
        ForceTagsController)
from .tablecontrollers import (VariableTableController, TestCaseTableController,
        KeywordTableController, ImportSettingsController,
        MetadataListController, TestCaseController)
from robotide.utils import PY3
if PY3:
    from robotide.utils import basestring


def _get_controller(project, data, parent):
    if isinstance(data, TestCaseFile):
        return TestCaseFileController(data, project, parent)
    if isinstance(data, ExcludedDirectory):
        return ExcludedDirectoryController(data, project, parent)
    return TestDataDirectoryController(data, project, parent)


def DataController(data, project, parent=None):
    return _get_controller(project, data, parent)


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
        return self._stat != (0, 0) and not self.exists()

    def relative_path_to(self, other):
        other_path = os.path.join(other.directory, other.filename)
        return os.path.relpath(other_path, start=self.directory).replace('\\', '/')

    def is_readonly(self):
        return not os.access(self.filename, os.W_OK)

    def exists(self):
        return self.filename and os.path.isfile(self.filename)

    @property
    def basename(self):
        return os.path.splitext(os.path.basename(self.filename))[0]

    @property
    def source(self):
        """Deprecated, use ``filename`` or ``directory`` instead."""
        # Todo: remove when backwards compatibility with plugin API can break
        return self.filename or self.directory


class _DataController(_BaseController, WithUndoRedoStacks, WithNamespace):

    def __init__(self, data, project=None, parent=None):
        self._project = project
        if project:
            self._set_namespace_from(project)
            self._resource_file_controller_factory =\
                project.resource_file_controller_factory
        else:
            self._resource_file_controller_factory = None
        self.parent = parent
        self.set_datafile(data)
        self.dirty = False
        self.children = self._children(data)
        # Filename needs to be set when creating a new datafile
        if hasattr(self.data, 'initfile'):
            self.filename = self.data.initfile
        else:
            self.filename = self.data.source

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
        return chain([self], (df for df in self._project.datafiles
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

    def sort_keywords(self):
        if self.keywords:
            index_difference = self.keywords.sort()
            self.mark_dirty()
            RideDataFileSet(item=self).publish() #TODO: Use a more gentle message
            return index_difference
        return None

    def restore_keyword_order(self, index_difference):
        if self.keywords and index_difference:
            self.keywords.restore_keyword_order(index_difference)
            self.mark_dirty()
            RideDataFileSet(item=self).publish() #TODO: Use a more gentle message

    def get_keyword_names(self):
        if self.keywords:
            return [kw.name for kw in self.keywords._items]
        return None

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
        self.execute(robotide.controller.ctrlcommands.SaveFile())
        if old_file != self.filename:
            self.remove_from_filesystem(old_file)

    def remove_readonly(self, path=None):
            path = path or self.filename
            os.chmod(path, stat.S_IWRITE)

    def open_filemanager(self, path=None):
        # tested on Win7 x64
        path = path or self.filename
        if os.path.exists(path):
            if sys.platform == 'win32':
                #  There was encoding errors if directory had unicode chars
                # TODO test on all OS directory names with accented chars, for example 'ccedilla'
                os.startfile(r"%s" % os.path.dirname(path), 'explore')
            elif sys.platform.startswith('linux'):
                # how to detect which explorer is used?
                # nautilus, dolphin, konqueror
                # TODO check if explorer exits
                # TODO get prefered explorer from preferences
                try:
                    subprocess.Popen(["nautilus", "{}".format(
                        os.path.dirname(path))])
                except OSError or FileNotFoundError:
                    try:
                        subprocess.Popen(
                            ["dolphin", "{}".format(os.path.dirname(path))])
                    except OSError or FileNotFoundError:
                        try:
                            subprocess.Popen(
                               ["konqueror", "{}".format(
                                   os.path.dirname(path))])
                        except OSError or FileNotFoundError:
                            print("Could not launch explorer. Tried nautilus, "
                                  "dolphin and konqueror.")
            else:
                try:
                    subprocess.Popen(["finder", "{}".format(
                        os.path.dirname(path))])
                except OSError or FileNotFoundError:
                    subprocess.Popen(["open", "{}".format(
                        os.path.dirname(path))])

    def remove_from_filesystem(self, path=None):
        path = path or self.filename
        if os.path.exists(path):
            os.remove(path)

    def remove_folder_from_filesystem(self, path=None):
        shutil.rmtree(path or self.data.directory)

    def save_with_new_format(self, format):
        self._project.change_format(self, format)

    def save_with_new_format_recursive(self, format):
        self._project.change_format_recursive(self, format)

    def validate_keyword_name(self, name):
        return self.keywords.validate_name(name)

    def is_directory_suite(self):
        return False

    def resource_import_modified(self, path):
        return self._project.resource_import_modified(path, self.directory)

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
        self._project.save(self)

    def get_local_variables(self):
        return {}

    def is_inside_top_suite(self, res):
        return False


class TestDataDirectoryController(_DataController, _FileSystemElement, _BaseController):

    def __init__(self, data, project=None, parent=None):
        dir_ = data.directory
        dir_ = os.path.abspath(dir_) if isinstance(dir_, basestring) else dir_
        _FileSystemElement.__init__(self, self._filename(data), dir_)
        _DataController.__init__(self, data, project, parent)
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

    def add_child(self, child):
        self.children.append(child)

    def contains_tests(self):
        for suite in self.suites:
            if suite.contains_tests():
                return True
        return False

    def find_controller_by_longname(self, longname, testname = None):
        return self.find_controller_by_names(longname.split("."), testname)

    def find_controller_by_names(self, names, testname):
        namestring = '.'.join(names)
        if not namestring.startswith(self.name):
            return None
        if namestring == self.name:
            return self
        for suite in self.suites:
            res = suite.find_controller_by_names(namestring[len(self.name)+1:].split('.'), testname)
            if res:
                return res

    def is_excluded(self):
        return self._project.is_excluded(self.source) if self._project else False

    def _children(self, data):
        children = [DataController(child, self._project, self) for child in data.children]
        if self._can_add_directory_children(data):
            self._add_directory_children(children, data.source, data.initfile)
        return children

    def _can_add_directory_children(self, data):
        return data.source and os.path.isdir(data.source) and self._namespace

    def _add_directory_children(self, children, path, initfile):
        for filename in self._get_unknown_files_in_directory(children, path, initfile):
            if not self._is_robot_ignored_name(filename):
                self._add_directory_child(children, filename)

    def _is_robot_ignored_name(self, filename):
        base = os.path.basename(filename)
        return any(base.startswith(c) for c in '_.')

    def _add_directory_child(self, children, filename):
        if os.path.isdir(filename):
            children.append(self._directory_controller(filename))
        else:
            r = self._namespace.get_resource(filename, report_status=False)
            if self._is_valid_resource(r):
                children.append(self._resource_controller(r))

    def _directory_controller(self, path):
        dc = TestDataDirectoryController(TestDataDirectory(source=path),
                                         project=self._project,
                                         parent=self)
        self._add_directory_children(dc.children, dc.source, None)
        return dc

    def _is_valid_resource(self, resource):
        return resource and (resource.setting_table or resource.variable_table or resource.keyword_table or os.stat(resource.source)[6]==0)

    def _resource_controller(self, resource):
        resource_control =  self._resource_file_controller_factory.create(resource)
        resource_control.parent = self
        return resource_control

    def _get_unknown_files_in_directory(self, children, path, initfile):
        already_in_use = [c.filename for c in children] + [initfile]
        already_in_use += [c.directory for c in children]
        return [f for f in self._get_filenames_in_directory(path) if f not in already_in_use]

    def _get_filenames_in_directory(self, path):
        return [os.path.join(path, f) for f in os.listdir(path)]

    def add_child(self, controller):
        assert controller not in self.children
        self.children.append(controller)

    def has_format(self):
        return self.data.initfile is not None

    def set_format(self, format):
        self.data.initfile = os.path.join(self.data.source, '__init__.%s'
                                          % format.lower())
        self.filename = self.data.initfile

    def new_test_case_file(self, path):
        ctrl = self._new_data_controller(NewTestCaseFile(path))
        ctrl.mark_dirty()
        return ctrl

    def new_test_data_directory(self, path):
        return self._new_data_controller(NewTestDataDirectory(path))

    def _new_data_controller(self, datafile):
        self.data.children.append(datafile)
        datafile.parent = self.data
        self.children.append(DataController(datafile, self._project, self))
        return self.children[-1]

    def notify_suite_added(self, suite):
        RideSuiteAdded(parent=self, suite=suite).publish()

    def is_directory_suite(self):
        return True

    def reload(self):
        self.__init__(TestDataDirectory(source=self.directory, parent=self.data.parent).populate(),
                      self._project, parent=self.parent)

    def remove(self):
        path = self.filename
        self.data.initfile = None
        self._stat = self._get_stat(None)
        self.reload()
        RideInitFileRemoved(path=path, datafile=self).publish()

    def _remove_resources(self):
        for resource in self._find_resources_recursively(self):
            self._project.remove_resource(resource)
            RideDataFileRemoved(path=resource.filename, datafile=resource).publish()

    def remove_from_model(self):
        self._project.remove_datafile(self)
        self._remove_resources()
        RideDataFileRemoved(path=self.filename, datafile=self).publish()

    def remove_child(self, controller):
        if controller in self.children:
            self.children.remove(controller)
        else:
            for child in self.children:
                child.remove_child(controller)

    def is_inside_top_suite(self, ctrl):
        return ctrl.filename.startswith(self.directory)

    def _is_inside_test_data_directory(self, directory):
        return any(True for s in [self] + self.children
                   if s.is_directory_suite() and s.directory == directory)

    def remove_static_imports_to_this(self):
        for resource_import in self.get_where_used():
            resource_import[1].remove()

    def get_where_used(self):
        for imp in self._get_recursive_imports():
            yield imp

    def _all_imports(self):
        for df in self.datafiles:
            for imp in df.imports:
                yield imp

    def _get_recursive_imports(self):
        all_imports = self._all_imports()
        ctrls = self._find_controllers_recursively(self)
        for res in self._find_resources_recursively(self):
            for imp in all_imports:
                if imp.get_imported_controller() == res and imp.parent.parent not in ctrls:
                    yield res, imp

    def _find_resources_recursively(self, controller):
        resources = []
        if controller.children:
            for child in controller.children:
                resources += self._find_resources_recursively(child)
        elif isinstance(controller, ResourceFileController):
            resources.append(controller)
        return resources

    def _find_controllers_recursively(self, controller):
        resources = []
        if controller.children:
            for child in controller.children:
                resources += self._find_controllers_recursively(child)
        resources.append(controller)
        return resources

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
            if not isinstance(s, TestDataDirectoryController):
                continue
            if res.filename.startswith(s.directory):
                target = s
        return target

    def _create_target_dir_controller(self, res, res_dir, target):
        for dirname in res_dir[len(self.directory):].split(os.sep):
            if not dirname:
                continue
            target_dir = os.path.join(target.directory, dirname)
            dir_ctrl = TestDataDirectoryController(TestDataDirectory(source=target_dir), self._project, self)
            target._dir_controllers[target.directory] = dir_ctrl
            target.add_child(dir_ctrl)
            if target_dir == res_dir:
                dir_ctrl.add_child(res)
                return
            target = dir_ctrl
        if res not in self.children:
            self.add_child(res)

    def new_resource(self, path):
        ctrl = self._project.new_resource(path, parent=self)
        ctrl.mark_dirty()
        return ctrl

    def exclude(self):
        if self._project.is_datafile_dirty(self):
            raise DirtyRobotDataException()
        self._project._settings.excludes.update_excludes([self.directory])
        index = self.parent.children.index(self)
        result = ExcludedDirectoryController(self.data, self._project, self.parent)
        self.parent.children[index] = result
        return result


class DirtyRobotDataException(Exception):
    """
    Raised when data is dirty and you are trying to do an operation that requires undirty data.
    """
    pass


class TestCaseFileController(_FileSystemElement, _DataController):

    def __init__(self, data, project=None, parent=None):
        _FileSystemElement.__init__(self, data.source if data else None, data.directory)
        _DataController.__init__(self, data, project, parent)

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

    def contains_tests(self):
        return bool(self.tests)

    def find_controller_by_longname(self, longname, node_testname = None):
        return self.find_controller_by_names(longname.split("."), node_testname)

    def find_controller_by_names(self, names, node_testname = None):
        names = '.'.join(names)
        if not names.startswith(self.name):
            return None
        if len(self.name) < len(names) and not names.startswith(self.name+'.'):
            return None
        if len(names) == 1:
            return self
        for test in self.tests:
            if test.name == node_testname:
                return test
        return None

    @property
    def default_tags(self):
        return DefaultTagsController(self, self._setting_table.default_tags)

    def is_modifiable(self):
        return not self.exists() or not self.is_readonly()

    def create_test(self, name):
        return self.tests.new(name)

    def validate_test_name(self, name):
        return self.tests.validate_name(name)

    def remove_child(self, controller):
        if controller is self:
            self.remove()

    def remove(self):
        self._project.remove_datafile(self)
        RideDataFileRemoved(path=self.filename, datafile=self).publish()

    def reload(self):
        self.__init__(TestCaseFile(parent=self.data.parent, source=self.filename).populate(),
                      project=self._project,
                      parent=self.parent)

    def get_template(self):
        return self.data.setting_table.test_template


class ResourceFileControllerFactory(object):

    def __init__(self, namespace, project):
        self._resources = []
        self._namespace = namespace
        self._project = project
        self._all_resource_imports_resolved = False

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
        if not res:
            res = self.create(resource_model)
            self._project.insert_into_suite_structure(res)
        assert(res is not None)
        return res

    def create(self, data, parent=None):
        rfc = ResourceFileController(data, self._project, parent, self)
        self.resources.append(rfc)
        self.set_all_resource_imports_unresolved()
        return rfc

    def set_all_resource_imports_resolved(self):
        self._all_resource_imports_resolved = True

    def set_all_resource_imports_unresolved(self):
        self._all_resource_imports_resolved = False

    def is_all_resource_file_imports_resolved(self):
        return self._all_resource_imports_resolved

    def remove(self, controller):
        self._resources.remove(controller)
        self.set_all_resource_imports_unresolved()


class ResourceFileController(_FileSystemElement, _DataController):

    def __init__(self, data, project=None, parent=None, resource_file_controller_factory=None):
        self._resource_file_controller_factory = resource_file_controller_factory
        self._known_imports = set()
        _FileSystemElement.__init__(self, data.source if data else None, data.directory)
        _DataController.__init__(self, data, project,
                                 parent or self._find_parent_for(project, data.source))
        if self.parent and self not in self.parent.children:
            self.parent.add_child(self)
        self._unresolve_all_if_none_existing()

    def _unresolve_all_if_none_existing(self):
        if not self.exists() and self._resource_file_controller_factory:
            self._resource_file_controller_factory.set_all_resource_imports_unresolved() # Some import may have referred to this none existing resource

    def _find_parent_for(self, project, source):
        if not project:
            return None
        dir = os.path.dirname(source)
        for ctrl in project.datafiles:
            if ctrl.is_directory_suite() and self._to_os_style(ctrl.directory) == dir:
                return ctrl
        return None

    def _to_os_style(self, path):
        return path.replace('/', os.sep)

    @property
    def display_name(self):
        _, tail = os.path.split(self.data.source)
        return tail

    def is_modifiable(self):
        return not self.exists() or not self.is_readonly()

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
        # have to resolve imports before deleting
        # see: http://code.google.com/p/robotframework-ride/issues/detail?id=1119
        imports = [import_ for import_ in self.get_where_used()]
        for resource_import in imports:
            if resource_import.name.endswith(name):
                resource_import.remove()

    def _modify_file_name(self, modification, notification):
        old = self.filename
        modification()
        resource_imports = [resource_import_ for resource_import_ in self.get_where_used()]
        for resource_import in resource_imports:
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
        self.__init__(ResourceFile(source=self.filename).populate(), self._project, parent=self.parent)

    def remove(self):
        self._project.remove_resource(self)
        RideDataFileRemoved(path=self.filename, datafile=self).publish()

    def remove_known_import(self, _import):
        self._known_imports.remove(_import)

    def add_known_import(self, _import):
        self._known_imports.add(_import)

    def notify_opened(self):
        RideOpenResource(path=self.filename, datafile=self).publish()
        for _import in [ imp for imp in self.imports if imp.is_resource ]:
            _import.import_loaded_or_modified()

    def is_used(self):
        if self._known_imports:
            return True
        if self._resource_file_controller_factory.is_all_resource_file_imports_resolved():
            return False
        return any(self._resolve_known_imports())

    def get_where_used(self):
        if self._resource_file_controller_factory.is_all_resource_file_imports_resolved():
            source = self._known_imports
        else:
            source = self._resolve_known_imports()

        for usage in source:
            yield usage


    def _resolve_known_imports(self):
        for imp in self._all_imports():
            if imp.get_imported_controller() is self:
                yield imp
        self._resource_file_controller_factory.set_all_resource_imports_resolved()

    def _all_imports(self):
        for df in self.datafiles:
            for imp in df.imports:
                yield imp

    def remove_child(self, controller):
        pass

class ExcludedDirectoryController(_FileSystemElement, ControllerWithParent, WithNamespace):

    def __init__(self, data, project, parent):
        self.data = data
        self._project = project
        if self._project:
            self._set_namespace_from(self._project)
            self._resource_file_controller_factory =\
            self._project.resource_file_controller_factory
        else:
            self._resource_file_controller_factory = None
        self._parent = parent
        self.children = []
        self.keywords = []
        self.variables = tuple()
        self.tests = tuple()
        self.imports = tuple()
        _FileSystemElement.__init__(self, '', data.directory)

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
    def dirty(self):
        return False

    def keyword_info(self, keyword_name):
        return WithNamespace.keyword_info(self, self.data, keyword_name)

    @overrides(_BaseController)
    def is_excluded(self):
        return True

    def remove_from_excludes(self):
        self._project._settings.excludes.remove_path(self.source)
        index = self.parent.children.index(self)
        td = TestData(self.data.source, self.parent.data, self._project._settings)
        result = TestDataDirectoryController(td, self._project, self.parent)
        self.parent.children[index] = result
        return result

    def iter_datafiles(self):
        return [self]

    @property
    def name(self):
        return self.data.name

    def is_directory_suite(self):
        return True

    def add_child(self, child):
        self.children.append(child)
