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
from robotide.namespace.contentassister import ContentAssister
from robotide.namespace.cache import LibraryCache, ResourceFileCache, \
    VariableFileCache


class Namespace(object):

    def __init__(self):
        self._lib_cache = LibraryCache()
        self._res_cache = ResourceFileCache(self)
        self._var_cache = VariableFileCache()

    def content_assist_values(self, item, value=None):
        values = item.get_own_keywords('<this file>') + item.get_own_variables()+\
               self._lib_cache.get_default_keywords() +\
               item.imports.get_keywords() + item.imports.get_variables()
        return self._sort(self._remove_duplicates(values))

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

    def is_library_keyword(self, item, name):
        kws = self._filter(self._get_library_keywords(item), name)
        return kws and kws[0].is_library_keyword() or False

    def get_keyword_details(self, item, name):
        kws = self._filter(self._get_keywords(item), name)
        return kws and kws[0].get_details() or None

    def _get_keywords(self, item):
        return self._get_library_keywords(item) + item.get_own_keywords('<this file>')

    def _get_library_keywords(self, item):
        return item.imports.get_keywords() + \
               self._lib_cache.get_default_keywords()

    def _filter(self, keywords, name):
        if name is not None:
            keywords = [ kw for kw in keywords if utils.eq(kw.name, name) or
                                                  utils.eq(kw.longname, name) ]
        return keywords

    def _remove_duplicates(self, keywords):
        return list(set(keywords))

    def _sort(self, values):
        values.sort(key=operator.attrgetter('name'))
        return values

