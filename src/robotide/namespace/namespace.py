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
import re

from robot.parsing.model import ResourceFile
from robot.parsing.settings import Library, Resource
from robot.utils.match import eq
from robot.utils.normalizing import NormalizedDict, normalize
from robotide.namespace.cache import LibraryCache
from robotide.spec.iteminfo import TestCaseUserKeywordInfo, ResourceseUserKeywordInfo, VariableInfo


class Namespace(object):

    def __init__(self):
        self.lib_cache = LibraryCache()
        self.res_cache = ResourceCache()
        self.retriever = DatafileRetriever(self.lib_cache, self.res_cache)

    def get_all_keywords(self, datafiles):
        kws = set()
        kws.update(self._get_default_keywords())
        kws.update(self.retriever.get_keywords_from_several(datafiles))
        return list(kws)

    def _get_default_keywords(self):
        return self.lib_cache.get_default_keywords()

    def get_suggestions_for(self, datafile, start):
        if self._blank(start):
            return self._all_suggestions(datafile)
        if self._looks_like_variable(start):
            return self._variable_suggestions(datafile, start)
        return self._keyword_suggestions(datafile, start)

    def _blank(self, start):
        return start == ''

    def _all_suggestions(self, datafile):
        vars = self._variable_suggestions(datafile, '')
        kws = self._keyword_suggestions(datafile, '')
        return vars + kws

    def _looks_like_variable(self, start):
        return (len(start) == 1 and start.startswith('$') or start.startswith('@')) \
            or (len(start) >= 2 and start.startswith('${') or start.startswith('@{'))

    def _variable_suggestions(self, datafile, start):
        start_normalized = normalize(start)
        source = os.path.basename(datafile.source) if datafile.source else ''
        vars = self.retriever.get_variables_from(datafile)
        return [VariableInfo(k, v, source) for k, v in vars.variables.items()
                if normalize(k).startswith(start_normalized)]

    def _keyword_suggestions(self, datafile, start):
        start_normalized = normalize(start)
        suggestions = self._get_default_keywords()
        suggestions.extend(self.retriever.get_keywords_from(datafile))
        return sorted([sug for sug in suggestions
                       if normalize(sug.name).startswith(start_normalized)])

    def get_resources(self, datafile):
        return self.retriever.get_resources_from(datafile)

    def find_user_keyword(self, datafile, kw_name):
        uks = self.retriever.get_user_keywords_from(datafile)
        for kw in uks:
            if eq(kw_name, kw.name):
                return kw
        return None

    def keyword_details(self, datafile, name):
        kws = self.retirever.get_keywords(datafile)
        for k in kws:
            if eq(k.name, name):
                return k.details
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
        self.variables = NormalizedDict()
        self._regexp = re.compile('(\$\{[^{}]*\})')

    def add_vars(self, variable_table):
        for v in variable_table.variables:
            self.variables[v.name] = v.value

    def replace_variables(self, string):
        parts = self._regexp.split(string)
        return ''.join([self._replace_variable(part) for part in parts])

    def _replace_variable(self, string):
        result = self.variables.get(string, None)
        return result[0] if result else string


class DatafileRetriever(object):

    def __init__(self, lib_cache, res_cache):
        self.lib_cache = lib_cache
        self.res_cache = res_cache
        self.default_kws = self.lib_cache.get_default_keywords()

    def get_keywords_from_several(self, datafiles):
        kws = set()
        kws.update(self.default_kws)
        for df in datafiles:
            kws.update(self.get_keywords_from(df))
        return kws

    def get_keywords_from(self, datafile):
        vars = VariableStash()
        vars.add_vars(datafile.variable_table)
        return list(set(self._get_datafile_keywords(datafile) +\
                        self._get_imported_library_keywords(datafile, vars) + \
                        self._get_imported_resource_keywords(datafile, vars)))

    def _get_datafile_keywords(self, datafile):
        return [TestCaseUserKeywordInfo(kw) for kw in datafile.keywords]

    def _get_imported_library_keywords(self, datafile, vars):
        return self._collect_kws_from_imports(datafile, Library,
                                               self._lib_kw_getter, vars)

    def _collect_kws_from_imports(self, datafile, instance_type, getter, vars):
        kws = []
        for imp in self._collect_import_of_type(datafile, instance_type):
            kws.extend(getter(imp, vars))
        return kws

    def _lib_kw_getter(self, imp, vars):
        name = vars.replace_variables(imp.name)
        return self.lib_cache.get_library_keywords(name, imp.args)

    def _collect_import_of_type(self, datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def _get_imported_resource_keywords(self, datafile, vars):
        kws = self._collect_kws_from_imports(datafile, Resource,
                                              self._res_kw_recursive_getter, vars)
        return kws

    def _res_kw_recursive_getter(self, imp, vars):
        resolved_name = vars.replace_variables(imp.name)
        res = self.res_cache.get_resource(imp.directory, resolved_name)
        if not res:
            return []
        vars.add_vars(res.variable_table)
        kws = []
        for child in self._collect_import_of_type(res, Resource):
            kws.extend(self._res_kw_recursive_getter(child, vars))
        kws.extend(self._get_imported_library_keywords(res, vars))
        return [ResourceseUserKeywordInfo(kw) for kw in res.keywords] + kws

    def get_variables_from(self, datafile):
        return self._get_vars_recursive(datafile, VariableStash())

    def _get_vars_recursive(self, datafile, vars):
        vars.add_vars(datafile.variable_table)
        for imp in self._collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            if res:
                self._get_vars_recursive(res, vars)
        return vars

    def get_user_keywords_from(self, datafile):
        return list(self._get_user_keywords_recursive(datafile, VariableStash()))

    def _get_user_keywords_recursive(self, datafile, vars):
        kws = set()
        kws.update(datafile.keywords)
        vars.add_vars(datafile.variable_table)
        for imp in self._collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            kws.update(self._get_user_keywords_recursive(res, vars))
        return kws

    def get_resources_from(self, datafile):
        return list(self._get_resources_recursive(datafile, VariableStash()))

    def _get_resources_recursive(self, datafile, vars):
        resources = set()
        vars.add_vars(datafile.variable_table)
        for imp in self._collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            if res:
                resources.add(res)
                resources.update(self._get_resources_recursive(res, vars))
        for child in datafile.children:
            resources.update(self.get_resources_from(child))
        return resources
