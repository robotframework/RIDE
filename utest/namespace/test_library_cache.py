import unittest
import sys
import os

from robotide.namespace import cache
from robot.utils.asserts import assert_true, assert_false

from resources import DATAPATH
sys.path.append(os.path.join(DATAPATH, 'libs'))


class TestLibraryCache(unittest.TestCase):

    def test_reset_keywords(self):
        lib_cache = cache.LibraryCache()
        lib_cache.add_library('OperatingSystem')
        assert_true(lib_cache.library_keywords)
        lib_cache.reset()
        assert_false(lib_cache.library_keywords)

    def test_reset_default_keywords(self):
        lib_cache = cache.LibraryCache()
        kws = lib_cache.get_default_keywords()
        kws2 = lib_cache.get_default_keywords()
        assert_true(kws[0] is kws2[0])
        lib_cache.reset()
        kws3 = lib_cache.get_default_keywords()
        assert_false(kws[0] is kws3[0])

    def test_auto_importing_libraries(self):
        cache.SETTINGS = {'auto imports': ['TestLib']}
        self._assert_keyword_in_keywords(cache.LibraryCache().get_default_keywords(),
                                         'Testlib Keyword')

    def test_auto_importing_libraries_after_reset(self):
        cache.SETTINGS = {'auto imports': ['TestLib']}
        lib_cache = cache.LibraryCache()
        self._assert_keyword_in_keywords(lib_cache.get_default_keywords(),
                                         'Testlib Keyword')
        lib_cache.reset()
        self._assert_keyword_in_keywords(lib_cache.get_default_keywords(),
                                 'Testlib Keyword')

    def test_auto_importing_libraries_with_arguments(self):
        cache.SETTINGS = {'auto imports': ['ArgLib|foo']}
        self._assert_keyword_in_keywords(cache.LibraryCache().get_default_keywords(),
                                         'Get Mandatory')

    def _assert_keyword_in_keywords(self, keywords, name):
        for kw in keywords:
            if kw.name == name:
                return
        raise AssertionError('Keyword %s not found in default keywords' % name)


if __name__ == "__main__":
    unittest.main()