import os
import sqlite3
import unittest
import time
from robotide import spec
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.spec.libraryfetcher import _get_keywords

class TestLibraryDatabase(unittest.TestCase):

    def setUp(self):
        self._connection = sqlite3.connect(':memory:')
        with open(os.path.join(os.path.split(spec.__file__)[0], 'create_database.sql')) as script:
            self._connection.executescript(script.read())

    def tearDown(self):
        self._connection.close()

    def test_inserting_and_fetching(self):
        collections_kws = self._get_and_insert_keywords('Collections', '')
        string_kws = self._get_and_insert_keywords('String', '')
        collections_kws_from_db = self._fetch_keywords_from_db('Collections', '')
        string_kws_from_db = self._fetch_keywords_from_db('String', '')
        self._check_keywords(collections_kws, collections_kws_from_db)
        self._check_keywords(string_kws, string_kws_from_db)

    def test_finds_newest_version(self):
        lib = self._insert_library('lib.py', 'foo')
        self._insert_library_keywords([['this is old', 'doc', '', lib[0]]])
        lib = self._insert_library('lib.py', 'foo')
        self._insert_library_keywords([['this is new', 'doc', '', lib[0]]])
        kws = self._fetch_keywords_from_db('lib.py', 'foo')
        self.assertEqual(len(kws), 1)
        self.assertEqual(kws[0].name, 'this is new')

    def test_removing_old_data(self):
        self._get_and_insert_keywords('String', '')
        self._get_and_insert_keywords('String', '')
        newest = self._get_and_insert_keywords('String', '')
        self._remove_old_library_data('String', '')
        newest_again = self._fetch_keywords_from_db('String', '')
        self._check_keywords(newest, newest_again)
        count = self._connection.execute('select count(*) from libraries').fetchone()[0]
        self.assertEqual(count, 1)

    def test_unknown_library_keywords_fetch(self):
        results = self._fetch_keywords_from_db('Something that is not there', 'at all')
        self.assertEqual(len(results), 0)

    def test_unknown_library_fetch(self):
        self.assertIsNone(self._fetch_lib('is not there', 'is not'))

    def _remove_old_library_data(self, name, arguments):
        new = self._fetch_lib(name, arguments)
        old_versions = self._connection.execute('select id from libraries where name = ? and arguments = ? and id != ?', (name, arguments, new[0])).fetchall()
        self._connection.executemany('delete from keywords where library = ?', old_versions)
        self._connection.execute('delete from libraries where name = ? and arguments = ? and id != ?', (name, arguments, new[0]))

    def _get_and_insert_keywords(self, library_name, library_arguments):
        kws = _get_keywords(library_name, library_arguments)
        lib = self._insert_library(library_name, library_arguments)
        keyword_values = [[kw.name, kw.doc, u' | '.join(kw.arguments), lib[0]] for kw in kws]
        self._insert_library_keywords(keyword_values)
        return kws

    def _insert_library(self, name, arguments):
        self._connection.execute('insert into libraries values (null, ?, ?, ?)', (name, arguments, time.time()))
        return self._fetch_lib(name, arguments)

    def _fetch_lib(self, name, arguments):
        t = self._connection.execute('select max(last_updated) from libraries where name = ? and arguments = ?', (name, arguments)).fetchone()[0]
        return self._connection.execute('select * from libraries where name = ? and arguments = ? and last_updated = ?', (name, arguments, t)).fetchone()

    def _insert_library_keywords(self, data):
        self._connection.executemany('insert into keywords values (?, ?, ?, ?)', data)

    def _fetch_keywords_from_db(self, library_name, library_arguments):
        lib = self._fetch_lib(library_name, library_arguments)
        if lib is None:
            return []
        return [LibraryKeywordInfo(name, doc, lib[1], arguments.split(u' | '))
                for name, doc, arguments in
                self._connection.execute('select name, doc, arguments from keywords where library = ?', [lib[0]])]

    def _check_keywords(self, originals, from_database):
        for k1, k2 in zip(originals, from_database):
            self.assertEqual(k1.name, k2.name)
            self.assertEqual(k1.doc, k2.doc)
            self.assertEqual(k1.arguments, k2.arguments)
            self.assertEqual(k1.source, k2.source)
        self.assertEqual(len(originals), len(from_database))

if __name__ == '__main__':
    unittest.main()
