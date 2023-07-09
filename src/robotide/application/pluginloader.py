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

import importlib
import importlib.util
import inspect
import os

from ..context import LOG
from ..pluginapi import Plugin
from .pluginconnector import plugin_factory


class PluginLoader(object):

    def __init__(self, application, load_dirs, standard_classes):
        self._load_errors = []
        self.plugins = [plugin_factory(application, cls) for cls in standard_classes + self._find_classes(load_dirs)]
        if self._load_errors:
            LOG.error('\n\n'.join(self._load_errors))

    def enable_plugins(self):
        for p in self.plugins:
            p.enable_on_startup()

    def _find_classes(self, load_dirs):
        classes = []
        for path in self._find_python_files(load_dirs):
            for cls in self._import_classes(path):
                if self._is_plugin_class(path, cls):
                    classes.append(cls)
        return classes

    def _is_plugin_class(self, path, cls):
        try:
            return issubclass(cls, Plugin) and cls is not Plugin
        except Exception as err:
            msg = "Finding classes from module '%s' failed: %s"
            self._load_errors.append(msg % (path, err))

    def _find_python_files(self, load_dirs):
        files = []
        for path in load_dirs:
            if not os.path.exists(path):
                continue
            for filename in os.listdir(path):
                full_path = os.path.join(path, filename)
                if filename[0].isalpha() and \
                        os.path.splitext(filename)[1].lower() == ".py":
                    files.append(full_path)
                elif os.path.isdir(full_path):
                    files.extend(self._find_python_files([full_path]))
        return files

    def _import_classes(self, path):
        _, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        spec = importlib.util.spec_from_file_location(modulename, path)
        if spec is None:
            return []
        try:
            m_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m_module)
        except Exception as err:
            self._load_errors.append("Importing plugin module '%s' failed:\n%s"
                                     % (path, err))
            return []
        return [cls for _, cls in
                inspect.getmembers(m_module, predicate=inspect.isclass)]
