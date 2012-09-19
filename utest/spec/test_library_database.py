import os
import sqlite3
import unittest
import time
from robotide import spec
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.spec.libraryfetcher import _get_keywords

class TestLibraryDatabase(unittest.TestCase):

    def test_testing(self):
        conn = sqlite3.connect(':memory:')
        with open(os.path.join(os.path.split(spec.__file__)[0], 'create_database.sql')) as script:
            conn.executescript(script.read())
        collections_kws = self._get_and_insert_keywords(conn, 'Collections', '')
        string_kws = self._get_and_insert_keywords(conn, 'String', '')
        collections_kws_from_db = self._fetch_keywords_from_db(conn, 'Collections', '')
        string_kws_from_db = self._fetch_keywords_from_db(conn, 'String', '')
        self._check_keywords(collections_kws, collections_kws_from_db)
        self._check_keywords(string_kws, string_kws_from_db)

    def _get_and_insert_keywords(self, conn, library_name, library_arguments):
        kws = _get_keywords(library_name, library_arguments)
        conn.execute('insert into libraries values (null, ?, ?, ?)', (library_name, library_arguments, time.time()))
        lib = [l for l in conn.execute('select * from libraries where name = ? and arguments = ?', (library_name, library_arguments))][0]
        keyword_values = [[kw.name, kw.doc, u' | '.join(kw.arguments), lib[0]] for kw in kws]
        conn.executemany('insert into keywords values (?, ?, ?, ?)', keyword_values)
        return kws

    def _fetch_keywords_from_db(self, conn, library_name, library_arguments):
        lib = [l for l in conn.execute('select * from libraries where name = ? and arguments = ?', (library_name, library_arguments))][0]
        return [LibraryKeywordInfo(name, doc, lib[1], arguments.split(u' | '))
                for name, doc, arguments in
                conn.execute('select name, doc, arguments from keywords where library = ?', [lib[0]])]

    def _check_keywords(self, originals, from_database):
        for k1, k2 in zip(originals, from_database):
            self.assertEqual(k1.name, k2.name)
            self.assertEqual(k1.doc, k2.doc)
            self.assertEqual(k1.arguments, k2.arguments)
            self.assertEqual(k1.source, k2.source)
        self.assertEqual(len(originals), len(from_database))

if __name__ == '__main__':
    unittest.main()
