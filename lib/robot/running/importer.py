#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

import os.path
import copy

from robot.output import LOGGER
from robot.parsing import ResourceFile
from robot.errors import FrameworkError
from robot import utils

from testlibraries import TestLibrary


class Importer:

    def __init__(self):
        self._library_cache = ImportCache()
        self._resource_cache = ImportCache()

    def import_library(self, name, args, alias, variables):
        lib = TestLibrary(name, args, variables, create_handlers=False)
        positional, named = lib.positional_args, lib.named_args
        lib = self._import_library(name, positional, named, lib)
        if alias and name != alias:
            lib = self._copy_library(lib, alias)
            LOGGER.info("Imported library '%s' with name '%s'" % (name, alias))
        return lib

    def import_resource(self, path):
        if path in self._resource_cache:
            LOGGER.info("Found resource file '%s' from cache" % path)
        else:
            resource = ResourceFile(path).populate()
            self._resource_cache[path] = resource
        return self._resource_cache[path]

    def _import_library(self, name, positional, named, lib):
        key = (name, positional, named)
        if key in self._library_cache:
            LOGGER.info("Found test library '%s' with arguments %s from cache"
                        % (name, utils.seq2str2(positional)))
            return self._library_cache[key]
        lib.create_handlers()
        self._library_cache[key] = lib
        libtype = lib.__class__.__name__.replace('Library', '').lower()[1:]
        LOGGER.info("Imported library '%s' with arguments %s (version %s, "
                    "%s type, %s scope, %d keywords, source %s)"
                    % (name, utils.seq2str2(positional), lib.version, libtype,
                       lib.scope.lower(), len(lib), lib.source))
        if len(lib) == 0:
            LOGGER.warn("Imported library '%s' contains no keywords" % name)
        return lib

    def _copy_library(self, lib, newname):
        libcopy = copy.copy(lib)
        libcopy.name = newname
        libcopy.init_scope_handling()
        libcopy.handlers = utils.NormalizedDict(ignore=['_'])
        for handler in lib.handlers.values():
            handcopy = copy.copy(handler)
            handcopy.library = libcopy
            libcopy.handlers[handler.name] = handcopy
        return libcopy


class ImportCache:
    """Keeps track on and optionally caches imported items.

    Handles paths in keys case-insensitively on case-insensitive OSes.
    Unlike dicts, this storage accepts mutable values in keys.
    """

    def __init__(self):
        self._keys = []
        self._items = []

    def __setitem__(self, key, item):
        if not isinstance(key, (basestring, tuple)):
            raise FrameworkError('Invalid key for ImportCache')
        key = self._norm_path_key(key)
        if key not in self._keys:
            self._keys.append(key)
            self._items.append(item)
        else:
            self._items[self._keys.index(key)] = item

    def add(self, key, item=None):
        self.__setitem__(key, item)

    def __getitem__(self, key):
        key = self._norm_path_key(key)
        if key not in self._keys:
            raise KeyError
        return self._items[self._keys.index(key)]

    def __contains__(self, key):
        return self._norm_path_key(key) in self._keys

    def values(self):
        return self._items

    def _norm_path_key(self, key):
        if isinstance(key, tuple):
            return tuple(self._norm_path_key(k) for k in key)
        if isinstance(key, basestring) and os.path.exists(key):
            return utils.normpath(key)
        return key
