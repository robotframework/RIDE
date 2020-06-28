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
import sys
import unittest
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.spec.librarydatabase import LibraryDatabase
from robotide.spec.libraryfetcher import get_import_result

testlibpath = os.path.join(os.path.dirname(__file__), '..', 'resources',
                           'robotdata', 'lib_with_doc_format')
sys.path.append(testlibpath)

class TestLibraryDatabase(unittest.TestCase):

    def setUp(self):
        self._database = LibraryDatabase(':memory:')
        self._database.create_database()

    def tearDown(self):
        self._database.close()

    def test_inserting_and_fetching(self):
        collections_kws = self._get_and_insert_keywords('Collections', '')
        string_kws = self._get_and_insert_keywords('String', '')
        builtin_kws = self._get_and_insert_keywords('BuiltIn', '')
        collections_kws_from_db = self._database.fetch_library_keywords('Collections', '')
        string_kws_from_db = self._database.fetch_library_keywords('String', '')
        builtin_kws_from_db = self._database.fetch_library_keywords('BuiltIn', '')
        for originals, from_database in [[collections_kws, collections_kws_from_db],
                                         [string_kws, string_kws_from_db],
                                         [builtin_kws, builtin_kws_from_db]]:
            self._check_keywords(originals, from_database)

    def test_libkw_doc_format(self):
        self._get_and_insert_keywords('testLibText', '')
        self._get_and_insert_keywords('testLibRobot', '')
        self._get_and_insert_keywords('testLibRest', '')
        self._get_and_insert_keywords('testLibHtml', '')
        self._get_and_insert_keywords('testLibHtmlClass', '')

        text_doc_format_kws = self._database.fetch_library_keywords('testLibText', '')
        robot_doc_format_kws = self._database.fetch_library_keywords('testLibRobot', '')
        rest_doc_format_kws = self._database.fetch_library_keywords('testLibRest', '')
        html1_doc_format_kws = self._database.fetch_library_keywords('testLibHtml', '')
        html2_doc_format_kws = self._database.fetch_library_keywords('testLibHtmlClass', '')

        self.assertTrue(all([kw.doc_format == "TEXT" for kw in text_doc_format_kws]))
        self.assertTrue(all([kw.doc_format == "ROBOT" for kw in robot_doc_format_kws]))
        self.assertTrue(all([kw.doc_format == "REST" for kw in rest_doc_format_kws]))
        self.assertTrue(all([kw.doc_format == "HTML" for kw in html1_doc_format_kws]))
        self.assertTrue(all([kw.doc_format == "HTML" for kw in html2_doc_format_kws]))

    def test_valid_doc_format(self):
        for format in ("TEXT", "ROBOT", "REST", "HTML"):
            orig_kws = [LibraryKeywordInfo('first', 'doc', format, 'lib.py', ''),
                        LibraryKeywordInfo('second', 'doc', format, 'lib.py', ''),
                        LibraryKeywordInfo('third', 'doc', format, 'lib.py', '')]
                        
            self._database.insert_library_keywords('lib.py', 'foo', orig_kws)
            kws = self._database.fetch_library_keywords('lib.py', 'foo')
            for kw in kws:
                self.assertEqual(kw.doc_format, format)
    
    def test_default_doc_format(self):
        for format in ("non", "valid", "format", ""):
            self._database.insert_library_keywords('lib.py', 'foo', [LibraryKeywordInfo('this is old', 'doc', format, 'lib.py', '')])
            kws = self._database.fetch_library_keywords('lib.py', 'foo')
            self.assertEqual(kws[0].doc_format, "ROBOT")
        
        kws = self._get_and_insert_keywords('String', '')
        for kw in kws:
            self.assertEqual(kw.doc_format, "ROBOT")
    
    def test_finds_newest_version(self):
        self._database.insert_library_keywords('lib.py', 'foo', [LibraryKeywordInfo('this is old', 'doc', 'ROBOT', 'lib.py', '')])
        self._database.insert_library_keywords('lib.py', 'foo', [LibraryKeywordInfo('this is new', 'doc', 'ROBOT', 'lib.py', '')])
        kws = self._database.fetch_library_keywords('lib.py', 'foo')
        self.assertEqual(len(kws), 1, str(kws))
        self.assertEqual(kws[0].name, 'this is new')

    def test_removing_old_data(self):
        self._get_and_insert_keywords('String', '')
        self._get_and_insert_keywords('String', '')
        newest = self._get_and_insert_keywords('String', '')
        newest_again = self._database.fetch_library_keywords('String', '')
        self._check_keywords(newest, newest_again)
        self.assertEqual(self._database._connection.execute('select count(*) from libraries').fetchone()[0], 1)
        self.assertEqual(self._database._connection.execute('select count(*) from keywords').fetchone()[0], len(newest))

    def test_unknown_library_keywords_fetch(self):
        results = self._database.fetch_library_keywords('Something that is not there', 'at all')
        self.assertEqual(len(results), 0)

    def test_unknown_library_fetch(self):
        self.assertFalse(self._database.library_exists('library', ''))
        self._database.insert_library_keywords('library', '', [])
        self.assertTrue(self._database.library_exists('library', ''))

    def _get_and_insert_keywords(self, library_name, library_arguments):
        kws = get_import_result(library_name, library_arguments)
        self._database.insert_library_keywords(library_name, library_arguments, kws)
        return kws

    def _check_keywords(self, originals, from_database):
        for k1, k2 in zip(originals, from_database):
            self.assertEqual(k1.name, k2.name)
            self.assertEqual(k1.doc, k2.doc)
            self.assertEqual(k1.doc_format, k2.doc_format)
            self.assertEqual(k1.arguments, k2.arguments, 'Arguments differ ("%s" != "%s") on keyword %s' %
                                                         (k1.arguments, k2.arguments, k1.name))
            self.assertEqual(k1.source, k2.source)
        self.assertEqual(len(originals), len(from_database))

if __name__ == '__main__':
    unittest.main()
