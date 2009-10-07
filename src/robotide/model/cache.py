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

from robotide import utils
from robotide.context import SETTINGS
from robotide.spec import LibrarySpec, XMLResource
from robotide.robotapi import RobotVariables, normpath
from robotide.errors import DataError


class LibraryCache(object):

    def __init__(self):
        self.libraries = {}
        self._default_libraries = self._get_default_libraries()

    def add_library(self, name, args=None):
        if not self.libraries.has_key(name):
            self.libraries[name] = LibrarySpec(name, args)

    def get_library_keywords(self, name, args=None):
        if not self.libraries.has_key(name):
            self.add_library(name, args)
        return self.libraries[name].keywords

    def get_default_keywords(self):
        kws = []
        for spec in self._default_libraries.values():
            kws.extend(spec.keywords)
        return kws

    def _get_default_libraries(self):
        default_libs = {}
        for libsetting in SETTINGS['auto imports'] + ['BuiltIn']:
            name, args = self._get_name_and_args(libsetting)
            default_libs[name] = LibrarySpec(name, args)
        return default_libs

    def _get_name_and_args(self, libsetting):
        parts = libsetting.split('|')
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1:]


class _FileCache(object):

    def _get_name_and_absolute_path(self, source, name):
        name = name.replace('/', os.sep)
        if os.path.isfile(name):
            path = name
        else:
            path = os.path.join(os.path.dirname(source), name)
            if not os.path.isfile(path):
                path = utils.find_from_pythonpath(name)
        if path:
            path = normpath(path)
        return name, path


class VariableFileCache(_FileCache):

    def __init__(self):
        self._variable_files = {}

    def get_varfile(self, source, name, args):
        name, path = self._get_name_and_absolute_path(source, name)
        variable_file_id = (path, tuple(args))
        try:
            return self._variable_files[variable_file_id]
        except KeyError:
            varfile = self._import_variable_files(path, name,args)
            if varfile:
                self._variable_files[variable_file_id] = varfile
            return varfile

    def _import_variable_files(self, path, name, args):
        imported = RobotVariables()
        try:
            imported.set_from_file(path, args)
        except DataError:
            return None
        imported.source = name
        return imported


class ResourceFileCache(_FileCache):

    def __init__(self):
        self._resource_files = {}

    def get_resource_file(self, source, name):
        try:
            return self._get_from_cache(source, name)
        except KeyError:
            pass
        name, path = self._get_name_and_absolute_path(source, name)
        return self._get_resource_file(path, name, create_new=False)

    def load_resource(self, path, datafile=None):
        if datafile:
            return self.get_resource_file(datafile.source, path)
        else:
            return self._get_resource_file(normpath(path), None, create_new=True)

    def _get_resource_file(self, path, name, create_new=False):
        try:
            return self._resource_files[path or name]
        except KeyError:
            #TODO: There is cyclic import which should be removed
            from files import ResourceFileFactory
            try:
                resource = ResourceFileFactory(path, create_new) or XMLResource(name)
            except DataError:
                resource = None
            if resource:
                self._resource_files[path or name] = resource
            return resource

    def _get_from_cache(self, source, name):
        try:
            return self._resource_files[name]
        except KeyError:
            path = normpath(os.path.join(os.path.dirname(source), name))
            return self._resource_files[path]


LIBRARYCACHE = LibraryCache()
VARIABLEFILECACHE = VariableFileCache()
RESOURCEFILECACHE = ResourceFileCache()

