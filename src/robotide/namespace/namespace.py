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

from robot.parsing.model import ResourceFile
from robot.parsing.settings import Library, Resource
from robot.utils.match import eq
from robot.utils.normalizing import NormalizedDict, normalize
from robotide.namespace.cache import LibraryCache
import os
import re



class KeywordInfo(object):

    def __init__(self, name, source=None, doc=None):
        self.name = name
        self.source = source
        self.doc = doc

    def __str__(self):
        return 'KeywordInfo[name: %s, source: %s, doc: %s]' %(self.name,
                                                              self.source,
                                                              self.doc)

    def __cmp__(self, other):
        name_cmp = cmp(self.name, other.name)
        return name_cmp if name_cmp else cmp(self.source, other.source)

    def __eq__(self, other):
        return not self.__cmp__(other)

    def __hash__(self):
        # FIXME: is this correct way to combine hashes?
        return hash(self.name) + hash(self.source)


class Namespace(object):

    def __init__(self):
        self.lib_cache = LibraryCache()
        self.res_cache = ResourceCache()

    def get_all_keywords(self, datafiles):
        kws = set()
        kws.update(self._get_default_keywords())
        kws.update(self._get_keywords_from(datafiles))
        return list(kws)

    def _get_default_keywords(self):
        kws = []
        for kw in self.lib_cache.get_default_keywords():
            kws.append(KeywordInfo(kw.name, kw.source, kw.doc))
        return kws

    def _get_keywords_from(self, datafiles):
        kws = set()
        for df in datafiles:
            kws.update(self._get_keywords(df))
        return kws

    def _get_keywords(self, datafile):
        vars = VariableStash()
        vars.add_vars(datafile.variable_table)
        return list(set(self._get_default_keywords() + \
                        self._get_datafile_keywords(datafile) +\
                        self._get_imported_keywords(datafile, vars) + \
                        self._get_import_resource_keywords(datafile, vars)))

    def _get_datafile_keywords(self, datafile):
        return [KeywordInfo(kw.name, datafile.source, kw.doc)
                for kw in datafile.keywords]

    def _get_imported_keywords(self, datafile, vars):
        return self.__collect_kws_from_imports(datafile, Library,
                                               self.__lib_kw_getter, vars)

    def __lib_kw_getter(self, imp, vars):
        name = vars.replace_variables(imp.name)
        return self.lib_cache.get_library_keywords(name, imp.args)

    def _get_import_resource_keywords(self, datafile, vars):
        kws = self.__collect_kws_from_imports(datafile, Resource,
                                              self.__res_kw_recursive_getter, vars)
        return kws

    def __res_kw_recursive_getter(self, imp, vars):
        resolved_name = vars.replace_variables(imp.name)
        res = self.res_cache.get_resource(imp.directory, resolved_name)
        if not res:
            return []
        vars.add_vars(res.variable_table)
        kws = []
        for child in self.__collect_import_of_type(res, Resource):
            kws.extend(self.__res_kw_recursive_getter(child, vars))
        kws.extend(self._get_imported_keywords(res, vars))
        return res.keywords + kws

    def __collect_kws_from_imports(self, datafile, instance_type, getter, vars):
        kws = []
        for imp in self.__collect_import_of_type(datafile, instance_type):
            kws.extend([KeywordInfo(kw.name, kw.source, kw.doc)
                        for kw in getter(imp, vars)])
        return kws

    def __collect_import_of_type(self, datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def _get_name_and_args(self, libsetting):
        parts = libsetting.split('|')
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1:]

    def get_suggestions_for(self, datafile, start):
        start_normalized = normalize(start)
        suggestions = self._get_keywords(datafile)
        return sorted([sug for sug in suggestions
                       if normalize(sug.name).startswith(start_normalized)])

    def get_resources(self, datafile):
        return list(self._get_resources_recursive(datafile, VariableStash()))

    def _get_resources_recursive(self, datafile, vars):
        resources= set()
        vars.add_vars(datafile.variable_table)
        for imp in self.__collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            if res:
                resources.add(res)
                resources.update(self._get_resources_recursive(res, vars))
        for child in datafile.children:
            resources.update(self.get_resources(child))
        return resources

    def find_user_keyword(self, datafile, kw_name):
        vars = VariableStash()
        return self._find_user_recursive_keyword(datafile, kw_name, vars)

    def _find_user_recursive_keyword(self, datafile, kw_name, vars):
        if not datafile:
            return None
        vars.add_vars(datafile.variable_table)
        for kw in datafile.keywords:
            if eq(kw_name, kw.name):
                return kw
        for imp in self.__collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            result = self._find_user_recursive_keyword(res, kw_name, vars)
            if result:
                return result
        return None


class ResourceCache(object):

    def __init__(self):
        self.cache = {}

    def get_resource(self, directory, name):
        path = os.path.join(directory, name)
        normalized = os.path.normpath(path)
        if normalized not in self.cache:
            try:
                self.cache[normalized] = ResourceFile(normalized)
            except:
                return None
        return self.cache[normalized]


class VariableStash(object):

    def __init__(self):
        self._variables = NormalizedDict()
        self._regexp = re.compile('(\$\{[^{}]*\})')

    def add_vars(self, variable_table):
        for v in variable_table.variables:
            self._variables[v.name] = v.value

    def replace_variables(self, string):
        parts = self._regexp.split(string)
        return ''.join([self._replace_variable(part) for part in parts])

    def _replace_variable(self, string):
        result = self._variables.get(string, None)
        return result[0] if result else string