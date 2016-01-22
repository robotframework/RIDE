import unittest
from robotide.namespace.namespace import _Keywords
from nose.tools import assert_true, assert_false, assert_equals


class ItemMock(object):

    def __init__(self, name, args, long):
        self.name = name
        self.arguments = args
        self.longname = long


class TestKeywords(unittest.TestCase):

    def setUp(self):
        self.kws = _Keywords(
            [ItemMock('My kw', ['${arg}'], 'source.My kw'),
             ItemMock('Given foo', [], 'source.Given foo'),
             ItemMock('${user} should ${foo} and ${bar}', [], 'longem'),
             ItemMock('this ${has} real args', ['${arg}'], 'long.normal')])

    def test_parse_keywords(self):
        assert_true(self.kws.get('My kw'))

    def test_normalize(self):
        assert_true(self.kws.get('mykw'))
        assert_true(self.kws.get('M Y     KW'))
        assert_false(self.kws.get('my kw?'))

    def test_underscore_normalization(self):
        assert_true(self.kws.get('m_ykw'))
        assert_true(self.kws.get('_mY_kw_'))

    def test_longname(self):
        assert_true(self.kws.get('source.my kw'))

    def test_given_when_then(self):
        assert_true(self.kws.get('Given foo'))
        assert_true(self.kws.get('Given my kw'))
        assert_true(self.kws.get('When my kw'))
        assert_true(self.kws.get('then mykw'))
        assert_true(self.kws.get('  and  given foo'))
        assert_true(self.kws.get('But my kw'))

    def test_embedded_args(self):
        assert_true(self.kws.get(
            'john should embed arguments and something'))
        assert_true(self.kws.get(
            'WHEN john should embed arguments and something'))
        assert_true(self.kws.get(
            'but john should embed arguments and something'))
        assert_false(self.kws.get(
            'this keyword has real args'))

    def test_embedded_args_are_space_sensitive(self):
        assert_false(self.kws.get(
            'john shouldembed arguments and something'))
        assert_false(self.kws.get(
            'given johnshould embed arguments and something'))

    def test_first_come_prioritized_when_same_short_name(self):
        kws = _Keywords([ItemMock('My kw', ['${arg}'], 'source.My kw'),
                         ItemMock('My kw', [], 'Collision!')])
        assert_equals(kws.get('My kw').arguments, ['${arg}'])
        assert_equals(kws.get('Collision!').arguments, [])


if __name__ == "__main__":
    unittest.main()
