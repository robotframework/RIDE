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
import shutil
import tempfile

from robotide.context import LOG
from robotide.controller.ctrlcommands import NullObserver, SaveFile
from robotide.publish.messages import RideOpenSuite, RideNewProject, RideFileNameChanged

from .basecontroller import WithNamespace, _BaseController
from .dataloader import DataLoader
from .filecontrollers import DataController, ResourceFileControllerFactory
from .robotdata import NewTestCaseFile, NewTestDataDirectory
from robotide.spec.librarydatabase import DATABASE_FILE
from robotide.spec.librarymanager import LibraryManager
from robotide.spec.xmlreaders import SpecInitializer
from robotide.utils import overrides
from robotide.utils import PY3
if PY3:
    from robotide.utils import unicode


class Project(_BaseController, WithNamespace):

    def __init__(self, namespace=None, settings=None, library_manager=None):
        self._library_manager = self._construct_library_manager(library_manager, settings)
        if not self._library_manager.is_alive():
            self._library_manager.start()
        self._set_namespace(namespace)
        self._settings = settings
        self._loader = DataLoader(namespace, settings)
        self._controller = None
        self.name = None
        self.external_resources = []
        self._resource_file_controller_factory = ResourceFileControllerFactory(namespace, self)
        self._serializer = Serializer(settings, LOG)

    def _construct_library_manager(self, library_manager, settings):
        return library_manager or \
            LibraryManager(DATABASE_FILE,
                SpecInitializer(settings.get('library xml directories', [])[:]))

    def __del__(self):
        if self._library_manager:
            self.close()

    def close(self):
        self._library_manager.stop()
        self._library_manager = None

    @overrides(WithNamespace)
    def _set_namespace(self, namespace):
        namespace.set_library_manager(self._library_manager)
        WithNamespace._set_namespace(self, namespace)

    @property
    def display_name(self):
        return 'Project'

    @property
    def default_dir(self):
        return os.path.abspath(self._settings.get('default directory', ''))

    def update_default_dir(self, path):
        default_dir = path if os.path.isdir(path) else os.path.dirname(path)
        self._settings.set('default directory', default_dir)

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

    def find_controller_by_longname(self, longname, testname=None):
        return self._controller.find_controller_by_longname(longname, testname)

    def new_directory_project(self, path):
        self._new_project(NewTestDataDirectory(path))

    def new_file_project(self, path):
        self._new_project(NewTestCaseFile(path))

    def _new_project(self, datafile):
        self.update_default_dir(datafile.directory)
        self._controller = DataController(datafile, self)
        self._resource_file_controller_factory = ResourceFileControllerFactory(self._namespace, self)
        RideNewProject(path=datafile.source, datafile=datafile).publish()

    def new_resource(self, path, parent=None):
        res = self._namespace.new_resource(path)
        self.update_default_dir(path)
        resource_controller = self._create_resource_controller(res, parent)
        return resource_controller

    def load_data(self, path, load_observer=None):
        load_observer = load_observer or NullObserver()
        if self._load_initfile(path, load_observer):
            return
        if self._load_datafile(path, load_observer):
            return
        if self._load_resource(path, load_observer):
            return
        try:
            load_observer.error("Given file '%s' is not a valid Robot Framework "
                            "test case or resource file." % path)
        except AttributeError:  # DEBUG
            pass

    def is_excluded(self, source):
        return self._settings.excludes.contains(source) if self._settings else False

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
        e = UserWarning("Invalid data file")
        return e

    def _load_datafile(self, path, load_observer):
        datafile = self._loader.load_datafile(path, load_observer)
        if not datafile:
            return None
        self._populate_from_datafile(path, datafile, load_observer)
        return datafile

    def _populate_from_datafile(self, path, datafile, load_observer):
        self.__init__(self._namespace, self._settings, library_manager=self._library_manager)
        resources = self._loader.resources_for(datafile, load_observer)
        self._create_controllers(datafile, resources)
        RideOpenSuite(path=path, datafile=self._controller).publish()
        load_observer.finish()

    def _create_controllers(self, datafile, resources):
        self.clear_namespace_update_listeners()
        self._controller = DataController(datafile, self)
        new_resource_controllers = []
        for r in resources:
            self._create_resource_controller(r, resource_created_callback=lambda controller: new_resource_controllers.append(controller))
        for controller in new_resource_controllers:
            self._inform_resource_created(controller)

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

    def _create_resource_controller(self, parsed_resource, parent=None, resource_created_callback=None):
        old = self._resource_file_controller_factory.find(parsed_resource)
        if old:
            return old
        controller = self._resource_file_controller_factory.create(parsed_resource, parent=parent)
        self.insert_into_suite_structure(controller)
        resource_created_callback = resource_created_callback or self._inform_resource_created
        resource_created_callback(controller)
        return controller

    def _inform_resource_created(self, controller):
        controller.notify_opened()

    def insert_into_suite_structure(self, resource):
        if self._controller and self._controller.is_inside_top_suite(resource):
            self._controller.insert_to_test_data_directory(resource)
        else:
            self.external_resources.append(resource)
            self._sort_external_resources()

    def _sort_external_resources(self):
        self.external_resources.sort(key=lambda resource: resource.name.lower())

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
        if self.data and self.is_datafile_dirty(self.data):
            return True
        for res in self.resources:
            if res.dirty:
                return True
        return False

    def is_datafile_dirty(self, datafile):
        if datafile.dirty:
            return True
        for df in datafile.children:
            if self.is_datafile_dirty(df):
                return True
        return False

    def change_format(self, controller, format):
        if controller.is_same_format(format):
            return
        old_path = controller.filename
        controller.set_format(format)
        controller.execute(SaveFile())
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
        assert controller is not None
        self._serializer.serialize_file(controller)

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

    def serialize_file(self, controller):
        try:
            self._serialize_file(controller)
        finally:
            self._log_errors()

    def _serialize_file(self, controller):
        with Backup(controller):
            try:
                controller.datafile.save(**self._get_options())
            except Exception as err:
                self._cache_error(controller, err)
                raise

    def _get_options(self):
        return {'line_separator': self._get_line_separator(),
                'pipe_separated': self._get_pipe_separated(),
                'txt_separating_spaces': self._get_separating_spaces()}

    def _get_line_separator(self):
        setting = self._settings.get('line separator', 'native').lower()
        if setting in ('crlf', 'windows'):
            return '\r\n'
        if setting in ('lf', 'unix'):
            return '\n'
        return os.linesep

    def _get_pipe_separated(self):
        return self._settings.get('txt format separator', 'space') == 'pipe'

    def _get_separating_spaces(self):
        return self._settings.get('txt number of spaces', 4)

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
        if path is None or not os.path.isfile(path):
            return None
        self._backup_dir = tempfile.mkdtemp(dir=os.path.dirname(path))
        return os.path.join(self._backup_dir, os.path.basename(path))

    def __enter__(self):
        self._make_backup()

    def _make_backup(self):
        if self._backup:
            try:
                self._move(self._path, self._backup)
            except IOError:
                self._backup = None
                self._remove_backup_dir()

    def __exit__(self, *args):
        if any(args):
            self._restore_backup()
        else:
            self._remove_backup()

    def _remove_backup(self):
        if self._backup:
            os.remove(self._backup)
            self._remove_backup_dir()

    def _restore_backup(self):
        if self._backup:
            self._move(self._backup, self._path)
            self._file_controller.refresh_stat()
            self._remove_backup_dir()

    def _move(self, from_path, to_path):
        shutil.move(from_path, to_path)

    def _remove_backup_dir(self):
        shutil.rmtree(self._backup_dir)
