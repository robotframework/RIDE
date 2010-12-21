import unittest
import sys
import os

from robotide.namespace import cache
from robot.utils.asserts import assert_true, assert_false

from resources import DATAPATH
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

    def _assert_keyword_in_keywords(self, keywords, name):
        for kw in keywords:
            if kw.name == name:
                return
        raise AssertionError('Keyword %s not found in default keywords' % name)


if __name__ == "__main__":
    unittest.main()