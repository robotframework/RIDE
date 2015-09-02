import unittest

from robotide.robotapi import TestCase
from robotide.controller.macrocontrollers import TestCaseController
from robotide.searchtests.searchtests import TestSearchMatcher


class _TestSearchTest(object):

    def _test(self, name='name', tags=None, doc='documentation'):
        parent = lambda: 0
        parent.datafile_controller = parent
        parent.register_for_namespace_updates = lambda *_: 0
        parent.force_tags = []
        parent.default_tags = []
        robot_test = TestCase(parent=parent, name=name)
        robot_test.get_setter('documentation')(doc)
        robot_test.get_setter('tags')(tags or [])
        test = TestCaseController(parent, robot_test)
        return test

    def _match(self, text, name='name', tags=None, doc='documentation'):
        return TestSearchMatcher(text).matches(self._test(name, tags, doc))


class TestTestSearchMatcher(_TestSearchTest, unittest.TestCase):

    def test_matching_name(self):
        self.assertTrue(self._match('name', name='name'))

    def test_not_matching(self):
        self.assertFalse(self._match('tERm', name='no match',
                                     tags=['no match'], doc='no match'))

    def test_matching_name_partially(self):
        self.assertTrue(self._match('match', doc='prefix[match]postfix'))

    def test_matching_name_is_case_insensitive_in_tags(self):
        self.assertTrue(self._match('mAtCh', tags=['MATcH']))

    def test_matching_name_is_case_insensitive_in_name(self):
        self.assertTrue(self._match('mAtCh', name=' MATcH'))

    def test_matching_name_is_case_insensitive_in_doc(self):
        self.assertTrue(self._match('mAtCh', doc='Doc MATcHoc'))

    def test_matching_to_documentation(self):
        self.assertTrue(self._match('docstring', doc='docstring matching!'))

    def test_matching_to_tag(self):
        self.assertTrue(self._match('tag', tags=['tag']))

    def test_multiple_match_terms(self):
        self.assertTrue(self._match(
            'name tag doc', name='name!',
            tags=['foo', 'tag', 'bar'], doc='well doc to you!'))
