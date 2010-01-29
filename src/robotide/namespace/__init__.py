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

import operator

from robotide import utils
from robotide.namespace.spec import UserKeywordContent, _XMLResource
from robotide.namespace.cache import LibraryCache, ResourceFileCache, \
    VariableFileCache


class ContentAssistItem(object):

    def __init__(self, source, name, details=''):
        self.source = source
        self.name = name
        self.details = details

    def get_details(self):
        return self.details

class VariableSpec(ContentAssistItem):
    pass


class Namespace(object):

    def __init__(self):
        self._lib_cache = LibraryCache()
        self._res_cache = ResourceFileCache(self)
        self._var_cache = VariableFileCache()
        self._hooks = []

    def register_content_assist_hook(self, hook):
        self._hooks.append(hook)

    def content_assist_values(self, item, value=''):
        values = self._get_item_keywords(item) + item.get_own_variables()+\
               self._lib_cache.get_default_keywords() +\
               item.imports.get_variables()
        for hook in self._hooks:
            values.extend(hook())
        return self._sort(self._remove_duplicates(values))

    def get_all_keywords(self, model):
        kws = []
        if model.suite:
            kws = model.suite.get_keywords()
            for s in model.suite.suites:
                kws.extend(s.get_keywords())
        for res in model.resources:
            kws.extend(res.get_keywords())
        kws.extend(self._lib_cache.get_default_keywords())
        return self._sort(self._remove_duplicates(kws))

    def _get_item_keywords(self, item):
        return [ UserKeywordContent(kw, '<this file>', item.type) for
                 kw in item.get_own_keywords() ] +\
                self._get_user_keywords_from_imports(item) +\
                item.imports.get_library_keywords()

    def _get_user_keywords_from_imports(self, item):
        kws = []
        for res in item.imports.get_resources():
            if isinstance(res, _XMLResource):
                kws.extend(res.get_keywords())
            else:
                kws.extend([UserKeywordContent(kw, res.name, res.type) for kw in
                            res.keywords])
                kws.extend(self._get_user_keywords_from_imports(res))
        return kws

    def load_resource(self, path, datafile):
        return self._res_cache.load_resource(path, datafile)

    def get_resource_file(self, source, name):
        return self._res_cache.get_resource_file(source, name)

    def get_varfile(self, source, name, args):
        return self._var_cache.get_varfile(source, name, args)

    def get_library_keywords(self, name, args):
        return self._lib_cache.get_library_keywords(name, args)

    def get_keywords(self, item):
        return item.get_own_keywords() + item.imports.get_keywords() +\
                self._lib_cache.get_default_keywords()

    def get_user_keyword(self, item, name):
        kws = self._match_name(item.get_user_keywords(), name)
        return kws and kws[0] or None

    def is_library_keyword(self, item, name):
        kws = self._match_name(self._get_library_keywords(item), name)
        return kws and kws[0].is_library_keyword() or False

    def is_user_keyword(self, item, name):
        return self._match_name(item.get_user_keywords(), name) != []

    def get_keyword_details(self, item, name):
        kws = self._match_name(self._get_keywords(item), name)
        return kws and kws[0].get_details() or None

    def _get_keywords(self, item):
        return self._get_item_keywords(item) +\
            self._lib_cache.get_default_keywords()

    def _get_library_keywords(self, item):
        return item.imports.get_library_keywords() + \
               self._lib_cache.get_default_keywords()

    def _match_name(self, keywords, name):
        if name is not None:
            keywords = [ kw for kw in keywords if utils.eq(kw.name, name) or
                                                  utils.eq(kw.longname, name) ]
        return keywords

    def _remove_duplicates(self, keywords):
        return list(set(keywords))

    def _sort(self, values):
        values.sort(key=operator.attrgetter('name'))
        return values

