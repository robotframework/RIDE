import unittest
import time
from nose.tools import assert_is_none, assert_equals

from robotide.namespace.cache import ExpiringCache


class TestExpiringCache(unittest.TestCase):

    def test_cache_hit(self):
        cache = ExpiringCache(0.1)
        cache.put('a', 'b')
        assert_equals('b', cache.get('a'))

    def test_cache_expiration(self):
        cache = ExpiringCache(0.01)
        cache.put('a', 'b')
        time.sleep(0.1)
        assert_is_none(cache.get('a'))
        cache.put('a', 'c')
        assert_equals('c', cache.get('a'))


if __name__ == "__main__":
    unittest.main()
