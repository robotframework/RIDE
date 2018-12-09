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

from functools import total_ordering
from robotide import robotapi


class SuggestionSource(object):

    def __init__(self, plugin, controller):
        self._plugin = plugin
        self._controller = controller

    def get_suggestions(self, value, row=None):
        if self._controller:
            return self._controller.get_local_namespace_for_row(row).get_suggestions(value)
        return self._plugin.content_assist_values(value) # TODO: Remove old functionality when no more needed


@total_ordering
class _Suggester(object):

    def _suggestion(self, name):
        s = lambda:0
        s.name = name
        s.longname = name
        s.details = None
        return s

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(repr(self))

    def __gt__(self, other):
        return self.name.lower() > other.name.lower()


class HistorySuggester(_Suggester):

    def __init__(self):
        self._suggestions = list()

    def get_suggestions(self, name, *args):
        return [s for s in self._suggestions if name is None or name.lower() in s.name.lower()]

    def store(self, name):
        self._suggestions += [self._suggestion(name)]
        # DEBUG For now remove sorting self._suggestions.sort()


class _ImportSuggester(_Suggester):

    def __init__(self, controller):
        self._df_controller = controller.datafile_controller

    def get_suggestions(self, name, *args):
        already_imported = self._get_already_imported()
        all_resources = self._get_all_available()
        suggestion_names = all_resources - already_imported
        return [self._suggestion(n) for n in sorted(suggestion_names) if name in n]

    def _get_already_imported(self):
        return set(imp.name for imp in self._df_controller.imports)


class ResourceSuggester(_ImportSuggester):

    def _get_all_available(self):
        return set(self._df_controller.relative_path_to(r) for r in self._df_controller._project.resources)


class CachedLibrarySuggester(_ImportSuggester):

    def _get_all_available(self):
        return set(self._df_controller.get_all_cached_library_names())


class BuiltInLibrariesSuggester(_Suggester):

    def get_suggestions(self, name, *args):
        return [self._suggestion(n) for n in sorted(robotapi.STDLIB_NAMES)
                if name.lower() in n.lower() and n not in ['BuiltIn', 'Reserved', 'Easter']]


class LibrariesSuggester(_Suggester):

    def __init__(self, controller, history_suggester):
        self._history_suggester = history_suggester
        self._cached_suggester = CachedLibrarySuggester(controller)
        self._builtin_suggester = BuiltInLibrariesSuggester()

    def get_suggestions(self, name, *args):
        history = set(h.name for h in self._history_suggester.get_suggestions(name, *args))
        cached = set(c.name for c in self._cached_suggester.get_suggestions(name, *args))
        builtin = set(b.name for b in self._builtin_suggester.get_suggestions(name, *args))
        already_imported = self._cached_suggester._get_already_imported()
        return [self._suggestion(s)
                for s in sorted((history | cached | builtin)-already_imported,
                key=lambda s: s.lower())]
