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
import time
from threading import Thread

from robotide import context
from robotide.controller import DataController, ResourceFileController
from robotide.errors import SerializationError
from robotide.writer.serializer import Serializer
from robot.parsing.model import TestData, ResourceFile
from robotide.publish.messages import RideOpenResource, RideSaving, RideSaveAll,\
    RideSaved


class ChiefController(object):

    def __init__(self, namespace):
        self._namespace = namespace
        self._controller = None
        self.resources = []

    @property
    def data(self):
        return self._controller

    @property
    def suite(self):
        return self._controller.data if self._controller else None

    def load_data(self, path, load_observer):
        df = self.load_datafile(path, load_observer, notify_finish=False)
        if df:
            load_observer.finish()
            return
        res = self.load_resource(path, load_observer, notify_finish=False)
        if res:
            load_observer.finish()
        else:
            load_observer.error("Given file '%s' is not a valid Robot Framework "
                                "test case or resource file." % path)

    def new_resource(self, path):
        res = ResourceFile()
        res.source = path
        return self._create_resource_controller(res)

    def load_datafile(self, path, load_observer, notify_finish=True):
        self.__init__(self._namespace)
        datafile = self._load_datafile(path, load_observer)
        if not datafile:
            if notify_finish:
                load_observer.error("Invalid data file '%s'." % path)
            return None
        resources = self._load_resources(datafile, load_observer)
        self._create_controllers(datafile, resources)
        if notify_finish:
            load_observer.finish()
        return datafile

    def _load_datafile(self, path, load_observer):
        loader = _DataLoader(path)
        loader.start()
        while loader.isAlive():
            load_observer.notify()
            time.sleep(0.1)
        return loader.datafile

    def _create_controllers(self, datafile, resources):
        self._controller = DataController(datafile, self)
        for r in resources:
            self._create_resource_controller(r)

    def _load_resources(self, datafile, load_observer):
        loader = _ResourceLoader(datafile, self._namespace.get_resources)
        loader.start()
        while loader.isAlive():
            time.sleep(0.1)
            load_observer.notify()
        return loader.resources

    def load_resource(self, path, load_observer, notify_finish=True):
        resource = self._namespace.get_resource(path)
        if resource:
            if notify_finish:
                load_observer.finish()
            RideOpenResource(path=resource.source).publish()
            return self._create_resource_controller(resource)
        if notify_finish:
            load_observer.error("Invalid resource file '%s'." % path)
        return None

    def _create_resource_controller(self, resource):
        controller = ResourceFileController(resource, self)
        for other in self.resources:
            if other.source == controller.source:
                return None
        self.resources.append(controller)
        return controller

    def new_datafile(self, datafile):
        self._controller = DataController(datafile, self)
        self.resources = []

    def get_all_keywords(self):
        return self._namespace.get_all_keywords(ctrl.datafile for ctrl in self._get_all_controllers())

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

    def _remove_file(self, path):
        if path:
            os.remove(path)

    def change_format_recursive(self, controller, format):
        for datafile in controller.iter_datafiles():
            self.change_format(datafile, format)

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
        RideSaving(path=controller.source).publish()
        serializer = Serializer()
        serializer.serialize(controller)
        controller.unmark_dirty()
        RideSaved(path=controller.source).publish()

    def _get_all_dirty_controllers(self):
        return [controller for controller in self._get_all_controllers() if controller.dirty]

    def _get_all_controllers(self):
        return list(self.data.iter_datafiles()) + self.resources

    def resource_import_modified(self, path):
        resource = self._namespace.get_resource(path)
        if resource:
            return self._create_resource_controller(resource)
        return None


class _DataLoader(Thread):

    def __init__(self, path):
        Thread.__init__(self)
        self._path = path
        self.datafile = None

    def run(self):
        try:
            self.datafile = TestData(source=self._path)
        except Exception:
            pass
            # TODO: Log this error somehow


class _ResourceLoader(Thread):

    def __init__(self, datafile, resource_loader):
        Thread.__init__(self)
        self._datafile = datafile
        self._loader = resource_loader
        self.resources = []

    def run(self):
        self.resources = self._loader(self._datafile)
