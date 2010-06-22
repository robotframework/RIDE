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

from robot.errors import DataError
from robot.parsing.model import ResourceFile
from robot.parsing.settings import Library, Resource, Variables
from robot.utils.match import eq
from robot.utils.normalizing import normalize
from robot.variables import Variables as RobotVariables

from robotide.namespace.cache import LibraryCache, ExpiringCache
from robotide.spec.iteminfo import (TestCaseUserKeywordInfo,
                                    ResourceseUserKeywordInfo,
                                    VariableInfo, LibraryKeywordInfo)
from robotide import utils


class Namespace(object):

    def __init__(self):
        self.lib_cache = LibraryCache()
        self.res_cache = ResourceCache()
        self.retriever = DatafileRetriever(self.lib_cache, self.res_cache)
        self._content_assist_hooks = []

    def register_content_assist_hook(self, hook):
        self._content_assist_hooks.append(hook)

    def get_all_keywords(self, datafiles):
        kws = set()
        kws.update(self._get_default_keywords())
        kws.update(self.retriever.get_keywords_from_several(datafiles))
        return list(kws)

    def _get_default_keywords(self):
        return self.lib_cache.get_default_keywords()

    def get_suggestions_for(self, datafile, start):
        sugs = set()
        sugs.update(self._get_suggestions_from_hooks(datafile, start))
        if self._blank(start):
            sugs.update(self._all_suggestions(datafile))
        elif self._looks_like_variable(start):
            sugs.update(self._variable_suggestions(datafile, start))
        else:
            sugs.update(self._keyword_suggestions(datafile, start))
        sugs_list = list(sugs)
        sugs_list.sort()
        return sugs_list

    def _get_suggestions_from_hooks(self, datafile, start):
        sugs = []
        for hook in self._content_assist_hooks:
            sugs.extend(hook(datafile, start))
        return sugs

    def _blank(self, start):
        return start == ''

    def _all_suggestions(self, datafile):
        vars = self._variable_suggestions(datafile, '')
        kws = self._keyword_suggestions(datafile, '')
        all = vars + kws
        all.sort()
        return all

    def _looks_like_variable(self, start):
        return (len(start) == 1 and start.startswith('$') or start.startswith('@')) \
            or (len(start) >= 2 and start.startswith('${') or start.startswith('@{'))

    def _variable_suggestions(self, datafile, start):
        start_normalized = normalize(start)
        source = os.path.basename(datafile.source) if datafile.source else ''
        vars = self.retriever.get_variables_from(datafile)
        return [VariableInfo(k, v, source) for k, v in vars.items()
                if normalize(k).startswith(start_normalized)]

    def _keyword_suggestions(self, datafile, start):
        start_normalized = normalize(start)
        suggestions = self._get_default_keywords()
        suggestions.extend(self.retriever.get_keywords_from(datafile))
        return sorted([sug for sug in suggestions
                       if normalize(sug.name).startswith(start_normalized)])

    def get_resources(self, datafile):
        return self.retriever.get_resources_from(datafile)

    def get_resource(self, path):
        return self.res_cache.get_resource('', path)

    def find_user_keyword(self, datafile, kw_name):
        uks = self.retriever.get_user_keywords_dict_cached(datafile)
        return uks[kw_name] if kw_name in uks else None

    def _find_from(self, kws, predicate):
        for k in kws:
            if predicate(k):
                return k
        return None

    def is_user_keyword(self, datafile, kw_name):
        return bool(self.find_user_keyword(datafile, kw_name))

    def find_library_keyword(self, datafile, kw_name):
        return self._find_from_lib_keywords(datafile,
            lambda k: eq(k.name, kw_name) and isinstance(k, LibraryKeywordInfo))

    def _find_from_lib_keywords(self, datafile, predicate):
        kws = self._get_default_keywords()
        kws.extend(self.retriever.get_keywords_from(datafile))
        return self._find_from(kws, predicate)

    def is_library_keyword(self, datafile, kw_name):
        return bool(self.find_library_keyword(datafile, kw_name))

    def keyword_details(self, datafile, name):
        kw = self._find_from_lib_keywords(datafile, lambda k: eq(k.name, name))
        if kw:
            return kw.details
        return None


class ResourceCache(object):

    def __init__(self):
        self.cache = {}
        self.python_path_cache = {}

    def get_resource(self, directory, name):
        path = os.path.join(directory, name)
        res = self._get_resource(path)
        if res:
            return res
        path_from_pythonpath = self._get_python_path(name)
        if path_from_pythonpath:
            return self._get_resource(path_from_pythonpath)
        return None

    def _get_python_path(self, name):
        if name in self.python_path_cache:
            return self.python_path_cache[name]
        path_from_pythonpath = utils.find_from_pythonpath(name)
        self.python_path_cache[name] = path_from_pythonpath
        return self.python_path_cache[name]

    def _get_resource(self, path):
        normalized = os.path.normpath(path)
        if normalized not in self.cache:
            try:
                self.cache[normalized] = ResourceFile(path)
            except Exception:
                self.cache[normalized] = None
                return None
        return self.cache[normalized]


class VariableStash(RobotVariables):

    def replace_variables(self, value):
        return self.replace_string(value, ignore_errors=True)


class DatafileRetriever(object):

    def __init__(self, lib_cache, res_cache):
        self.lib_cache = lib_cache
        self.res_cache = res_cache
        self.user_keyword_cache = ExpiringCache()
        self.default_kws = self.lib_cache.get_default_keywords()

    def get_keywords_from_several(self, datafiles):
        kws = set()
        kws.update(self.default_kws)
        for df in datafiles:
            kws.update(self.get_keywords_from(df))
        return kws

    def get_keywords_from(self, datafile):
        vars = VariableStash()
        vars.set_from_variable_table(datafile.variable_table)
        return list(set(self._get_datafile_keywords(datafile) +
                        self._get_imported_library_keywords(datafile, vars) +
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
        args = [vars.replace_variables(a) for a in imp.args]
        return self.lib_cache.get_library_keywords(name, args)

    def _collect_import_of_type(self, datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def _get_imported_resource_keywords(self, datafile, vars):
        return self._collect_kws_from_imports(datafile, Resource,
                                              self._res_kw_recursive_getter, vars)

    def _res_kw_recursive_getter(self, imp, vars):
        kws = []
        resolved_name = vars.replace_variables(imp.name)
        res = self.res_cache.get_resource(imp.directory, resolved_name)
        if not res:
            return kws
        vars.set_from_variable_table(res.variable_table)
        for child in self._collect_import_of_type(res, Resource):
            kws.extend(self._res_kw_recursive_getter(child, vars))
        kws.extend(self._get_imported_library_keywords(res, vars))
        return [ResourceseUserKeywordInfo(kw) for kw in res.keywords] + kws

    def get_variables_from(self, datafile):
        return self._get_vars_recursive(datafile, VariableStash())

    def _get_vars_recursive(self, datafile, vars):
        vars.set_from_variable_table(datafile.variable_table)
        vars = self._collect_vars_from_variable_files(datafile, vars)
        vars = self._collect_vars_from_resource_files(datafile, vars)
        return vars

    def _collect_vars_from_variable_files(self, datafile, vars):
        for imp in self._collect_import_of_type(datafile, Variables):
            varfile_path = os.path.join(datafile.directory,
                                        vars.replace_variables(imp.name))
            args = [vars.replace_variables(a) for a in imp.args]
            try:
                vars.set_from_file(varfile_path, args)
            except DataError:
                pass # TODO: log somewhere
        return vars

    def _collect_vars_from_resource_files(self, datafile, vars):
        self._collect_each_res_import(datafile, vars, self._var_collector)
        return vars

    def _var_collector(self, res, vars, items):
        self._get_vars_recursive(res, vars)

    def get_user_keywords_dict_cached(self, datafile):
        values = self.user_keyword_cache.get(datafile.source)
        if not values:
            words = self._get_user_keywords_from(datafile)
            values = self._keywords_to_dict(words)
            self.user_keyword_cache.put(datafile.source, values)
        return values

    def _keywords_to_dict(self, keywords):
        ret = {}
        for kw in keywords:
            ret[kw.name] = kw
        return ret

    def _get_user_keywords_from(self, datafile):
        return list(self._get_user_keywords_recursive(datafile, VariableStash()))

    def _get_user_keywords_recursive(self, datafile, vars):
        kws = set()
        kws.update(datafile.keywords)
        kws_from_res = self._collect_each_res_import(datafile, vars,
            lambda res, vars, kws: kws.update(self._get_user_keywords_recursive(res, vars)))
        kws.update(kws_from_res)
        return kws

    def _collect_each_res_import(self, datafile, vars, collector):
        items = set()
        vars.set_from_variable_table(datafile.variable_table)
        for imp in self._collect_import_of_type(datafile, Resource):
            resolved_name = vars.replace_variables(imp.name)
            res = self.res_cache.get_resource(imp.directory, resolved_name)
            if res:
                collector(res, vars, items)
        return items

    def get_resources_from(self, datafile):
        return list(self._get_resources_recursive(datafile, VariableStash()))

    def _get_resources_recursive(self, datafile, vars):
        resources = set()
        res = self._collect_each_res_import(datafile, vars, self._add_resource)
        resources.update(res)
        for child in datafile.children:
            resources.update(self.get_resources_from(child))
        return resources

    def _add_resource(self, res, vars, items):
        items.add(res)
        items.update(self._get_resources_recursive(res, vars))
