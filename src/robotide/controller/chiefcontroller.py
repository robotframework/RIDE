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
from __future__ import with_statement

import os
import shutil
import tempfile

from robotide.context import LOG, SETTINGS
from robotide.publish.messages import RideOpenResource, RideSaving, RideSaveAll, \
    RideSaved, RideOpenSuite, RideNewProject, RideFileNameChanged

from .basecontroller import WithNamespace, _BaseController
from .dataloader import DataLoader
from .filecontrollers import DataController, ResourceFileControllerFactory
from .robotdata import NewTestCaseFile, NewTestDataDirectory


class ChiefController(_BaseController, WithNamespace):

    def __init__(self, namespace):
        self._set_namespace(namespace)
        self._loader = DataLoader(namespace)
        self._controller = None
        self.name = None
        self.external_resources = []
        self._resource_file_controller_factory = ResourceFileControllerFactory(namespace)
        self._serializer = Serializer(SETTINGS, LOG)

    @property
    def display_name(self):
        return 'Chief'

    @property
    def default_dir(self):
        return os.path.abspath(SETTINGS['default directory'])

    def update_default_dir(self, path):
        default_dir = path if os.path.isdir(path) else os.path.dirname(path)
        SETTINGS.set('default directory', default_dir)

    # TODO: in all other controllers data returns a robot data model object.
    @property
    def data(self):
        return self._controller

    @property
    def suite(self):
        return self._controller.data if self._controller else None

    @property
    def datafiles(self):
        return self._suites() + self.resources

    @property
    def resources(self):
        return self._resource_file_controller_factory.resources

    @property
    def resource_file_controller_factory(self):
        return self._resource_file_controller_factory

    def new_directory_project(self, path):
        self._new_project(NewTestDataDirectory(path))

    def new_file_project(self, path):
        self._new_project(NewTestCaseFile(path))

    def _new_project(self, datafile):
        self.update_default_dir(datafile.directory)
        self._controller = DataController(datafile, self)
        self._resource_file_controller_factory = ResourceFileControllerFactory(self._namespace)
        RideNewProject(path=datafile.source, datafile=datafile).publish()

    def new_resource(self, path, parent=None):
        res = self._namespace.new_resource(path)
        self.update_default_dir(path)
        return self._create_resource_controller(res, parent)

    def load_data(self, path, load_observer):
        if self._load_initfile(path, load_observer):
            return
        if self._load_datafile(path, load_observer):
            return
        if self._load_resource(path, load_observer):
            return
        load_observer.error("Given file '%s' is not a valid Robot Framework "
                            "test case or resource file." % path)

    def _load_initfile(self, path, load_observer):
        if not os.path.splitext(os.path.split(path)[1])[0] == '__init__':
            return None
        initfile = self._loader.load_initfile(path, load_observer)
        if not initfile:
            return None
        self._populate_from_datafile(path, initfile, load_observer)
        return initfile

    def load_datafile(self, path, load_observer):
        datafile = self._load_datafile(path, load_observer)
        if datafile:
            return datafile
        load_observer.error("Invalid data file '%s'." % path)

    def _load_datafile(self, path, load_observer):
        datafile = self._loader.load_datafile(path, load_observer)
        if not datafile:
            return None
        self._populate_from_datafile(path, datafile, load_observer)
        return datafile

    def _populate_from_datafile(self, path, datafile, load_observer):
        self.__init__(self._namespace)
        resources = self._loader.resources_for(datafile, load_observer)
        self._create_controllers(datafile, resources)
        RideOpenSuite(path=path, datafile=self._controller).publish()
        load_observer.finish()

    def _create_controllers(self, datafile, resources):
        self.clear_namespace_update_listeners()
        self._controller = DataController(datafile, self)
        for r in resources:
            self._create_resource_controller(r)

    def load_resource(self, path, load_observer):
        resource = self._load_resource(path, load_observer)
        if resource:
            return resource
        load_observer.error("Invalid resource file '%s'." % path)

    def _load_resource(self, path, load_observer):
        resource = self._namespace.get_resource(path)
        if not resource:
            return None
        ctrl = self._create_resource_controller(resource)
        load_observer.finish()
        return ctrl

    def _create_resource_controller(self, parsed_resource, parent=None):
        old = self._resource_file_controller_factory.find(parsed_resource)
        if old:
            return old
        controller = self._resource_file_controller_factory.create(parsed_resource, self, parent=parent)
        self._insert_into_suite_structure(controller)
        RideOpenResource(path=parsed_resource.source, datafile=controller).publish()
        self._load_resources_resource_imports(controller)
        return controller

    def _insert_into_suite_structure(self, resource):
        if self._controller and self._controller.is_inside_top_suite(resource):
            self._controller.insert_to_test_data_directory(resource)
        else:
            self.external_resources.append(resource)
            self._sort_external_resources()
    
    def _sort_external_resources(self):
        self.external_resources.sort(key=lambda resource: resource.name.lower())

    def _load_resources_resource_imports(self, controller):
        for _import in [ imp for imp in controller.imports if imp.is_resource ]:
            _import.import_loaded_or_modified()

    def get_all_keywords(self):
        return self.get_all_keywords_from(ctrl.datafile for ctrl in self.datafiles if ctrl.datafile)

    def all_testcases(self):
        for df in self._suites():
            for test in df.tests:
                yield test

    def get_files_without_format(self, controller=None):
        if controller:
            controller_list = [controller]
        else:
            controller_list = self._get_all_dirty_controllers()
        return [ dc for dc in controller_list if dc.dirty and not dc.has_format() ]

    def get_root_suite_dir_path(self):
        return self.suite.get_dir_path()

    def is_dirty(self):
        if self.data and self._is_datafile_dirty(self.data):
            return True
        for res in self.resources:
            if res.dirty:
                return True
        return False

    def _is_datafile_dirty(self, datafile):
        if datafile.dirty:
            return True
        for df in datafile.children:
            if self._is_datafile_dirty(df):
                return True
        return False

    def change_format(self, controller, format):
        if controller.is_same_format(format):
            return
        old_path = controller.filename
        controller.set_format(format)
        self.save(controller)
        if old_path:
            self._remove_file(old_path)
            RideFileNameChanged(old_filename=old_path,
                                datafile=controller).publish()

    def _remove_file(self, path):
        if path and os.path.isfile(path):
            os.remove(path)

    def change_format_recursive(self, controller, format):
        for datafile in controller.iter_datafiles():
            self.change_format(datafile, format)

    def remove_datafile(self, controller):
        if controller is self._controller:
            self._controller = None
        else:
            self._controller.remove_child(controller)

    def remove_resource(self, controller):
        self._resource_file_controller_factory.remove(controller)

    def save(self, controller):
        if controller:
            self._serializer.serialize_file(controller)
        else:
            self._serializer.serialize_files(self._get_all_dirty_controllers())

    def _get_all_dirty_controllers(self):
        return [controller for controller in self.datafiles if controller.dirty]

    def _suites(self):
        if not self.data:
            return []
        return [df for df in self.data.iter_datafiles() if not df in self.resources]

    def resource_import_modified(self, path, directory):
        resource = self._namespace.get_resource(path, directory)
        if resource:
            return self._create_resource_controller(resource)


class Serializer(object):

    def __init__(self, settings, logger):
        self._settings = settings
        self._logger = logger
        self._errors = []

    def serialize_files(self, controllers):
        try:
            for data in controllers:
                self._serialize_file(data)
            RideSaveAll().publish()
        finally:
            self._log_errors()

    def serialize_file(self, controller):
        try:
            self._serialize_file(controller)
        finally:
            self._log_errors()

    def _serialize_file(self, controller):
        RideSaving(path=controller.filename, datafile=controller).publish()
        with Backup(controller):
            try:
                controller.datafile.save(**self._get_options())
            except Exception, err:
                self._cache_error(controller, err)
                raise
        controller.unmark_dirty()
        RideSaved(path=controller.filename).publish()

    def _get_options(self):
        return {'line_separator': self._resolve_line_separator(),
                'pipe_separated': self._resolve_pipe_separated()}

    def _resolve_line_separator(self):
        setting = self._settings.get('line separator', 'native').lower()
        if setting in ('crlf', 'windows'):
            return '\r\n'
        if setting in ('lf', 'unix'):
            return '\n'
        return os.linesep

    def _resolve_pipe_separated(self):
        return self._settings.get('txt format separator', 'space') == 'pipe'

    def _cache_error(self, data, error):
        self._errors.append("Error in serializing '%s':\n%s"
                            % (data.data.source, unicode(error)))

    def _log_errors(self):
        if self._errors:
            self._logger.error('\n\n'.join(self._errors))
            self._errors = []


class Backup(object):

    def __init__(self, file_controller):
        self._path = file_controller.filename
        self._file_controller = file_controller
        self._backup = self._get_backup_name(self._path)

    def _get_backup_name(self, path):
        if not os.path.isfile(path):
            return None
        return os.path.join(tempfile.gettempdir(), os.path.basename(path))

    def __enter__(self):
        self._make_backup()

    def _make_backup(self):
        if self._backup:
            self._move(self._path, self._backup)

    def __exit__(self, *args):
        if any(args):
            self._restore_backup()
        else:
            self._remove_backup()

    def _remove_backup(self):
        if self._backup:
            os.remove(self._backup)

    def _restore_backup(self):
        if self._backup:
            self._move(self._backup, self._path)
            self._file_controller.refresh_stat()

    def _move(self, from_path, to_path):
        shutil.move(from_path, to_path)
