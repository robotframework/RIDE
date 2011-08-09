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

from robotide import context
from robotide.errors import SerializationError
from robotide.publish.messages import RideOpenResource, RideSaving, RideSaveAll, \
    RideSaved, RideChangeFormat, RideOpenSuite, RideNewProject
from robotide.writer.serializer import Serializer

from filecontrollers import DataController, ResourceFileController
from dataloader import DataLoader
from robotide.context import SETTINGS


class ChiefController(object):

    def __init__(self, namespace):
        self._namespace = namespace
        self._loader = DataLoader(namespace)
        self._controller = None
        self.name = None
        self.resources = []

    @property
    def default_dir(self):
        return os.path.abspath(SETTINGS['default directory'])

    def update_default_dir(self, path):
        default_dir = path if os.path.isdir(path) else os.path.dirname(path)
        SETTINGS.set('default directory', default_dir)

    def execute(self, command):
        return command.execute(self)

    # TODO: in all other controllers data returns a robot data model object.
    @property
    def data(self):
        return self._controller

    @property
    def suite(self):
        return self._controller.data if self._controller else None

    def load_data(self, path, load_observer):
        if self._load_datafile(path, load_observer):
            return
        if self._load_resource(path, load_observer):
            return
        load_observer.error("Given file '%s' is not a valid Robot Framework "
                            "test case or resource file." % path)

    def new_resource(self, path):
        res = self._namespace.new_resource(path)
        return self._create_resource_controller(res)

    def load_datafile(self, path, load_observer):
        datafile = self._load_datafile(path, load_observer)
        if datafile:
            return datafile
        load_observer.error("Invalid data file '%s'." % path)

    def _load_datafile(self, path, load_observer):
        self.__init__(self._namespace)
        datafile = self._loader.load_datafile(path, load_observer)
        if not datafile:
            return None
        resources = self._loader.resources_for(datafile, load_observer)
        self._create_controllers(datafile, resources)
        RideOpenSuite(path=path, datafile=self._controller).publish()
        load_observer.finish()
        return datafile

    def _create_controllers(self, datafile, resources):
        self._namespace.clear_update_listeners()
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

    def _create_resource_controller(self, resource):
        controller = ResourceFileController(resource, self, parent=self._find_parent_for(resource.source))
        for other in self.resources:
            if other.source == controller.source:
                return other
        if controller.parent:
            controller.parent.children += [controller]
        self.resources.append(controller)
        RideOpenResource(path=resource.source, datafile=controller).publish()
        self._load_resources_resource_imports(controller)
        return controller

    def _find_parent_for(self, source):
        dir = os.path.dirname(source)
        for ctrl in self.datafiles:
            if ctrl.data.source == dir:
                return ctrl
        return None

    def _load_resources_resource_imports(self, controller):
        for _import in [ imp for imp in controller.imports if imp.is_resource ]:
            _import.import_loaded_or_modified()

    def new_project(self, datafile):
        self._controller = DataController(datafile, self)
        self.resources = []
        RideNewProject(path=datafile.source, datafile=datafile).publish()

    def update_namespace(self):
        self._namespace.update()

    def register_for_namespace_updates(self, listener):
        self._namespace.register_update_listener(listener)

    def unregister_namespace_updates(self, listener):
        self._namespace.unregister_update_listener(listener)

    def is_user_keyword(self, datafile, value):
        return self._namespace.is_user_keyword(datafile, value)

    def is_library_keyword(self, datafile, value):
        return self._namespace.is_library_keyword(datafile, value)

    def get_all_keywords(self):
        return self._namespace.get_all_keywords(ctrl.datafile for ctrl in self.datafiles)

    def all_testcases(self):
        for df in self._suites():
            for test in df.tests:
                yield test

    def keyword_info(self, datafile, keyword_name):
        return self._namespace.find_keyword(datafile, keyword_name)

    def get_files_without_format(self, controller=None):
        if controller:
            controller_list = [controller]
        else:
            controller_list = self._get_all_dirty_controllers()
        return [ dc for dc in controller_list if dc.dirty and not dc.has_format() ]

    def get_root_suite_dir_path(self):
        return self.suite.get_dir_path()

    def is_directory_suite(self):
        return self.suite.is_directory_suite

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
        old_path = controller.source
        controller.set_format(format)
        self.serialize_controller(controller)
        self._remove_file(old_path)
        RideChangeFormat(oldpath=old_path, newpath=controller.source).publish()

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
        self.resources.remove(controller)

    def save(self, controller):
        if controller:
            self.serialize_controller(controller)
        else:
            self.serialize_all()

    def serialize_all(self):
        errors = []
        datacontrollers = self._get_all_dirty_controllers()
        for dc in datacontrollers:
            try:
                self._serialize_file(dc)
            except SerializationError, err:
                errors.append(self._get_serialization_error(err, dc))
        self._log_serialization_errors(errors)
        RideSaveAll().publish()

    def serialize_controller(self, controller):
        try:
            self._serialize_file(controller)
        except SerializationError, err:
            self._log_serialization_errors([self._get_serialization_error(err, controller)])

    def _log_serialization_errors(self, errors):
        if errors:
            context.LOG.error('Following file(s) could not be saved:\n\n%s' %
                              '\n'.join(errors))

    def _get_serialization_error(self, err, controller):
        return '%s: %s\n' % (controller.data.source, str(err))

    def _serialize_file(self, controller):
        if not controller.has_format():
            return
        RideSaving(path=controller.source,
                   datafile=controller).publish()
        serializer = Serializer()
        serializer.serialize(controller.datafile)
        controller.unmark_dirty()
        RideSaved(path=controller.source).publish()

    def _get_all_dirty_controllers(self):
        return [controller for controller in self.datafiles if controller.dirty]

    @property
    def datafiles(self):
        return self._suites() + self.resources

    @property
    def all_datafiles(self):
        return self.datafiles

    def _suites(self):
        return list(self.data.iter_datafiles() if self.data else [])

    def resource_import_modified(self, path, directory):
        resource = self._namespace.get_resource(path, directory)
        if resource:
            return self._create_resource_controller(resource)
