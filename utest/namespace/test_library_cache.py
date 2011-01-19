import unittest
import sys
import os

from robotide.namespace import cache
from robot.utils.asserts import assert_true, assert_false, assert_equals, fail

from resources import DATAPATH
from robotide.namespace.cache import _LibraryCache
sys.path.append(os.path.join(DATAPATH, 'libs'))


class TestLibraryCache(unittest.TestCase):

    def test_auto_importing_libraries(self):
        cache.SETTINGS = {'auto imports': ['TestLib']}
        self._assert_keyword_in_keywords(cache.LibraryCache().get_default_keywords(),
                                         'Testlib Keyword')

    def test_auto_importing_libraries_with_arguments(self):
        cache.SETTINGS = {'auto imports': ['ArgLib|foo']}
        self._assert_keyword_in_keywords(cache.LibraryCache().get_default_keywords(),
                                         'Get Mandatory')

    def test_importing_library_with_dictionary_arg(self):
        cache.LibraryCache().add_library('ArgLib', [{'moi':'hoi'}, []])

    def _assert_keyword_in_keywords(self, keywords, name):
        for kw in keywords:
            if kw.name == name:
                return
        raise AssertionError('Keyword %s not found in default keywords' % name)


class TestMutableKeyCache(unittest.TestCase):

    def test_normal_get_set(self):
        cache = _LibraryCache()
        cache[{}] = 1
        assert_equals(1, cache[{}])

    def test_resetting(self):
        cache = _LibraryCache()
        cache['a'] = 'b'
        assert_equals('b', cache['a'])
        cache['a'] = 3
        assert_equals(3, cache['a'])

    def test_mutable_equals(self):
        cache = _LibraryCache()
        cache[['a', []]] = 3
        assert_equals(3, cache[['a', []]])

    def test_self_referencing(self):
        cache = _LibraryCache()
        key = []
        key.append(key)
        cache[key] = 321
        assert_equals(321, cache[key])

    def test_keyerror(self):
        cache = _LibraryCache()
        try:
            cache[3]
            fail()
        except KeyError:
            pass

    def IGNORED_test_timing(self):
        from time import time
        t = time()
        cache = _LibraryCache()
        for i in range(50000):
            cache[i] = i
        for i in range(50000):
            cache[i]
        print time()-t

if __name__ == "__main__":
    unittest.main()