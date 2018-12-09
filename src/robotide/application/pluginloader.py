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
import inspect
from robotide.context import LOG
from robotide.pluginapi import Plugin
from .pluginconnector import PluginFactory

from robotide.utils import PY2
if PY2:
    import imp  # Deprecated in Python 3.3
else:
    import importlib
    import importlib.util
    import sys


class PluginLoader(object):

    def __init__(self, application, load_dirs, standard_classes):
        self._load_errors = []
        self.plugins = [ PluginFactory(application, cls) for cls in
                         standard_classes + self._find_classes(load_dirs) ]
        # print("DEBUG: PluginLoader plugins:%s" % self.plugins)
        if self._load_errors:
            LOG.error('\n\n'.join(self._load_errors))

    def enable_plugins(self):
        for p in self.plugins:
            p.enable_on_startup()

    def _find_classes(self, load_dirs):
        classes = []
        for path in self._find_python_files(load_dirs):
            for cls in self._import_classes(path):
                # print("DEBUG: _find_classes cls:%s" % cls)
                if self._is_plugin_class(path, cls):
                    # print("DEBUG: _find_classes Plugin:%s" % cls)
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

    def _import_cls2(self, path):
        dirpath, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        try:
            file, imppath, description = imp.find_module(modulename, [dirpath])
        except ImportError:
            return []
        try:
            try:
                module = imp.load_module(modulename, file, imppath,
                                         description)
            except Exception as err:
                self._load_errors.append("Importing plugin module '%s' failed:\n%s"
                                         % (path, err))
                return []
        finally:
            if file:
                file.close()
        return [ cls for _, cls in
                 inspect.getmembers(module, predicate=inspect.isclass) ]

    def _import_cls3(self, path):
        dirpath, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        # print("DEBUG: import_class dir:%s file:%s module:%s path:%s" % (dirpath, filename, modulename, path))
        # spec = None
        # file, imppath, description = importlib.find_module(modulename, [dirpath])

        spec = importlib.util.spec_from_file_location(modulename, path)
        #spec = importlib.util.find_spec(modulename, dirpath)
        if spec is None:
            # print("DEBUG: import_class spec is None: %s" % modulename)
            return []
        try:
            m_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m_module)
            #module = importlib.load_module(modulename, file, imppath,
            #                         description)
        except Exception as err:
                self._load_errors.append("Importing plugin module '%s' failed:\n%s"
                                         % (path, err))
                return []
        return [cls for _, cls in
                inspect.getmembers(m_module, predicate=inspect.isclass)]

    def _import_classes(self, path):
        if PY2:
            return self._import_cls2(path)
        else:
            return self._import_cls3(path)
