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
import os
from robot.parsing.model import ResourceFile
from robotide import utils


class ResourceCache(object):

    def __init__(self):
        self.cache = {}
        self.python_path_cache = {}

    def get_resource(self, directory, name):
        path = os.path.join(directory, name) if directory else name
        res = self._get_resource(path)
        if res:
            return res
        path_from_pythonpath = self._get_python_path(name)
        if path_from_pythonpath:
            return self._get_resource(path_from_pythonpath)
        return None

    def new_resource(self, directory, name):
        path = os.path.join(directory, name) if directory else name
        path = self._normalize(path)
        resource = ResourceFile(source=path)
        self.cache[path] = resource
        return resource

    def _get_python_path(self, name):
        if name in self.python_path_cache:
            return self.python_path_cache[name]
        path_from_pythonpath = utils.find_from_pythonpath(name)
        self.python_path_cache[name] = path_from_pythonpath
        return self.python_path_cache[name]

    def _get_resource(self, path):
        normalized = self._normalize(path)
        if normalized not in self.cache:
            try:
                self.cache[normalized] = ResourceFile(path).populate()
            except Exception:
                self.cache[normalized] = None
                return None
        return self.cache[normalized]

    def _normalize(self, path):
        return os.path.normcase(os.path.normpath(path))
