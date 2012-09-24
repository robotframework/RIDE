import unittest
import time
from robotide.spec.libraryfetcher import _get_keywords
from robotide.spec.librarymanager import LibraryManager


class TestLibraryManager(unittest.TestCase):

    def setUp(self):
        self._keywords = None
        self._library_manager = LibraryManager(':memory:')
        self._library_manager._initiate_database_connection()
        self._library_manager._database.create_database()

    def tearDown(self):
        self._library_manager._database.close()

    def test_database_update(self):
        self._library_manager.fetch_keywords('BuiltIn', '', self._callback)
        keywords = _get_keywords('BuiltIn', '')
        self._library_manager._handle_message()
        self.assertFalse(self._library_manager._keywords_differ(keywords, self._keywords))

    def test_manager_handles_callback_exception(self):
        self._library_manager.fetch_keywords('Collections', '', (lambda *_: 1/0))
        self._library_manager._handle_message()
        self._library_manager.fetch_keywords('BuiltIn', '', self._callback)
        self._library_manager._handle_message()
        self.assertIsNotNone(self._keywords)

    def test_fetching_unknown_library(self):
        self._library_manager.fetch_keywords('FooBarZoo', '', self._callback)
        self._library_manager._handle_message()
        self.assertEqual(self._keywords, [])

    def _stop_and_run(self):
        self._library_manager.stop()
        self._library_manager.run()

    def _callback(self, keywords):
        self._keywords = keywords


if __name__ == '__main__':
    unittest.main()
