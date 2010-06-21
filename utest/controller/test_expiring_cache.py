import unittest
from robotide.namespace.namespace import ExpiringCache
from numpy.ma.testutils import assert_equal
import time
from robot.utils.asserts import assert_none



class TestExpiringCache(unittest.TestCase):

    def test_cache_hit(self):
        cache = ExpiringCache(0.1)
        cache.put('a', 'b')
        assert_equal('b', cache.get('a'))

    def test_cache_expiration(self):
        cache = ExpiringCache(0.01)
        cache.put('a', 'b')
        time.sleep(0.1)
        assert_none(cache.get('a'))
        cache.put('a', 'c')
        assert_equal('c', cache.get('a'))


if __name__ == "__main__":
    unittest.main()