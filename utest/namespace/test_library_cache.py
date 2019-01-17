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
import sys
import os
from robotide.spec.librarymanager import LibraryManager
from threading import Thread

from robotide.namespace.cache import LibraryCache

from resources import DATAPATH

sys.path.append(os.path.join(DATAPATH, 'libs'))


class TestLibraryCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._library_manager = LibraryManager(':memory:')
        cls._library_manager.start()
        cls._library_manager.create_database()

    @classmethod
    def tearDownClass(cls):
        cls._library_manager.stop()
        cls._library_manager = None

    def test_auto_importing_libraries(self):
        cache = self._create_cache_with_auto_imports('TestLib')
        self._assert_keyword_in_keywords(cache.get_default_keywords(), 'Testlib Keyword')

    def test_auto_importing_libraries_with_arguments(self):
        cache = self._create_cache_with_auto_imports('ArgLib|foo')
        self._assert_keyword_in_keywords(cache.get_default_keywords(), 'Get Mandatory')

    def test_importing_library_with_dictionary_arg(self):
        LibraryCache({}, lambda:0, self._library_manager)._get_library('ArgLib', [{'moi':'hoi'}, []])

    def test_importing_from_two_threads(self):
        cache = self._create_cache_with_auto_imports('TestLib')
        self._thread_results = []
        def check_test_lib_keyword():
            cache.get_default_keywords()
            self._thread_results.append('ok')
        t1 = Thread(target=check_test_lib_keyword)
        t2 = Thread(target=check_test_lib_keyword)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(['ok', 'ok'], self._thread_results)

    def _create_cache_with_auto_imports(self, auto_import):
        settings = {'auto imports': [auto_import]}
        return LibraryCache(settings, lambda:0, self._library_manager)

    def _assert_keyword_in_keywords(self, keywords, name):
        for kw in keywords:
            if kw.name == name:
                return
        raise AssertionError('Keyword %s not found in default keywords' % name)


if __name__ == "__main__":
    unittest.main()
