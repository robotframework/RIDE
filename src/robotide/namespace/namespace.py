#  Copyright 2008-2015 Nokia Solutions and Networks
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
import sys
import re
import operator
import tempfile
from itertools import chain

from robotide import robotapi, utils
from robotide.namespace import variablefetcher
from robotide.namespace.cache import LibraryCache, ExpiringCache
from robotide.namespace.resourcefactory import ResourceFactory
from robotide.spec.iteminfo import TestCaseUserKeywordInfo,\
    ResourceUserKeywordInfo, VariableInfo, _UserKeywordInfo, ArgumentInfo
from robotide.namespace.embeddedargs import EmbeddedArgsHandler
from robotide.publish import PUBLISHER, RideSettingsChanged


class Namespace(object):

    def __init__(self, settings):
        self._settings = settings
        self._library_manager = None
        self._content_assist_hooks = []
        self._update_listeners = set()
        self._init_caches()
        self._set_pythonpath()
        PUBLISHER.subscribe(self._setting_changed, RideSettingsChanged)

    def _init_caches(self):
        self._lib_cache = LibraryCache(
            self._settings, self.update, self._library_manager)
        self._resource_factory = ResourceFactory(self._settings)
        self._retriever = DatafileRetriever(self._lib_cache, self._resource_factory)
        self._context_factory = _RetrieverContextFactory()

    def _set_pythonpath(self):
        values = self._settings.get('pythonpath', [])
        for path in values:
            if path not in sys.path:
                sys.path.insert(0, path.replace('/', os.sep))

    def _setting_changed(self, message):
        section, setting = message.keys
        if section == '' and setting == 'pythonpath':
            for p in set(message.old).difference(message.new):
                if p in sys.path:
                    sys.path.remove(p)
            self._set_pythonpath()

    def set_library_manager(self, library_manager):
        self._library_manager = library_manager
        self._lib_cache.set_library_manager(library_manager)

    def update(self, *args):
        self._retriever.expire_cache()
        self._context_factory = _RetrieverContextFactory()
        for listener in self._update_listeners:
            listener()

    def resource_filename_changed(self, old_name, new_name):
        self._resource_factory.resource_filename_changed(old_name, new_name)

    def reset_resource_and_library_cache(self):
        self._init_caches()

    def register_update_listener(self, listener):
        self._update_listeners.add(listener)

    def unregister_update_listener(self, listener):
        if listener in self._update_listeners:
            self._update_listeners.remove(listener)

    def clear_update_listeners(self):
        self._update_listeners.clear()

    def register_content_assist_hook(self, hook):
        self._content_assist_hooks.append(hook)

    def get_all_keywords(self, testsuites):
        kws = set()
        kws.update(self._get_default_keywords())
        kws.update(self._retriever.get_keywords_from_several(testsuites))
        return list(kws)

    def _get_default_keywords(self):
        return self._lib_cache.get_default_keywords()

    def get_suggestions_for(self, controller, start):
        datafile = controller.datafile
        ctx = self._context_factory.ctx_for_controller(controller)
        sugs = set()
        sugs.update(self._get_suggestions_from_hooks(datafile, start))
        if self._blank(start) or self._looks_like_variable(start):
            sugs.update(self._variable_suggestions(controller, start, ctx))
        else:
            sugs.update(self._variable_suggestions(controller, '${'+start, ctx))
            sugs.update(self._variable_suggestions(controller, '@{'+start, ctx))
        if self._blank(start) or not self._looks_like_variable(start):
            sugs.update(self._keyword_suggestions(datafile, start, ctx))
        sugs_list = list(sugs)
        sugs_list.sort()
        return sugs_list

    def _get_suggestions_from_hooks(self, datafile, start):
        sugs = []
        for hook in self._content_assist_hooks:
            sugs.extend(hook(datafile, start))
        return sugs

    def get_all_cached_library_names(self):
        return self._retriever.get_all_cached_library_names()

    def _blank(self, start):
        return start == ''

    def _looks_like_variable(self, start):
        return (len(start) == 1 and start.startswith('$') or
                start.startswith('@')) \
            or (len(start) >= 2 and start.startswith('${') or
                start.startswith('@{'))

    def _variable_suggestions(self, controller, start, ctx):
        datafile = controller.datafile
        start_normalized = utils.normalize(start)
        self._add_kw_arg_vars(controller, ctx.vars)
        variables = self._retriever.get_variables_from(datafile, ctx)
        return (v for v in variables
                if utils.normalize(v.name).startswith(start_normalized))

    def _add_kw_arg_vars(self, controller, variables):
        for name, value in controller.get_local_variables().iteritems():
            variables.set_argument(name, value)

    def _keyword_suggestions(self, datafile, start, ctx):
        start_normalized = utils.normalize(start)
        return (sug for sug in chain(
            self._get_default_keywords(),
            self._retriever.get_keywords_from(datafile, ctx))
                if sug.name_begins_with(start_normalized) or
                sug.longname_begins_with(start_normalized))

    def get_resources(self, datafile):
        return self._retriever.get_resources_from(datafile)

    def get_resource(self, path, directory='', report_status=True):
        return self._resource_factory.get_resource(
            directory, path, report_status=report_status)

    def find_resource_with_import(self, imp):
        ctx = self._context_factory.ctx_for_datafile(imp.parent.parent)
        return self._resource_factory.get_resource_from_import(imp, ctx)

    def new_resource(self, path, directory=''):
        return self._resource_factory.new_resource(directory, path)

    def find_user_keyword(self, datafile, kw_name):
        kw = self.find_keyword(datafile, kw_name)
        return kw if isinstance(kw, _UserKeywordInfo) else None

    def is_user_keyword(self, datafile, kw_name):
        return bool(self.find_user_keyword(datafile, kw_name))

    def find_library_keyword(self, datafile, kw_name):
        kw = self.find_keyword(datafile, kw_name)
        return kw if kw and kw.is_library_keyword() else None

    def is_library_import_ok(self, datafile, imp):
        return self._retriever.is_library_import_ok(
            datafile, imp, self._context_factory.ctx_for_datafile(datafile))

    def is_variables_import_ok(self, datafile, imp):
        return self._retriever.is_variables_import_ok(
            datafile, imp, self._context_factory.ctx_for_datafile(datafile))

    def find_keyword(self, datafile, kw_name):
        if not kw_name:
            return None
        kwds = self._retriever.get_keywords_cached(datafile,
                                                   self._context_factory)
        return kwds.get(kw_name)

    def is_library_keyword(self, datafile, kw_name):
        return bool(self.find_library_keyword(datafile, kw_name))

    def keyword_details(self, datafile, name):
        kw = self.find_keyword(datafile, name)
        return kw.details if kw else None


class _RetrieverContextFactory(object):

    def __init__(self):
        self._context_cache = {}

    def ctx_for_controller(self, controller):
        if controller not in self._context_cache:
            self._context_cache[controller] = RetrieverContext()
            self._context_cache[controller.datafile] = self._context_cache[controller]
        return self._context_cache[controller]

    def ctx_for_datafile(self, datafile):
        if datafile not in self._context_cache:
            ctx = RetrieverContext()
            ctx.set_variables_from_datafile_variable_table(datafile)
            self._context_cache[datafile] = ctx
        return self._context_cache[datafile]


class RetrieverContext(object):

    def __init__(self):
        self.vars = _VariableStash()
        self.parsed = set()

    def set_variables_from_datafile_variable_table(self, datafile):
        self.vars.set_from_variable_table(datafile.variable_table)

    def replace_variables(self, text):
        return self.vars.replace_variables(text)

    def allow_going_through_resources_again(self):
        """Resets the parsed-cache.
        Normally all resources that have been handled are added to 'parsed' and
        then not handled again, to prevent looping forever. If this same context
        is used for going through the resources again, then you should call
        this.
        """
        self.parsed = set()


class _VariableStash(object):
    # Global variables copied from robot.variables.__init__.py
    global_variables =  {'${TEMPDIR}': os.path.normpath(tempfile.gettempdir()),
                         '${EXECDIR}': os.path.abspath('.'),
                         '${/}': os.sep,
                         '${:}': os.pathsep,
                         '${SPACE}': ' ',
                         '${EMPTY}': '',
                         '${True}': True,
                         '${False}': False,
                         '${None}': None,
                         '${null}': None,
                         '${OUTPUT_DIR}': '',
                         '${OUTPUT_FILE}': '',
                         '${SUMMARY_FILE}': '',
                         '${REPORT_FILE}': '',
                         '${LOG_FILE}': '',
                         '${DEBUG_FILE}': '',
                         '${PREV_TEST_NAME}': '',
                         '${PREV_TEST_STATUS}': '',
                         '${PREV_TEST_MESSAGE}': '',
                         '${CURDIR}': '.',
                         '${TEST_NAME}': '',
                         '@{TEST_TAGS}': '',
                         '${TEST_STATUS}': '',
                         '${TEST_MESSAGE}': '',
                         '${SUITE_NAME}': '',
                         '${SUITE_SOURCE}': '',
                         '${SUITE_STATUS}': '',
                         '${SUITE_MESSAGE}': ''}

    ARGUMENT_SOURCE = object()

    def __init__(self):
        self._vars = robotapi.RobotVariables()
        self._sources = {}
        for k, v in self.global_variables.iteritems():
            self.set(k, v, 'built-in')

    def set(self, name, value, source):
        self._vars[name] = value
        self._sources[name] = source

    def set_argument(self, name, value):
        self.set(name, value, self.ARGUMENT_SOURCE)

    def replace_variables(self, value):
        try:
            return self._vars.replace_scalar(value)
        except robotapi.DataError:
            return self._vars.replace_string(value, ignore_errors=True)

    def set_from_variable_table(self, variable_table):
        for variable in variable_table:
            try:
                if not self._vars.has_key(variable.name):
                    _, value = self._vars._get_var_table_name_and_value(
                        variable.name,
                        variable.value,
                        variable.report_invalid_syntax
                    )
                    self.set(variable.name, value, variable_table.source)
            except robotapi.DataError:
                if robotapi.is_var(variable.name):
                    self.set(variable.name, '', variable_table.source)

    def set_from_file(self, varfile_path, args):
        for item in variablefetcher.import_varfile(varfile_path, args):
            self.set(*item)

    def __iter__(self):
        for name, value in self._vars.items():
            source = self._sources[name]
            if source == self.ARGUMENT_SOURCE:
                yield ArgumentInfo(name, value)
            else:
                yield VariableInfo(name, value, source)


class DatafileRetriever(object):

    def __init__(self, lib_cache, resource_factory):
        self._lib_cache = lib_cache
        self._resource_factory = resource_factory
        self.keyword_cache = ExpiringCache()
        self._default_kws = None

    def get_all_cached_library_names(self):
        return self._lib_cache.get_all_cached_library_names()

    @property
    def default_kws(self):
        if self._default_kws is None:
            self._default_kws = self._lib_cache.get_default_keywords()
        return self._default_kws

    def expire_cache(self):
        self.keyword_cache = ExpiringCache()
        self._lib_cache.expire()

    def get_keywords_from_several(self, datafiles):
        kws = set()
        kws.update(self.default_kws)
        for df in datafiles:
            kws.update(self.get_keywords_from(df, RetrieverContext()))
        return kws

    def get_keywords_from(self, datafile, ctx):
        self._get_vars_recursive(datafile, ctx)
        ctx.allow_going_through_resources_again()
        return sorted(set(self._get_datafile_keywords(datafile) +\
              self._get_imported_resource_keywords(datafile, ctx) +\
              self._get_imported_library_keywords(datafile, ctx)))

    def is_library_import_ok(self, datafile, imp, ctx):
        self._get_vars_recursive(datafile, ctx)
        return bool(self._lib_kw_getter(imp, ctx))

    def is_variables_import_ok(self, datafile, imp, ctx):
        self._get_vars_recursive(datafile, ctx)
        return self._import_vars(ctx, datafile, imp)

    def _get_datafile_keywords(self, datafile):
        if isinstance(datafile, robotapi.ResourceFile):
            return [ResourceUserKeywordInfo(kw) for kw in datafile.keywords]
        return [TestCaseUserKeywordInfo(kw) for kw in datafile.keywords]

    def _get_imported_library_keywords(self, datafile, ctx):
        return self._collect_kws_from_imports(datafile, robotapi.Library,
                                              self._lib_kw_getter, ctx)

    def _collect_kws_from_imports(self, datafile, instance_type, getter, ctx):
        kws = []
        for imp in self._collect_import_of_type(datafile, instance_type):
            kws.extend(getter(imp, ctx))
        return kws

    def _lib_kw_getter(self, imp, ctx):
        name = ctx.replace_variables(imp.name)
        name = self._convert_to_absolute_path(name, imp)
        args = [ctx.replace_variables(a) for a in imp.args]
        alias = ctx.replace_variables(imp.alias) if imp.alias else None
        return self._lib_cache.get_library_keywords(name, args, alias)

    def _convert_to_absolute_path(self, name, import_):
        full_name = os.path.join(import_.directory, name)
        if os.path.exists(full_name):
            return full_name
        return name

    def _collect_import_of_type(self, datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def _get_imported_resource_keywords(self, datafile, ctx):
        return self._collect_kws_from_imports(datafile, robotapi.Resource,
                                              self._res_kw_recursive_getter, ctx)

    def _res_kw_recursive_getter(self, imp, ctx):
        kws = []
        res = self._resource_factory.get_resource_from_import(imp, ctx)
        if not res or res in ctx.parsed:
            return kws
        ctx.parsed.add(res)
        ctx.set_variables_from_datafile_variable_table(res)
        for child in self._collect_import_of_type(res, robotapi.Resource):
            kws.extend(self._res_kw_recursive_getter(child, ctx))
        kws.extend(self._get_imported_library_keywords(res, ctx))
        return [ResourceUserKeywordInfo(kw) for kw in res.keywords] + kws

    def get_variables_from(self, datafile, ctx=None):
        return self._get_vars_recursive(datafile, ctx or RetrieverContext()).vars

    def _get_vars_recursive(self, datafile, ctx):
        ctx.set_variables_from_datafile_variable_table(datafile)
        self._collect_vars_from_variable_files(datafile, ctx)
        self._collect_each_res_import(datafile, ctx, self._var_collector)
        return ctx

    def _collect_vars_from_variable_files(self, datafile, ctx):
        for imp in self._collect_import_of_type(datafile, robotapi.Variables):
            self._import_vars(ctx, datafile, imp)

    def _import_vars(self, ctx, datafile, imp):
        varfile_path = os.path.join(datafile.directory,
            ctx.replace_variables(imp.name))
        args = [ctx.replace_variables(a) for a in imp.args]
        try:
            ctx.vars.set_from_file(varfile_path, args)
            return True
        except robotapi.DataError:
            return False # TODO: log somewhere

    def _var_collector(self, res, ctx, items):
        self._get_vars_recursive(res, ctx)

    def get_keywords_cached(self, datafile, context_factory):
        values = self.keyword_cache.get(datafile.source)
        if not values:
            words = self.get_keywords_from(datafile, context_factory.ctx_for_datafile(datafile))
            words.extend(self.default_kws)
            values = _Keywords(words)
            self.keyword_cache.put(datafile.source, values)
        return values

    def _get_user_keywords_from(self, datafile):
        return list(self._get_user_keywords_recursive(datafile, RetrieverContext()))

    def _get_user_keywords_recursive(self, datafile, ctx):
        kws = set()
        kws.update(datafile.keywords)
        kws_from_res = self._collect_each_res_import(datafile, ctx,
            lambda res, ctx, kws: kws.update(self._get_user_keywords_recursive(res, ctx)))
        kws.update(kws_from_res)
        return kws

    def _collect_each_res_import(self, datafile, ctx, collector):
        items = set()
        ctx.set_variables_from_datafile_variable_table(datafile)
        for imp in self._collect_import_of_type(datafile, robotapi.Resource):
            res = self._resource_factory.get_resource_from_import(imp, ctx)
            if res and res not in ctx.parsed:
                ctx.parsed.add(res)
                collector(res, ctx, items)
        return items

    def get_resources_from(self, datafile):
        resources = list(self._get_resources_recursive(datafile, RetrieverContext()))
        resources.sort(key=operator.attrgetter('name'))
        return resources

    def _get_resources_recursive(self, datafile, ctx):
        resources = set()
        res = self._collect_each_res_import(datafile, ctx, self._add_resource)
        resources.update(res)
        for child in datafile.children:
            resources.update(self.get_resources_from(child))

        return resources

    def _add_resource(self, res, ctx, items):
        items.add(res)
        items.update(self._get_resources_recursive(res, ctx))


class _Keywords(object):

    regexp = re.compile("\s*(given|when|then|and)\s*(.*)", re.IGNORECASE)

    def __init__(self, keywords):
        self.keywords = robotapi.NormalizedDict(ignore=['_'])
        self.embedded_keywords = {}
        self._add_keywords(keywords)

    def _add_keywords(self, keywords):
        for kw in keywords:
            self._add_keyword(kw)

    def _add_keyword(self, kw):
        # TODO: this hack creates a preference for local keywords over resources and libraries
        # Namespace should be rewritten to handle keyword preference order
        if kw.name not in self.keywords:
            self.keywords[kw.name] = kw
            self._add_embedded(kw)
        self.keywords[kw.longname] = kw

    def _add_embedded(self, kw):
        if '$' not in kw.name:
            return
        try:
            handler = EmbeddedArgsHandler(kw)
            self.embedded_keywords[handler.name_regexp] = kw
        except Exception:
            pass

    def get(self, kw_name):
        if kw_name in self.keywords:
            return self.keywords[kw_name]
        bdd_name = self._get_bdd_name(kw_name)
        if bdd_name and bdd_name in self.keywords:
            return self.keywords[bdd_name]
        for regexp in self.embedded_keywords:
            if regexp.match(kw_name) or (bdd_name and regexp.match(bdd_name)):
                return self.embedded_keywords[regexp]
        return None

    def _get_bdd_name(self, kw_name):
        match = self.regexp.match(kw_name)
        return match.group(2) if match else None
