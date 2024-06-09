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

from .basecontroller import WithNamespace, _BaseController
from .dataloader import DataLoader
from .robotdata import new_test_case_file, new_test_data_directory
from ..context import LOG
from ..controller.ctrlcommands import NullObserver, SaveFile
from ..publish.messages import RideOpenSuite, RideNewProject, RideFileNameChanged
from .. import spec
from ..spec.xmlreaders import SpecInitializer


class Project(_BaseController, WithNamespace):

    def __init__(self, namespace=None, settings=None, library_manager=None, tasks=False, file_language=None):
        from .filecontrollers import ResourceFileControllerFactory
        self._library_manager = self._construct_library_manager(library_manager, settings)
        if not self._library_manager.is_alive():
            self._library_manager.start()
        self._name_space = namespace
        self._set_namespace(self._name_space)
        self.tasks = tasks
        self.internal_settings = settings
        self._loader = DataLoader(self._name_space, settings)
        self.controller = None
        self.name = None
        self.external_resources = []
        self.file_language = file_language
        self._resource_file_controller_factory = ResourceFileControllerFactory(self._name_space, self)
        self._serializer = Serializer(settings, LOG)

    @staticmethod
    def _construct_library_manager(library_manager, settings):
        return library_manager or \
            spec.LibraryManager(spec.DATABASE_FILE, SpecInitializer(settings.get('library xml directories', [])[:]))

    def __del__(self):
        if self._library_manager:
            self.close()

    def close(self):
        self._library_manager.stop()
        self._library_manager = None

    def _set_namespace(self, namespace):
        namespace.set_library_manager(self._library_manager)
        WithNamespace._set_namespace(self, namespace)

    @property
    def display_name(self):
        return 'Project'

    @property
    def default_dir(self):
        return os.path.abspath(self.internal_settings.get('default directory', ''))

    def update_default_dir(self, path):
        default_dir = path if os.path.isdir(path) else os.path.dirname(path)
        self.internal_settings.set('default directory', default_dir)
        self._name_space.update_exec_dir_global_var(default_dir)
        self._name_space.update_cur_dir_global_var(default_dir)

    # DEBUG: in all other controllers data returns a robot data model object.
    @property
    def data(self):
        return self.controller

    @property
    def suite(self):
        return self.controller.data if self.controller else None

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
        return self.controller.find_controller_by_longname(longname, testname)

    def get_language_from_settings(self):
        from ..preferences import RideSettings
        _settings = RideSettings()
        lang = _settings.get('doc language', '')
        self.file_language = lang
        return lang

    def new_directory_project(self, path, tasks=False, lang=''):
        lang = lang if lang else self.get_language_from_settings()
        self._new_project(new_test_data_directory(path, tasks=tasks, lang=lang), tasks=tasks)

    def new_file_project(self, path, tasks=False, lang=''):
        lang = lang if lang else self.get_language_from_settings()
        self._new_project(new_test_case_file(path, tasks=tasks, lang=lang), tasks=tasks)

    def _new_project(self, datafile, tasks=False):
        from .filecontrollers import data_controller, ResourceFileControllerFactory
        self.update_default_dir(datafile.directory)
        self.controller = data_controller(datafile, self, tasks=tasks)
        self._resource_file_controller_factory = ResourceFileControllerFactory(self.namespace, self)
        RideNewProject(path=datafile.source, datafile=datafile).publish()

    def new_resource(self, path, parent=None):
        res = self.namespace.new_resource(path)
        resource_controller = self._create_resource_controller(res, parent)
        return resource_controller

    def load_data(self, path, load_observer=None):
        """ DEBUG: To be used in Localization
        """
        from robotide.context import APP
        try:
            robot_version = APP.robot_version
        except AttributeError:
            robot_version = '7.0.1'  # It is failing at unit tests
        print(f"DEBUG: project.py Project load_data robot version = {robot_version}")
        from ..lib.compat.parsing.language import check_file_language
        self.file_language = check_file_language(path)
        load_observer = load_observer or NullObserver()
        if self._load_initfile(path, load_observer, self.file_language):
            return
        if self._load_datafile(path, load_observer, self.file_language):
            return
        if self._load_resource(path, load_observer, self.file_language):
            return
        try:
            load_observer.error("Given file '%s' is not a valid Robot Framework "
                                "test case or resource file." % path)
        except AttributeError:  # DEBUG
            # print(f"DEBUG: load_data error not valid datafile: {path}")
            pass

    def is_excluded(self, source=None):
        return self.internal_settings.excludes.contains(source) if self.internal_settings else False

    def _load_initfile(self, path, load_observer, language=None):
        if os.path.splitext(os.path.split(path)[1])[0] != '__init__':
            return None
        initfile = self._loader.load_initfile(path, load_observer, language)
        if not initfile:
            return None
        self._populate_from_datafile(path, initfile, load_observer, language)
        return initfile

    def load_datafile(self, path, load_observer, language=None):
        datafile = self._load_datafile(path, load_observer, language)
        if datafile:
            return datafile
        # print(f"DEBUG: project Before testing Resource load_datafile path={path}")
        # Let's see if it is a .robot file valid as .resource
        if path.endswith((".robot", ".resource")):
            datafile = self._load_resource(path, load_observer, language)
            if datafile:
                return datafile
        load_observer.error("Invalid data file '%s'." % path)
        e = UserWarning("Invalid data file")
        return e

    def _load_datafile(self, path, load_observer, language=None):
        # print(f"DEBUG: project ENTER _load_datafile path={path} self.file_language={self.file_language}"
        #       f" language={language}")
        datafile = self._loader.load_datafile(path, load_observer, self.file_language)
        if not datafile:
            return None
        self._populate_from_datafile(path, datafile, load_observer, language)
        return datafile

    def _populate_from_datafile(self, path, datafile, load_observer, language=None):
        self.__init__(self.namespace, self.internal_settings, library_manager=self._library_manager,
                      file_language=language)
        resources = self._loader.resources_for(datafile, load_observer)
        self._create_controllers(datafile, resources)
        RideOpenSuite(path=path, datafile=self.controller).publish()
        load_observer.finish()

    def _create_controllers(self, datafile, resources):
        from .filecontrollers import data_controller
        self.clear_namespace_update_listeners()
        self.controller = data_controller(datafile, self)
        new_resource_controllers = []
        for r in resources:
            self._create_resource_controller(r, resource_created_callback=lambda r_controller:
                                             new_resource_controllers.append(r_controller))
        for controller in new_resource_controllers:
            self._inform_resource_created(controller)

    def load_resource(self, path, load_observer, language=None):
        resource = self._load_resource(path, load_observer, language)
        if resource:
            return resource
        load_observer.error("Invalid resource file '%s'." % path)

    def _load_resource(self, path, load_observer, language=None):
        resource = self._loader.load_resource_file(path, load_observer, language)
        if not resource:
            return None
        ctrl = self._create_resource_controller(resource)
        load_observer.finish()
        return ctrl

    def _create_resource_controller(self, parsed_resource, parent=None,
                                    resource_created_callback=None):
        old = self._resource_file_controller_factory.find(parsed_resource)
        if old:
            return old
        controller = self._resource_file_controller_factory.create(parsed_resource, parent=parent)
        self.insert_into_suite_structure(controller)
        resource_created_callback = resource_created_callback or self._inform_resource_created
        resource_created_callback(controller)
        return controller

    @staticmethod
    def _inform_resource_created(controller):
        controller.notify_opened()

    def insert_into_suite_structure(self, resource):
        if self.controller and self.controller.is_inside_top_suite(resource):
            self.controller.insert_to_test_data_directory(resource)
        else:
            self.external_resources.append(resource)
            self._sort_external_resources()

    def _sort_external_resources(self):
        self.external_resources.sort(key=lambda resource: resource.name.lower())

    def get_all_keywords(self):
        return self.get_all_keywords_from(ctrl.datafile for ctrl in self.datafiles if
                                          ctrl.datafile)

    def all_testcases(self):
        for df in self._suites():
            for test in df.tests:
                yield test

    def get_files_without_format(self, controller=None):
        if controller:
            controller_list = [controller]
        else:
            controller_list = self._get_all_dirty_controllers()
        return [dc for dc in controller_list if dc.dirty and not dc.has_format()]

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

    def change_format(self, controller, cformat):
        if controller.is_same_format(cformat):
            return
        old_path = controller.filename
        controller.set_format(cformat)
        controller.execute(SaveFile(self.internal_settings.get('reformat', False)))
        if old_path:
            self._remove_file(old_path)
            RideFileNameChanged(old_filename=old_path,
                                datafile=controller).publish()

    def _remove_file(self, path):
        if path and os.path.isfile(path):
            os.remove(path)

    def change_format_recursive(self, controller, cformat):
        for datafile in controller.iter_datafiles():
            self.change_format(datafile, cformat)

    def remove_datafile(self, controller):
        if controller is self.controller:
            self.controller = None
        else:
            self.controller.remove_child(controller)

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
        return [df for df in self.data.iter_datafiles() if df not in self.resources]

    def resource_import_modified(self, path, directory):
        resource = self.namespace.get_resource(path, directory)
        if resource:
            return self._create_resource_controller(resource)

    def is_project_changed_from_disk(self):
        from .filecontrollers import TestDataDirectoryController
        for data_file in self.datafiles:
            if isinstance(data_file, TestDataDirectoryController):
                # print(f"DEBUG: Project is_project_changed_from_disk directory is {data_file.directory}")
                if not os.path.exists(data_file.directory):
                    # print(f"DEBUG: Project is_project_changed_from_disk directory TRUE {data_file.directory}")
                    return True
            else:
                if data_file.has_been_modified_on_disk() or \
                        data_file.has_been_removed_from_disk():
                    # print(f"DEBUG: Project is_project_changed_from_disk FILE  TRUE {data_file.name}")
                    return True
        return False


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
                            % (data.data.source, str(error)))

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
