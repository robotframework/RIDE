#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robot.utils.asserts import assert_equals
from robotide.controller.ui.treecontroller import TreeController, _History


class ActionRegistererMock(object):

    def register_actions(self, action_collections):
        self.action_collections = action_collections

    def register_action(self, action):
        pass


class TestTreeController(unittest.TestCase):

    def test_register_tree_actions(self):
        mocked_ar = ActionRegistererMock()
        TreeController(None, mocked_ar, None, None).register_tree_actions()
        self.assertEquals(["Go &Back", "Go &Forward"], [a.name for a in mocked_ar.action_collections])


class _BaseTreeControllerTest(object):

    def setUp(self):
        self.history = _History()
        self.controller = TreeController(self._tree_mock(), None, None, None, history=self.history)
        self.controller.add_to_history("Top Suite")

    def _tree_mock(self):
        tree_mock = lambda:0
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
        self.assertEquals('Top Suite', self._go_back_and_return_selection())

    def test_go_back_two_levels(self):
        nodes = ['Top Suite Fake UK 1', 'Sub Suite 1', 'Sub Suite 1 Fake UK 0']
        for name in nodes:
            self._select_node(name)
        nodes.reverse()
        for name in nodes[1:]:
            self.assertEquals(name, self._go_back_and_return_selection())

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
        nodes = ['Top Suite Fake UK 0', 'Resource Keyword', 'Sub Suite 0 Fake UK 2']
        for name in nodes:
            self._select_node(name)
        self._go_back_and_assert_selection('Resource Keyword')
        self._go_back_and_assert_selection('Top Suite Fake UK 0')
        self._go_forward_and_assert_selection('Resource Keyword')
        self._go_forward_and_assert_selection('Sub Suite 0 Fake UK 2')

    def _go_back_and_assert_selection(self, expected_selection):
        assert_equals(self._go_back_and_return_selection(), expected_selection)

    def _go_forward_and_assert_selection(self, expected_selection):
        assert_equals(self._go_forward_and_return_selection(), expected_selection)


if __name__ == '__main__':
    unittest.main()



