#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import unittest
from nose.tools import assert_equal

from robotide.robotapi import TestCase, TestCaseFile
from robotide.controller.ctrlcommands import ChangeTag
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.macrocontrollers import TestCaseController
from robotide.controller.tablecontrollers import TestCaseTableController
from robotide.controller.tags import Tag
from robotide.controller.ui.treecontroller import TreeController, _History, \
    TestSelectionController


class ActionRegistererMock(object):

    def register_actions(self, action_collections):
        self.action_collections = action_collections

    def register_action(self, action):
        pass


class TestTreeController(unittest.TestCase):

    def test_register_tree_actions(self):
        mocked_ar = ActionRegistererMock()
        TreeController(None, mocked_ar, None, None).register_tree_actions()
        self.assertEqual(
            ["Go &Back", "Go &Forward"],
            [a.name for a in mocked_ar.action_collections])


class _BaseTreeControllerTest(object):

    def setUp(self):
        self.history = _History()
        self.controller = TreeController(
            self._tree_mock(), None, None, None, history=self.history)
        self.controller.add_to_history("Top Suite")

    def _tree_mock(self):
        tree_mock = lambda: 0
        self._tree_mock_items = []
        tree_mock.SelectItem = lambda i: self._tree_mock_items.append(i)
        return tree_mock

    def _select_node(self, value):
        self.controller.add_to_history(value)

    def _go_back_and_return_selection(self):
        self.controller.OnGoBack(None)
        return self._tree_mock_items[-1]

    def _go_forward_and_return_selection(self):
        self.controller.OnGoForward(None)
        return self._tree_mock_items[-1]


class TestNavigationHistory(_BaseTreeControllerTest, unittest.TestCase):

    def test_go_back_one_level(self):
        self._select_node('Top Suite Fake UK 2')
        self.assertEqual('Top Suite', self._go_back_and_return_selection())

    def test_go_back_two_levels(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        nodes.reverse()
        for name in nodes[1:]:
            self.assertEqual(name, self._go_back_and_return_selection())

    def test_it_is_not_possible_to_go_back_farther_than_history(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        nodes.reverse()
        for name in nodes[1:] + ['Top Suite']:
            self._go_back_and_assert_selection(name)
        self._go_back_and_assert_selection('Top Suite')

    def test_go_back_with_selecting_in_between(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        self._go_back_and_assert_selection('Sub Suite 1')
        self._select_node('Sub Suite 2 Fake UK 0')
        self._go_back_and_assert_selection('Sub Suite 1')

    def test_go_forward(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        for _ in range(3):
            self.controller.OnGoBack(None)
        for name in nodes:
            self._go_forward_and_assert_selection(name)

    def test_go_back_and_forward_between_suite_and_resource(self):
        nodes = ['Top Suite Fake UK 0', 'Resource Keyword',
                 'Sub Suite 0 Fake UK 2']
        for name in nodes:
            self._select_node(name)
        self._go_back_and_assert_selection('Resource Keyword')
        self._go_back_and_assert_selection('Top Suite Fake UK 0')
        self._go_forward_and_assert_selection('Resource Keyword')
        self._go_forward_and_assert_selection('Sub Suite 0 Fake UK 2')

    def _go_back_and_assert_selection(self, expected_selection):
        assert_equal(self._go_back_and_return_selection(), expected_selection)

    def _go_forward_and_assert_selection(self, expected_selection):
        assert_equal(
            self._go_forward_and_return_selection(), expected_selection)


class TestTestSelectionController(unittest.TestCase):

    def setUp(self):
        self._tsc = TestSelectionController()

    def test_test_selection_is_empty_by_default(self):
        self.assertTrue(self._tsc.is_empty())

    def test_test_selection_is_not_empty_when_it_contains_a_test(self):
        self._tsc.select(self._create_test())
        self.assertFalse(self._tsc.is_empty())

    def test_test_selection_is_empty_after_removing_same_test_from_there_even_when_it_is_not_the_same_object(self):
        test = self._create_test()
        self._tsc.select(test)
        self._tsc.select(test, False)
        self.assertTrue(self._tsc.is_empty())

    def test_is_test_selected(self):
        test = self._create_test()
        self.assertFalse(self._tsc.is_test_selected(test))

        self._tsc.select(test)
        self.assertTrue(self._tsc.is_test_selected(test))

    def test_adding_tag_to_selected_tests(self):
        tests = [self._create_test('test%d' % i) for i in range(10)]
        for t in tests:
            self._tsc.select(t)
        self._tsc.add_tag('foo')
        for t in tests:
            self.assertEqual([tag.name for tag in t.tags], ['foo'])

    def test_adding_a_tag_to_test_with_a_default_tag(self):
        test = self._create_test()
        test.datafile_controller.default_tags.execute(
            ChangeTag(Tag(None), 'default'))
        assert_equal([t.name for t in test.tags], ['default'])
        self._tsc.select(test)
        self._tsc.add_tag('custom')
        self.assertEqual([t.name for t in test.tags], ['default', 'custom'])

    def _create_test(self, name='test'):
        suite = TestCaseFile(source='suite')
        suite_controller = TestCaseFileController(suite)
        parent = TestCaseTableController(
            suite_controller, suite.testcase_table)
        test = TestCase(parent=lambda: 0, name=name)
        return TestCaseController(parent, test)


if __name__ == "__main__":
    unittest.main()
