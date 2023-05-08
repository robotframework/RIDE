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
import time

from ..robotapi import normpath, ALIAS_MARKER
from ..spec.iteminfo import BlockKeywordInfo

BOOL_COND = '(boolean) condition'
SELECTOR_FOR = ('Selector for `FOR`. See `BuiltIn.FOR` docs at '
                'https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#for-loops.')
ARG_VALUES = '*values'


class LibraryCache(object):

    def __init__(self, settings, libraries_need_refresh_listener,
                 library_manager):
        self._library_manager = None
        self._settings = settings
        if library_manager:
            self.set_library_manager(library_manager)
        self._libraries_need_refresh_listener = libraries_need_refresh_listener
        self._library_keywords = {}
        self.__default_libraries = None
        self.__default_kws = None

    def set_library_manager(self, library_manager):
        self._library_manager = library_manager

    def expire(self):
        self.__init__(self._settings, self._libraries_need_refresh_listener,
                      self._library_manager)

    @property
    def _default_libraries(self):
        if self.__default_libraries is None:
            self.__default_libraries = self._get_default_libraries()
        return self.__default_libraries

    @property
    def _default_kws(self):
        if self.__default_kws is None:
            self.__default_kws = self._build_default_kws()
        return self.__default_kws

    def get_all_cached_library_names(self):
        return [name for name, _ in self._library_keywords]

    def _get_library(self, name, args):
        library_database = \
            self._library_manager.get_new_connection_to_library_database()
        try:
            last_updated = library_database.get_library_last_updated(name, args)
            if last_updated:
                if time.time() - last_updated > 10.0:
                    self._library_manager.fetch_keywords(
                        name, args, self._libraries_need_refresh_listener)
                return library_database.fetch_library_keywords(name, args)
            return self._library_manager.get_and_insert_keywords(name, args)
        finally:
            library_database.close()

    @staticmethod
    def _key(name, args):
        return name, str(tuple(args or ''))

    def get_library_keywords(self, name, args=None, alias=None):
        args_with_alias = self._alias_to_args(alias, args)
        key = self._key(name, args_with_alias)
        if key not in self._library_keywords:
            self._library_keywords[key] = [k.with_alias(alias) for k in
                                           self._get_library(name, args)]

        return self._library_keywords[key]

    @staticmethod
    def _alias_to_args(alias, args):
        if alias:
            if args:
                args = tuple(args) + (ALIAS_MARKER, alias)
            else:
                args = (ALIAS_MARKER, alias)
        return args

    def get_default_keywords(self):
        return self._default_kws[:]

    def _build_default_kws(self):
        kws = []
        for keywords_in_library in self._default_libraries.values():
            kws.extend(keywords_in_library)
        obj1 = BlockKeywordInfo('FOR',
                                'To create loops. Arguments: (scalars) loop_variables, selector: one of IN, IN RANGE,'
                                ' IN ENUMERATE, IN ZIP, values=scalars, lists, dictionaries. See `BuiltIn.FOR` docs'
                                ' at\n'
                                ' https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#for-loops.',
                                'ROBOT', 'BuiltIn', 'loop_variables', 'selector', ARG_VALUES)
        kws.append(obj1)
        obj2 = BlockKeywordInfo('END',
                                'Ends `FOR` loops, `IF/ELSE`, `WHILE` and `TRY/EXCEPT` blocks. See `BuiltIn.FOR` docs'
                                ' at\n https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#for-loops.')
        kws.append(obj2)
        obj3 = BlockKeywordInfo(': FOR', '*DEPRECATED*\nSee `BuiltIn.FOR` docs.')
        kws.append(obj3)
        obj4 = BlockKeywordInfo('WHILE',
                                'To create loops. Arguments: (boolean) condition, (optional) limit=counter or time. See'
                                ' `BuiltIn` docs at\n https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#while-loops.',
                                'ROBOT', 'BuiltIn', BOOL_COND, '(optional) limit=')
        kws.append(obj4)
        obj5 = BlockKeywordInfo('BREAK',
                                'To control loops. See `BuiltIn` docs at\n https://robotframework.org/robotframework/'
                                'latest/RobotFrameworkUserGuide.html#loop-control-using-break-and-continue.')
        kws.append(obj5)
        obj6 = BlockKeywordInfo('CONTINUE',
                                'To control loops. See `BuiltIn` docs at\n https://robotframework.org/robotframework/'
                                'latest/RobotFrameworkUserGuide.html#loop-control-using-break-and-continue.')
        kws.append(obj6)
        obj7 = BlockKeywordInfo('IF',
                                'To condition blocks of keywords. Arguments: (boolean) condition. See `BuiltIn` docs '
                                'at\n https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#if-else-syntax.',
                                'ROBOT', 'BuiltIn', BOOL_COND)
        kws.append(obj7)
        obj8 = BlockKeywordInfo('ELSE',
                                'To condition blocks of keywords. See `BuiltIn.IF` docs at\n '
                                'https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#if-else-syntax.\n Note: See also TRY/EXCEPT.')
        kws.append(obj8)
        obj9 = BlockKeywordInfo('ELSE IF',
                                'To condition blocks of keywords. Arguments: (boolean) condition. See `BuiltIn.IF` '
                                'docs at\n https://robotframework.org/robotframework/latest/'
                                'RobotFrameworkUserGuide.html#if-else-syntax.',
                                'ROBOT', 'BuiltIn', BOOL_COND)
        kws.append(obj9)
        obj10 = BlockKeywordInfo('TRY',
                                 'To prevent test failures based on messages from keywords. See `BuiltIn.TRY` '
                                 'docs at\n https://robotframework.org/robotframework/latest/'
                                 'RobotFrameworkUserGuide.html#try-except-syntax.')
        kws.append(obj10)
        obj11 = BlockKeywordInfo('EXCEPT',
                                 'To prevent test failures based on messages from keywords.\n\n'
                                 'Arguments: (optional) message=string, (optional) glob, regex, scalar, '
                                 '(optional) type, glob or error capture setting.\n\n See `BuiltIn.TRY` docs at\n '
                                 'https://robotframework.org/robotframework/latest/'
                                 'RobotFrameworkUserGuide.html#try-except-syntax.',
                                 'ROBOT', 'BuiltIn', '*options')
        kws.append(obj11)
        obj12 = BlockKeywordInfo('FINALLY',
                                 'To prevent test failures based on messages from keywords. See `BuiltIn.TRY` docs '
                                 'at\n https://robotframework.org/robotframework/latest/'
                                 'RobotFrameworkUserGuide.html#try-except-syntax.')
        kws.append(obj12)
        obj13 = BlockKeywordInfo('RETURN',
                                 'To return from keywords, with optional return values.\n\nArguments: (optional) any.'
                                 '\n\n See `BuiltIn.RETURN` docs at\n https://robotframework.org/robotframework/'
                                 'latest/RobotFrameworkUserGuide.html#toc-entry-348.',
                                 'ROBOT', 'BuiltIn', '(optional) *values=')
        kws.append(obj13)
        obj14 = BlockKeywordInfo('IN', SELECTOR_FOR, 'ROBOT', 'BuiltIn', ARG_VALUES)
        kws.append(obj14)
        obj15 = BlockKeywordInfo('IN RANGE', SELECTOR_FOR, 'ROBOT', 'BuiltIn', ARG_VALUES)
        kws.append(obj15)
        obj16 = BlockKeywordInfo('IN ENUMERATE', SELECTOR_FOR, 'ROBOT', 'BuiltIn', ARG_VALUES)
        kws.append(obj16)
        obj17 = BlockKeywordInfo('IN ZIP', SELECTOR_FOR, 'ROBOT', 'BuiltIn', ARG_VALUES)
        kws.append(obj17)
        return kws

    def _get_default_libraries(self):
        default_libs = {}
        for libsetting in self._settings['auto imports'] + ['BuiltIn']:
            name, args = self._get_name_and_args(libsetting)
            default_libs[name] = self._get_library(name, args)
        return default_libs

    @staticmethod
    def _get_name_and_args(libsetting):
        parts = libsetting.split('|')
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1:]


class ExpiringCache(object):

    def __init__(self, timeout=0.5):
        self._cache = {}
        self._timeout = timeout

    def get(self, key):
        if key in self._cache:
            key_time, values = self._cache[key]
            if self._is_valid(key_time):
                return values
        return None

    def _is_valid(self, key_time):
        return (time.time() - key_time) < self._timeout

    def put(self, key, values):
        self._cache[key] = (time.time(), values)

    def _get_from_cache(self, source, name):
        try:
            return self._resource_files[name]
        except KeyError:
            path = normpath(os.path.join(os.path.dirname(source), name))
            return self._resource_files[path]
