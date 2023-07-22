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
from robotide import utils, robotapi


class ResourceFactory(object):
    _IGNORE_RESOURCE_DIRECTORY_SETTING_NAME = 'ignored resource directory'

    def __init__(self, settings):
        self.cache = {}
        self.python_path_cache = {}
        self._excludes = settings.excludes
        self.check_path_from_excludes = self._excludes.contains
        # print("DEBUG: ResourceFactory init path_excludes %s\n" % self.check_path_from_excludes)

    @staticmethod
    def _with_separator(ddir):
        return os.path.abspath(ddir) + os.path.sep

    def get_resource(self, directory, name, report_status=True):
        path = self._build_path(directory, name)
        res = self._get_resource(path, report_status=report_status)
        if res:
            return res
        path_from_pythonpath = self._get_python_path(name)
        if path_from_pythonpath:
            return self._get_resource(path_from_pythonpath,
                                      report_status=report_status)
        return None

    @staticmethod
    def _build_path(directory, name):
        path = os.path.join(directory, name) if directory else name
        return os.path.abspath(path)

    def get_resource_from_import(self, import_, retriever_context):
        resolved_name = retriever_context.vars.replace_variables(import_.name)
        result = self.get_resource(import_.directory, resolved_name)
        # print("""
        #    DEBUG Resource Factory: get_resource_from_import importdir: %s
        #    resolved_name: %s :result: %s
        #    """ % (import_.directory, resolved_name, result))
        return result

    def new_resource(self, directory, name):
        path = os.path.join(directory, name) if directory else name
        resource = robotapi.ResourceFile(source=path)
        self.cache[self._normalize(path)] = resource
        return resource

    def resource_filename_changed(self, old_name, new_name):
        self.cache[self._normalize(new_name)] = self._get_resource(old_name,
                                                                   report_status=True)
        del self.cache[self._normalize(old_name)]

    def _get_python_path(self, name):
        if name not in self.python_path_cache:
            path_from_pythonpath = utils.find_from_pythonpath(name)
            self.python_path_cache[name] = path_from_pythonpath
        return self.python_path_cache[name]

    def _get_resource(self, path, report_status):
        normalized = self._normalize(path)
        if self.check_path_from_excludes(path) or self.check_path_from_excludes(normalized):
            return None
        if normalized not in self.cache:
            try:
                self.cache[normalized] = self._load_resource(path, report_status=report_status)
            except Exception as e:
                # print("DEBUG Resource Factory: exception %s" % str(e))
                print(e)
                self.cache[normalized] = None
                return None
        return self.cache[normalized]

    def _load_resource(self, path, report_status):
        r = robotapi.ResourceFile(path)
        if os.stat(path)[6] != 0 and report_status:
            return r.populate()
        robotapi.FromFilePopulator(r).populate(r.source, resource=True)
        return r

    @staticmethod
    def _normalize(path):
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))
