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

import operator
import os
import re
import sys
import tempfile
from itertools import chain
from multiprocessing import shared_memory
from robotide.lib.compat.parsing.language import Language

from .. import robotapi, utils
from ..publish import PUBLISHER, RideSettingsChanged, RideLogMessage
from ..robotapi import VariableFileSetter
from ..spec.iteminfo import (TestCaseUserKeywordInfo, ResourceUserKeywordInfo, VariableInfo, UserKeywordInfo,
                             ArgumentInfo, LibraryKeywordInfo, BlockKeywordInfo)
from .cache import LibraryCache, ExpiringCache
from .resourcefactory import ResourceFactory
from .embeddedargs import EmbeddedArgsHandler


class Namespace(object):

    def __init__(self, settings):
        self._context_factory = None
        self.settings = settings
        self._library_manager = None
        self._content_assist_hooks = []
        self._update_listeners = set()
        self._init_caches()
        self._set_pythonpath()
        self._words_cache = set()
        PUBLISHER.subscribe(self._setting_changed, RideSettingsChanged)

    def _init_caches(self):
        self._lib_cache = LibraryCache(
            self.settings, self.update, self._library_manager)
        self._resource_factory = ResourceFactory(self.settings)
        self._retriever = DatafileRetriever(self._lib_cache,
                                            self._resource_factory, self)
        self._context_factory = _RetrieverContextFactory()

    def _set_pythonpath(self):
        """Add user configured paths to PYTHONAPATH.
        """
        path_idx = 0
        dp = os.getenv('RIDE_DOC_PATH')
        if not dp:
            doc_paths = ['.']
        else:
            doc_paths = dp.split(',')
        for path in self.settings.get('pythonpath', []):
            if os.path.isdir(path):
                doc_paths.append(path.replace('/', os.sep))
            if path not in sys.path:
                normalized = path.replace('/', os.sep)
                sys.path.insert(path_idx, normalized)
                path_idx += 1
                RideLogMessage(u'Inserted \'{0}\' to sys.path.'.format(normalized)).publish()
        os.environ['RIDE_DOC_PATH'] = ",".join(doc_paths)

    def _setting_changed(self, message):
        section, setting = message.keys
        if section == '' and setting == 'pythonpath':
            for p in set(message.old).difference(message.new):
                if p in sys.path:
                    sys.path.remove(p)
            self._set_pythonpath()

    def update_exec_dir_global_var(self, exec_dir):
        _VariableStash.global_variables['${EXECDIR}'] = exec_dir
        self._context_factory.reload_context_global_vars()

    def update_cur_dir_global_var(self, cur_dir):
        dp = os.getenv('RIDE_DOC_PATH')
        parent_cur_dir=os.path.dirname(os.path.abspath(cur_dir))
        if dp:
            if cur_dir not in dp:
                os.environ['RIDE_DOC_PATH'] = dp + f", {cur_dir}, {parent_cur_dir}"
        else:
            os.environ['RIDE_DOC_PATH'] = f"{cur_dir}, {parent_cur_dir}"
        _VariableStash.global_variables['${CURDIR}'] = cur_dir
        self._context_factory.reload_context_global_vars()

    def set_library_manager(self, library_manager):
        self._library_manager = library_manager
        self._lib_cache.set_library_manager(library_manager)

    def update(self, *args):
        _ = args
        self._retriever.expire_cache()
        self._context_factory = _RetrieverContextFactory()
        for listener in self._update_listeners:
            listener()

    def resource_filename_changed(self, old_name, new_name):
        self._resource_factory.resource_filename_changed(old_name, new_name)

    def reset_resource_and_library_cache(self):
        self._init_caches()

    def register_update_listener(self, listener):
        self._update_listeners.add(listener)  # append(listener)  # DEBUG .add(listener)

    def unregister_update_listener(self, listener):
        if listener in self._update_listeners:
            self._update_listeners.remove(listener)

    def clear_update_listeners(self):
        self._update_listeners.clear()  # = list()  # DEBUG .clear()

    def register_content_assist_hook(self, hook):
        self._content_assist_hooks.append(hook)

    def get_all_keywords(self, testsuites):
        kws = set()
        kws.update(self._get_default_keywords())
        kws.update(self._retriever.get_keywords_from_several(testsuites))
        return kws

    def _get_default_keywords(self):
        return self._lib_cache.get_default_keywords()

    def get_suggestions_for(self, controller, start):
        if not controller:
            return []
        datafile = controller.datafile
        ctx = self._context_factory.ctx_for_controller(controller)
        sugs = set()  # self._words_cache or
        # print(f"DEBUG: namespace.py Namespace get_suggestions_for ENTER start={start} {datafile=} {ctx=} {sugs=}")
        while start and start[-1] in [']', '}', '=', ',']:
            start = start[:-1]
        sugs.update(self._get_suggestions_from_hooks(datafile, start))
        if self._blank(start) or not self._looks_like_variable(start):
            sugs.update(self._variable_suggestions(controller, start, ctx))
            sugs.update(self._keyword_suggestions(datafile, start, ctx))
        else:
            sugs.update(self._variable_suggestions(controller, start, ctx))
        # print(f"DEBUG: namespace.py Namespace get_suggestions_for BEFORE CONTENT start={start} {sugs=}")
        if not self._looks_like_variable(start):  # Search in content
            for v in ['${', '@{', '&{', '%{', '$']:
                sugs.update(self._content_suggestions(f'{v}{utils.normalize(start)}'))
        else:
            sugs.update(self._content_suggestions(f'{utils.normalize(start, suffixless=True)}'))
        # print(f"DEBUG: namespace.py Namespace get_suggestions_for FROM CONTENT start={start} {sugs=}")
        sugs_list = list(sugs)
        sugs_list.sort()
        # print(f"DEBUG: namespace.py Namespace get_suggestions_for RETURN {sugs_list=}")
        return sugs_list

    def _get_suggestions_from_hooks(self, datafile, start):
        sugs = []
        for hook in self._content_assist_hooks:
            sugs.extend(hook(datafile, start))
        return sugs

    def get_all_cached_library_names(self):
        return self._retriever.get_all_cached_library_names()

    @staticmethod
    def _blank(start):
        return start == ''

    @staticmethod
    def _looks_like_variable(start):
        return len(start) == 1 and start[0] in ['$', '@', '&', '%'] \
            or (len(start) >= 2 and start[:2] in ['${', '@{', '&{', '%{']) \
            or len(start) >= 2 and start[0] == '$'

    def _variable_suggestions(self, controller, start, ctx):
        self._add_kw_arg_vars(controller, ctx.vars)
        variables = self._retriever.get_variables_from(
            controller.datafile, ctx)
        sugs = (v for v in variables if v.name_matches(start))
        return sugs

    def _content_suggestions(self, start):
        sugs = set()
        for v in self._words_cache:
            if isinstance(v, (TestCaseUserKeywordInfo, ResourceUserKeywordInfo, UserKeywordInfo,
                              LibraryKeywordInfo, BlockKeywordInfo)):
                if v.name.lower().startswith(start.lower()):
                    sugs.add(v.name)
            elif isinstance(v, (VariableInfo, ArgumentInfo)):
                if v.name_matches(start):
                    # print(f"DEBUG: namespace.py Namespace _content_suggestions SUGGESTION from VARIABLE {v.name=}")
                    sugs.add(v.name)
            elif (v.lower().startswith(start.lower()) or v.strip('$&@%{[()]}=').lower()
                    .startswith(start.strip('$&@%{[()]}=').lower())):
                # print(f"DEBUG: namespace.py Namespace _content_suggestions SUGGESTION from STRING {v=}"
                #       f"\n v.lower().startswith(start.lower() ={v.lower().startswith(start.lower())}")
                sugs.add(v)
        return sugs

    @staticmethod
    def _add_kw_arg_vars(controller, variables):
        for name, value in controller.get_local_variables().items():
            variables.set_argument(name, value)

    def _keyword_suggestions(self, datafile, start, ctx):
        start_normalized = utils.normalize(start)
        all_kws = chain(self._get_default_keywords(),
                        self._retriever.get_keywords_from(datafile, ctx))
        return (sug for sug in all_kws
                if sug.name_begins_with(start_normalized) or
                sug.longname_begins_with(start_normalized))

    def get_resources(self, datafile, language=None):
        return self._retriever.get_resources_from(datafile, language=language)

    def get_resource(self, path, directory='', report_status=True):
        return self._resource_factory.get_resource(
            directory, path,
            report_status=report_status)

    def find_resource_with_import(self, imp):
        ctx = self._context_factory.ctx_for_datafile(imp.parent.parent)
        return self._resource_factory.get_resource_from_import(imp, ctx)

    def new_resource(self, path, directory=''):
        return self._resource_factory.new_resource(directory, path)

    def find_user_keyword(self, datafile, kw_name):
        kw = self.find_keyword(datafile, kw_name)
        return kw if isinstance(kw, UserKeywordInfo) else None

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
        from ..controller.cellinfo import UPPERCASE_KWS
        casesensitive = (kw_name.upper() != kw_name and kw_name.upper() in UPPERCASE_KWS)
        kwds = self._retriever.get_keywords_cached(datafile, self._context_factory, caseless=not casesensitive)
        # print(f"DEBUG: namespace.py Namespace find_keyword will GET kw_name=={kw_name} casesensitive={casesensitive}")
        return kwds.get(kw_name, origin=datafile)

    def is_library_keyword(self, datafile, kw_name):
        return bool(self.find_library_keyword(datafile, kw_name))

    def keyword_details(self, datafile, name):
        # print(f"DEBUG: namespace.py Namespace  keyword_details ENTER will look for name=={name} "
        #       f"in datafile={datafile.source}")
        kw = self.find_keyword(datafile, name)
        return kw.details if kw else None

    def update_words_cache(self, words_list:list, reset=False):
        if reset:
            self._words_cache.clear()
            return
        self._words_cache.update(set(words_list))


class _RetrieverContextFactory(object):
    def __init__(self):
        self._context_cache = {}

    def ctx_for_controller(self, controller):
        if controller not in self._context_cache:
            self._context_cache[controller] = RetrieverContext()
            self._context_cache[controller.datafile
                                ] = self._context_cache[controller]
        return self._context_cache[controller]

    def ctx_for_datafile(self, datafile):
        if datafile not in self._context_cache:
            ctx = RetrieverContext()
            ctx.set_variables_from_datafile_variable_table(datafile)
            self._context_cache[datafile] = ctx
        return self._context_cache[datafile]

    def reload_context_global_vars(self):
        for retrieve_context in self._context_cache.values():
            retrieve_context.vars.load_builtin_global_vars()


class RetrieverContext(object):
    def __init__(self):
        self.vars = _VariableStash()
        self.parsed = set()

    def set_variables_from_datafile_variable_table(self, datafile):
        self.vars.set_from_variable_table(datafile.variable_table)

    def replace_variables(self, text):
        return self.vars.replace_variables(text)

    def allow_going_through_resources_again(self):
        """Resets the parsed resources cache.

        Normally all resources that have been handled are added to 'parsed' and
        then not handled again, to prevent looping forever. If this same
        context is used for going through the resources again, this method
        should be called first.
        """
        self.parsed = set()


class _VariableStash(object):
    # Global variables copied from robot.variables
    global_variables = {
        '${:}': os.pathsep,
        '${/}': os.sep,
        '${CURDIR}': '.',
        '${DEBUG_FILE}': '',
        '${EMPTY}': '',
        '${EXECDIR}': os.path.abspath('.'),
        '${False}': False,
        '${KEYWORD_MESSAGE}': '',
        '${KEYWORD_STATUS}': '',
        '${LOG_FILE}': '',
        '${LOG_LEVEL}': '',
        '${\\n}': os.linesep,
        '${None}': None,
        '${null}': None,
        '${OUTPUT_DIR}': '',
        '${OUTPUT_FILE}': '',
        '${PREV_TEST_MESSAGE}': '',
        '${PREV_TEST_NAME}': '',
        '${PREV_TEST_STATUS}': '',
        '${REPORT_FILE}': '',
        '${SPACE}': ' ',
        '${SUITE_DOCUMENTATION}': '',
        '${SUITE_MESSAGE}': '',
        '${SUITE_METADATA}': '',
        '${SUITE_NAME}': '',
        '${SUITE_SOURCE}': '',
        '${SUITE_STATUS}': '',
        '${TEMPDIR}': os.path.normpath(tempfile.gettempdir()),
        '${TEST_DOCUMENTATION}': '',
        '${TEST_MESSAGE}': '',
        '${TEST_NAME}': '',
        '${TEST_STATUS}': '',
        '@{TEST_TAGS}': [],
        '${True}': True
    }

    ARGUMENT_SOURCE = object()

    def __init__(self):
        self._vars = robotapi.RobotVariables()
        self._sources = {}
        self.load_builtin_global_vars()

    def load_builtin_global_vars(self):
        for k, v in self.global_variables.items():
            self.set(k, v, 'built-in')

    def set(self, name, value, source):
        self._vars[name] = value
        self._sources[name[2:-1]] = source

    def set_argument(self, name, value):
        self.set(name, value, self.ARGUMENT_SOURCE)

    def replace_variables(self, value):
        try:
            return self._vars.replace_scalar(value)
        except robotapi.DataError:
            return self._vars.replace_string(value, ignore_errors=True)

    def set_from_variable_table(self, variable_table):
        # print("DEBUG: set_from_variable_table = %s \n" % list(variable_table))
        reader = robotapi.VariableTableReader()
        # print("DEBUG: set_from_variable_table reader %s \n" % reader)
        for variable in variable_table:
            try:
                if variable.name not in self._vars.store:
                    _, value = reader.get_name_and_value(
                        variable.name,
                        variable.value,
                        variable.report_invalid_syntax
                    )
                    #  print("DEBUG: inside variable.name= %s \n" % variable.name)
                    self.set(variable.name, value.resolve(self._vars),
                             variable_table.source)
            except (robotapi.VariableError, robotapi.DataError, Exception):
                if robotapi.is_var(variable.name):
                    val = self._empty_value_for_variable_type(variable.name)
                    self.set(variable.name, val, variable_table.source)

    @staticmethod
    def _empty_value_for_variable_type(name):
        if name[0] == '$':
            return ''
        if name[0] == '@':
            return []
        return {}

    def set_from_file(self, varfile_path, args):
        from ..robotapi import Variables
        from robotide.lib.robot.variables.store import VariableStore
        class Dummy:
            language='En'
        parent = Dummy()
        store = VariableStore(Variables(parent, ""))
        # print(f"namespace._VariableStash.set_from_file: variable_path {varfile_path} "
        #       f"args {args}")
        try:
            vars_from_file = VariableFileSetter(store)
            resulting_vars = vars_from_file._import_if_needed(varfile_path, args)
        except (robotapi.DataError, Exception) as e:
            # print(f"namespace._VariableStash.set_from_file: unexpected DataError: variable_path {varfile_path} "
            #       f"args {args}")
            raise e
        for name, value in resulting_vars:
            self.set(name, value, varfile_path)

    @staticmethod
    def _get_prefix(value):
        if utils.is_dict_like(value):
            return '&'
        elif utils.is_list_like(value):
            return '@'
        else:
            return '$'

    def __iter__(self):
        for name, value in self._vars.store.data.items():
            source = self._sources[name]
            prefix = self._get_prefix(value)
            name = u'{0}{{{1}}}'.format(prefix, name)
            if source == self.ARGUMENT_SOURCE:
                yield ArgumentInfo(name, value)
            else:
                yield VariableInfo(name, value, source)


class DatafileRetriever(object):
    def __init__(self, lib_cache, resource_factory, namespace):
        self._namespace = namespace
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
        return sorted(set(
            self._get_datafile_keywords(datafile) +
            self._get_imported_resource_keywords(datafile, ctx) +
            self._get_imported_library_keywords(datafile, ctx)))

    def is_library_import_ok(self, datafile, imp, ctx):
        self._get_vars_recursive(datafile, ctx)
        return bool(self._lib_kw_getter(imp, ctx))

    def is_variables_import_ok(self, datafile, imp, ctx):
        self._get_vars_recursive(datafile, ctx)
        return self._import_vars(ctx, datafile, imp)

    @staticmethod
    def _get_datafile_keywords(datafile):
        if isinstance(datafile, robotapi.ResourceFile):
            return [ResourceUserKeywordInfo(kw) for kw in datafile.keywords if not kw.name.startswith('#')]
        return [TestCaseUserKeywordInfo(kw) for kw in datafile.keywords if not kw.name.startswith('#')]

    def _get_imported_library_keywords(self, datafile, ctx):
        return self._collect_kws_from_imports(datafile, robotapi.Library,
                                              self._lib_kw_getter, ctx)

    def _collect_kws_from_imports(self, datafile, instance_type, getter, ctx):
        kws = []
        for imp in self._collect_import_of_type(datafile, instance_type):
            kws.extend(getter(imp, ctx))
        return kws

    def _lib_kw_getter(self, imp, ctx):
        # update cur dir for recursive import
        self._namespace.update_cur_dir_global_var(imp.directory)
        name = ctx.replace_variables(imp.name)
        name = self._convert_to_absolute_path(name, imp)
        args = [ctx.replace_variables(a) for a in imp.args]
        alias = ctx.replace_variables(imp.alias) if imp.alias else None
        return self._lib_cache.get_library_keywords(name, args, alias)

    @staticmethod
    def _convert_to_absolute_path(name, import_):
        full_name = os.path.join(import_.directory, name)
        if os.path.exists(full_name):
            return full_name
        return name

    @staticmethod
    def _collect_import_of_type(datafile, instance_type):
        return [imp for imp in datafile.imports
                if isinstance(imp, instance_type)]

    def _get_imported_resource_keywords(self, datafile, ctx):
        return self._collect_kws_from_imports(datafile, robotapi.Resource,
                                              self._res_kw_recursive_getter,
                                              ctx)

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
        return [ResourceUserKeywordInfo(kw) for kw in res.keywords if not kw.name.startswith('#')] + kws

    def get_variables_from(self, datafile, ctx=None):
        return self._get_vars_recursive(datafile,
                                        ctx or RetrieverContext()).vars

    def _get_vars_recursive(self, datafile, ctx):
        ctx.set_variables_from_datafile_variable_table(datafile)
        self._collect_vars_from_variable_files(datafile, ctx)
        self._collect_each_res_import(datafile, ctx, self._var_collector)
        return ctx

    def _collect_vars_from_variable_files(self, datafile, ctx):
        for imp in self._collect_import_of_type(datafile, robotapi.Variables):
            self._import_vars(ctx, datafile, imp)

    @staticmethod
    def _import_vars(ctx, datafile, imp):
        varfile_path = os.path.abspath(os.path.join(datafile.directory, ctx.replace_variables(imp.name)))
        args = [ctx.replace_variables(a) for a in imp.args]
        try:
            ctx.vars.set_from_file(varfile_path, args)
            return True
        except (robotapi.DataError, Exception):
            return False  # DEBUG: log somewhere

    def _var_collector(self, res, ctx, items):
        _ = items
        self._get_vars_recursive(res, ctx)

    def get_keywords_cached(self, datafile, context_factory, caseless=False):
        values = self.keyword_cache.get(datafile.source)
        if not values:
            words = self.get_keywords_from(datafile, context_factory.ctx_for_datafile(datafile))
            words.extend(self.default_kws)
            values = _Keywords(words, caseless=caseless)
            self.keyword_cache.put(datafile.source, values)
        # print(f"DEBUG: namespace.py DatafileRetrieve get_keywords_cached returning cached keywords values=={values}"
        #       f"\ndatafile={datafile.source}")
        # print(f"DEBUG: namespace.py DatafileRetrieve get_keywords_cached datafile = {datafile.source}")
        return values

    def _get_user_keywords_from(self, datafile):
        return list(self._get_user_keywords_recursive(datafile,
                                                      RetrieverContext()))

    def _get_user_keywords_recursive(self, datafile, contxt):
        kws = set()
        kws.update(datafile.keywords)
        kws_from_res = self._collect_each_res_import(
            datafile, contxt,
            lambda res, ctxt, kwords:
                kws.update(self._get_user_keywords_recursive(res, contxt)))
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

    def get_resources_from(self, datafile, language=None):
        resources = list(self._get_resources_recursive(datafile, RetrieverContext(), language=language))
        resources.sort(key=operator.attrgetter('name'))
        return resources  # DEBUG

    def _get_resources_recursive(self, datafile, ctx, language=None):
        # DEBUG: at this point it is not relevant the language, we would only need the header
        resources = set()
        res = self._collect_each_res_import(datafile, ctx, self._add_resource)
        resources.update(res)
        for child in datafile.children:
            resources.update(self._get_resources_recursive(child, ctx, language=language))
        return resources

    def _add_resource(self, res, ctx, items):
        items.add(res)
        items.update(self._get_resources_recursive(res, ctx))


class _Keywords(object):

    new_lang = None
    # Not Used? regexp = re.compile(r"\s*(given|when|then|and|but)\s*(.*)", re.IGNORECASE)

    def __init__(self, keywords, caseless=True, new_lang=None):
        if not self.new_lang:
            if not new_lang:
                new_lang = ['en']
                try:
                    set_lang = shared_memory.ShareableList(new_lang, name="language")
                except FileExistsError:  # Other instance created file
                    set_lang = shared_memory.ShareableList(name="language")
                self.new_lang = Language.from_name(set_lang[0].replace('_','-'))
            else:
                self.new_lang = new_lang
        self.normalized_bdd_prefixes = utils.normalize_pipe_list(list(self.new_lang.bdd_prefixes), spaces=False)
        self.gherkin_prefix = re.compile(fr'^({self.normalized_bdd_prefixes}) (.*)', re.IGNORECASE)
        self.keywords = robotapi.NormalizedDict(ignore=['_'], caseless=caseless)
        self.embedded_keywords = {}
        self._add_keywords(keywords)

    def _add_keywords(self, keywords):
        for kw in keywords:
            self._add_keyword(kw)

    def _add_keyword(self, kw):
        # DEBUG: this hack creates a preference for local keywords over
        # resources and libraries Namespace should be rewritten to handle
        # keyword preference order
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
            if hasattr(handler, 'longname_regexp'):
                self.embedded_keywords[handler.longname_regexp] = kw
            # print(f"DEBUG: namespace.py _add_embedded add kw={kw.name} longname={kw.longname}\n"
            #       f"handler.name_regexp={handler.name_regexp}")
        except TypeError:
            pass

    def get(self, kw_name, origin=None):
        if kw_name in self.keywords:
            # filename = os.path.basename(origin.source)
            # print(f"DEBUG: namespace.py _Keywords get keywords in loop FOUND {kw_name} @ {filename}"
            #       f" RETURNING {self.keywords[kw_name]} {self.keywords[kw_name].source == filename}")
            return self.keywords[kw_name]
        # print(f"DEBUG: namespace.py _Keywords get keywords {self.keywords}")
        bdd_name = self._get_bdd_name(kw_name)
        if bdd_name and bdd_name in self.keywords:
            return self.keywords[bdd_name]
        # print(f"DEBUG: namespace.py _Keywords get embedded kws {self.embedded_keywords}"
        #       f"\nseaching keyword={kw_name}")
        for regexp in self.embedded_keywords:
            try:
                if regexp.match(kw_name) or (bdd_name and regexp.match(bdd_name)):
                    return self.embedded_keywords[regexp]
            except AttributeError:
                pass
        return None

    def _get_bdd_name(self, kw_name):
        match = self.gherkin_prefix.match(kw_name)
        # print(f"DEBUG: namespace.py _Keywords _get_bdd_name match={match}")
        return match.group(2) if match else None
