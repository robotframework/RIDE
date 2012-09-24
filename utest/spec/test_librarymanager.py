import unittest
from robotide.spec.libraryfetcher import LibraryManager, _get_keywords, _keywords_differ

class TestLibraryManager(unittest.TestCase):

    def setUp(self):
        self._keywords = None
        self._library_manager = LibraryManager(':memory:')
        self._library_manager.create_database()
        self._library_manager.start()

    def test_database_update(self):
        self._library_manager.fetch_keywords('BuiltIn', '', self._callback)
        keywords = _get_keywords('BuiltIn', '')
        self._stop_and_join()
        self.assertFalse(_keywords_differ(keywords, self._keywords))

    def test_database_actor_handles_callback_exception(self):
        self._library_manager.fetch_keywords('Collections', '', (lambda *_: 1/0))
        self._library_manager.fetch_keywords('BuiltIn', '', self._callback)
        self._stop_and_join()
        self.assertIsNotNone(self._keywords)

    def test_fetching_unknown_library(self):
        self._library_manager.fetch_keywords('FooBarZoo', '', self._callback)
        self._stop_and_join()
        self.assertEqual(self._keywords, [])

    def _stop_and_join(self):
        self._library_manager.stop()
        self._library_manager.join()

    def _callback(self, keywords):
        self._keywords = keywords


if __name__ == '__main__':
    unittest.main()
