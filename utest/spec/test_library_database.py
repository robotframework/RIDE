import unittest
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.spec.librarydatabase import LibraryDatabase
from robotide.spec.libraryfetcher import get_import_result

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

    def test_finds_newest_version(self):
        self._database.insert_library_keywords('lib.py', 'foo', [LibraryKeywordInfo('this is old', 'doc', 'lib.py', '')])
        self._database.insert_library_keywords('lib.py', 'foo', [LibraryKeywordInfo('this is new', 'doc', 'lib.py', '')])
        kws = self._database.fetch_library_keywords('lib.py', 'foo')
        self.assertEqual(len(kws), 1, unicode(kws))
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
            self.assertEqual(k1.arguments, k2.arguments, 'Arguments differ ("%s" != "%s") on keyword %s' %
                                                         (k1.arguments, k2.arguments, k1.name))
            self.assertEqual(k1.source, k2.source)
        self.assertEqual(len(originals), len(from_database))

if __name__ == '__main__':
    unittest.main()
