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

import time
from threading import Thread

from robotide import context
from robotide.controller import DataController, ResourceFileController
from robotide.controller.filecontroller import TestCaseFileController
from robotide.errors import DataError, SerializationError
from robotide.writer.serializer import Serializer
from robot.parsing.model import TestData
from robotide.publish.messages import RideOpenResource


class ChiefController(object):

    def __init__(self, namespace):
        self._namespace = namespace
        self._controller = None
        self.resources = []

    @property
    def data(self):
        return self._controller

    def load_data(self, load_observer, path):
        try:
            self.load_datafile(load_observer, path)
        except DataError:
            resource = self.load_resource(path)
            if not resource:
                raise DataError("Given file '%s' is not a valid Robot Framework "
                                "test case or resource file" % path)

    def load_datafile(self, load_observer, path):
        datafile = self._load_datafile(load_observer, path)
        if datafile:
            self._controller = DataController(datafile)
            self.resources = [ResourceFileController(r) for r
                              in self._namespace.get_resources(datafile)]
        else:
            raise DataError()

    def _load_datafile(self, load_observer, path):
        loader = _DataLoader(path)
        loader.start()
        while loader.isAlive():
            time.sleep(0.1)
            load_observer.notify()
        load_observer.finished()
        return loader.datafile

    @property
    def suite(self):
        return self._controller.data if self._controller else None

    def load_resource(self, path, datafile=None):
        resource = self._namespace.get_resource(path)
        if not resource:
            raise DataError()
        controller = ResourceFileController(resource)
        RideOpenResource(path=resource.source).publish()
        if controller not in self.resources:
            self.resources.append(controller)
        return controller

    def _resolve_imported_resources(self, datafile):
        resources = datafile.get_resources()
        for res in resources:
            if res not in self.resources:
                self.resources.append(res)
        for item in datafile.suites + resources:
            self._resolve_imported_resources(item)

    def get_all_keywords(self):
        return self._namespace.get_all_keywords([self.data.data] if self.data else [] + self.resources )

    def get_files_without_format(self, controller=None):
        if controller:
            controller_list = [controller]
        else:
            controller_list = self._get_all_controllers()
        return [ dc for dc in controller_list if not dc.has_format() ]

    def get_root_suite_dir_path(self):
        return self.suite.get_dir_path()

    def is_directory_suite(self):
        return self.suite.is_directory_suite

    def is_dirty(self):
        if self.data and self._is_suite_dirty(self.data):
            return True
        for res in self.resources:
            if res.dirty:
                return True
        return False

    def _is_suite_dirty(self, suite):
        if suite.dirty:
            return True
        for s in suite.suites:
            if self._is_suite_dirty(s):
                return True
        return False

    def serialize(self, controller):
        if controller:
            self.serialize_controller(controller)
        else:
            self.serialize_all()

    def serialize_all(self):
        errors = []
        # FIXME: Handle also directories (=init files)
        datacontrollers = self._get_all_controllers()
        for dc in datacontrollers:
            try:
                self._serialize_file(dc)
            except SerializationError, err:
                errors.append(self._get_serialization_error(err, dc))
        self._log_serialization_errors(errors)

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
        serializer = Serializer()
        serializer.serialize(controller.data)
        controller.unmark_dirty()

    def _get_files_to_serialize(self, datafile):
        if datafile:
            return self._find_datafile_controller(datafile)
        return self._get_all_controllers()

    def _get_all_controllers(self):
        return self._get_filecontroller_and_all_child_filecontrollers(self.data)\
               + self.resources

    def _get_filecontroller_and_all_child_filecontrollers(self, parent_controller):
        ret = []
        # FIXME: This should not be necessary. Directories should be saved also.
        if isinstance(parent_controller, TestCaseFileController):
            ret.append(parent_controller)
        for controller in parent_controller.children:
            ret.extend(self._get_filecontroller_and_all_child_filecontrollers(controller))
        return ret

    def unsaved_modifications(self):
        return self.is_dirty()


class _DataLoader(Thread):

    def __init__(self, path):
        Thread.__init__(self)
        self._path = path
        self.datafile = None

    def run(self):
        try:
            self.datafile = TestData(source=self._path)
        except Exception, err:
            pass
            #context.LOG.error(str(err))
