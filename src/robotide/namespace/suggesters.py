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
        # print(f"DEBUG: suggesters.py SuggestionSource get_suggestions ENTER value={value}")
        start = value
        while start and start[-1] in [']', '}', '=', ',']:
            start = start[:-1]
            # print(f"DEBUG: suggesters.py SuggestionSource get_suggestions SEARCHING start={start}")
        # If we have a space separated value, try first the value and then the last word
        key = start.split(' ')[-1]
        keys = [start, key] if start != key else [start]
        sugs = set()
        for initial in keys:
            if self._controller:
                try:
                    sugs.update(self._controller.get_local_namespace_for_row(row).get_suggestions(initial))
                except AttributeError:
                    try:
                      sugs.update(self._controller.get_local_namespace.get_suggestions(initial))
                    except AttributeError:  # For example TestCaseFileController
                        pass
                # return list(sugs)
            if self._plugin:
                sugs.update(self._plugin.content_assist_values(initial))  # DEBUG: Remove old functionality when no more needed
            # print(f"DEBUG: suggesters.py SuggestionSource get_suggestions IN LOOP initial ={initial} len sugs={len(sugs)}")
        return list(sugs)

    def update_from_local(self, words: list, language:str):
        from ..lib.compat.parsing.languages import Language
        if isinstance(language, list):
            language = language[0]
        if language in [None, '', 'English', 'En']:
            localized = Language.from_name('en')
        else:
            localized = Language.from_name(language)
        words.extend(set(list(localized.headers.values()) + list(localized.settings.values()) +
                         list(localized.bdd_prefixes) + localized.true_strings + localized.false_strings))
        namespace = self._controller.get_local_namespace()
        namespace.update_words_cache(words)
        # print(f"DEBUG: suggesters.py SuggestionSource update_from_local words={words} namespace={namespace} "
        #       f"language={localized.name}")

@total_ordering
class _Suggester(object):
    name = None

    @staticmethod
    def _suggestion(name):
        s = lambda: 0
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
        _ = args
        return [s for s in self._suggestions if name is None or name.lower() in s.name.lower()]

    def store(self, name):
        self._suggestions += [self._suggestion(name)]
        # DEBUG For now remove sorting self._suggestions.sort()


class _ImportSuggester(_Suggester):

    def __init__(self, controller):
        self._df_controller = controller.datafile_controller

    def get_suggestions(self, name, *args):
        _ = args
        already_imported = self.get_already_imported()
        all_resources = self.get_all_available()
        suggestion_names = all_resources - already_imported
        return [self._suggestion(n) for n in sorted(suggestion_names) if name in n]

    def get_already_imported(self):
        return set(imp.name for imp in self._df_controller.imports)

    def get_all_available(self):
        return NotImplemented


class ResourceSuggester(_ImportSuggester):

    def get_all_available(self):
        return set(self._df_controller.relative_path_to(r) for r in self._df_controller._project.resources)


class CachedLibrarySuggester(_ImportSuggester):

    def get_all_available(self):
        return set(self._df_controller.get_all_cached_library_names())


class BuiltInLibrariesSuggester(_Suggester):

    def get_suggestions(self, name, *args):
        _ = args
        # print(f"DEBUG: suggesters.py BuiltInLibrariesSuggester get_suggestions ENTER name={name}")
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
        already_imported = self._cached_suggester.get_already_imported()
        return [self._suggestion(s)
                for s in sorted((history | cached | builtin)-already_imported,
                key=lambda s: s.lower())]
