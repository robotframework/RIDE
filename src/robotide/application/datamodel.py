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

from robotide import context
from robotide.controller import DataController, ResourceFileController
from robotide.controller.filecontroller import TestCaseFileController
from robotide.errors import DataError, SerializationError
from robotide.robotapi import TestDataDirectory, TestCaseFile
from robotide.writer.serializer import Serializer
import os



class DataModel(object):

    def __init__(self, namespace, path=None):
        self.resources = []
        self.data = None
        self._namespace = namespace
        self._open(path)

    def _open(self, path):
        if not path:
            return
        try:
            self._open_suite(path)
        except DataError:
            try:
                self.open_resource(path)
            except DataError:
                raise DataError("Given file '%s' is not a valid Robot Framework "
                                "test case or resource file" % path)

    def _open_suite(self, path):
        if os.path.isdir(path):
            self.data = DataController(TestDataDirectory(source=path))
        else:
            self.data = DataController(TestCaseFile(source=path))
        self.resources = [ResourceFileController(r) for r in self._namespace.get_resources(self.data.data)]
        # FIXME:::  self._resolve_imported_resources(self.suite)

    def open_resource(self, path, datafile=None):
        resource = self._namespace.load_resource(path, datafile)
        if not resource:
            return None
        if resource not in self.resources:
            self.resources.append(resource)
            return resource
        return None

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
        return []
        # FIXME: please implement
        if controller:
            datafiles = [controller]
        else:
            datafiles = [self.suite] + self.suite.suites
        return [ df for df in datafiles if df.dirty and not df.has_format() ]

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
        return False
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
        # FIXME: HAndle also directories (=init files)
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
        # FIXME: there should be a method for this?
        controller.dirty = False

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
