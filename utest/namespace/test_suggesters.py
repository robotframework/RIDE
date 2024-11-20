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

import unittest
from robotide.controller.filecontrollers import ResourceFileController
from robotide.robotapi import STDLIB_NAMES
from robotide.namespace.suggesters import ResourceSuggester, CachedLibrarySuggester, BuiltInLibrariesSuggester, LibrariesSuggester, HistorySuggester
from robotide.utils import overrides


class _ImportSuggesterHelpers(object):

    def _assert_suggestion_names(self, expected, value):
        self.assertEqual(expected, self._suggestion_names(value))

    def _suggestion_names(self, value):
        return [s.name for s in self._suggester.get_suggestions(value) if s.name != 'Telnet']


class _ImportSuggesterTests(_ImportSuggesterHelpers):

    def setUp(self):
        self._suggester = self._create_suggester(['foofoo'], ['foofoo', 'foobar', 'barbar', 'doodoo'])

    def test_all_suggestions_with_empty_string(self):
        self._assert_suggestion_names(['barbar', 'doodoo', 'foobar'], '')

    def test_only_matching_suggestion(self):
        self._assert_suggestion_names(['foobar'], 'foo')

    def test_multiple_matching_suggestions(self):
        self._assert_suggestion_names(['barbar', 'foobar'], 'bar')

    def test_no_matching_suggestions(self):
        self._assert_suggestion_names([], 'zoo')

    def _controller(self, imports=(), resources=(), libraries=()):
        controller = lambda:0
        controller.datafile_controller = controller
        controller.relative_path_to = lambda other: other.display_name
        controller.imports = [self._import(i) for i in imports]
        controller._project = controller
        controller.resources = [self._resource(r) for r in resources]
        controller.get_all_cached_library_names = lambda: libraries[:]
        return controller

    def _resource(self, name):
        data = lambda:0
        data.source = name
        data.directory = '.'
        resource = ResourceFileController(data)
        return resource

    def _import(self, name):
        imp = lambda:0
        imp.name = name
        return imp


class TestResourceSuggester(_ImportSuggesterTests, unittest.TestCase):

    def _create_suggester(self, already_imported=(), available=()):
        return ResourceSuggester(self._controller(imports=already_imported, resources=available))


class TestCachedLibrarySuggester(_ImportSuggesterTests, unittest.TestCase):

    def _create_suggester(self, already_imported=(), available=()):
        return CachedLibrarySuggester(self._controller(imports=already_imported, libraries=available))

class TestBuiltInLibrariesSuggester(_ImportSuggesterHelpers, unittest.TestCase):

    def setUp(self):
        self._suggester = BuiltInLibrariesSuggester()

    def test_returns_all_builtin_libraries_with_empty_string(self):
        # print(f"DEBUG: test_suggesters.py {[x for x in STDLIB_NAMES]}")
        self._assert_suggestion_names(['Collections',
                                       'DateTime',
                                       'Dialogs',
                                       'OperatingSystem',
                                       'Process',
                                       'Remote',
                                       'Screenshot',
                                       'String',
                                       # 'Telnet',  # Broken in Python 3.13, RF 7.1.1
                                       'XML'], '')

    def test_returns_matching_builtin_libraries(self):
        self._assert_suggestion_names(['Remote', 'Screenshot'], 're')

class TestLibrariesSuggester(_ImportSuggesterTests, unittest.TestCase):

    def _create_suggester(self, already_imported=(), available=()):
        self._history_suggester = HistorySuggester()
        return LibrariesSuggester(self._controller(imports=already_imported, libraries=available),
                                  self._history_suggester)

    # @overrides(_ImportSuggesterTests)
    def test_all_suggestions_with_empty_string(self):
        self._assert_suggestion_names(['barbar',
                                       'Collections',
                                       'DateTime',
                                       'Dialogs',
                                       'doodoo',
                                       'foobar',
                                       'OperatingSystem',
                                       'Process',
                                       'Remote',
                                       'Screenshot',
                                       'String',
                                        # 'Telnet',  # Broken in Python 3.13, RF 7.1.1
                                       'XML'], '')

    def test_history(self):
        self._assert_suggestion_names([], 'ooz')
        self._history_suggester.store(u'zooZoo')
        self._assert_suggestion_names([u'zooZoo'], 'ooz')


if __name__ == '__main__':
    unittest.main()
