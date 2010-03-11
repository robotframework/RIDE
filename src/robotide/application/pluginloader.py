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
import imp
import inspect

from robotide.context import LOG
from robotide.pluginapi import Plugin

from pluginconnector import PluginFactory


class PluginLoader(object):

    def __init__(self, application, load_dirs, standard_classes):
        self._load_errors = []
        self.plugins = [ PluginFactory(application, cls) for cls in
                         standard_classes + self._find_classes(load_dirs) ]
        if self._load_errors:
            LOG.error('\n\n'.join(self._load_errors))

    def enable_plugins(self):
        for p in self.plugins:
            p.enable_on_startup()

    def _find_classes(self, load_dirs):
        classes = []
        for path in self._find_python_files(load_dirs):
            for cls in self._import_classes(path):
                if issubclass(cls, Plugin) and cls is not Plugin:
                    classes.append(cls)
        return classes

    def _find_python_files(self, load_dirs):
        for path in load_dirs:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if os.path.splitext(filename)[1].lower() == ".py":
                        yield os.path.join(path, filename)

    def _import_classes(self, path):
        dirpath, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        file, imppath, description = imp.find_module(modulename, [dirpath])
        try:
            try:
                module = imp.load_module(modulename, file, imppath,
                                         description)
            except Exception, err:
                self._load_errors.append("Importing plugin module '%s' failed:\n%s"
                                         % (path, err))
                return []
        finally:
            if file:
                file.close()
        return [ cls for _, cls in
                 inspect.getmembers(module, predicate=inspect.isclass) ]
