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

from utest.ui.test_tree import _BaseSuiteTreeTest


class TestRestoringSelectionAcrossPopulate(_BaseSuiteTreeTest):
    """Saving a directory __init__.robot rebuilds the tree, dropping every controller.

    TreePlugin.on_saving restores the selection through the node labels only, so these
    tests exercise that round trip."""

    def test_label_path_of_nested_node(self):
        self._select_node('Sub Suite 1 Fake Test 2')
        assert self._tree.get_label_path() == \
               ['Top Suite', 'Sub Suite 1', 'Sub Suite 1 Fake Test 2']

    def test_label_path_of_an_explicitly_given_node(self):
        node = self._get_node('Sub Suite 0 Fake UK 1')
        assert self._tree.get_label_path(node) == \
               ['Top Suite', 'Sub Suite 0', 'Sub Suite 0 Fake UK 1']

    def test_label_path_is_empty_without_selection(self):
        self._tree.UnselectAll()
        assert self._tree.get_label_path() == []

    def test_selection_survives_repopulate(self):
        self._select_node('Sub Suite 1 Fake Test 2')
        path = self._tree.get_label_path()
        self._tree.populate(self._model, select_first=False)
        assert self._get_selected_label() != 'Sub Suite 1 Fake Test 2'
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 1 Fake Test 2'

    def test_keyword_selection_survives_repopulate(self):
        self._select_node('Sub Suite 2 Fake UK 3')
        path = self._tree.get_label_path()
        self._tree.populate(self._model, select_first=False)
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 2 Fake UK 3'

    def test_restores_children_that_were_not_rendered_yet(self):
        """populate() only renders the children of datafile_nodes[0], so the target
        node does not exist as a tree item until the path walk expands it."""
        self._select_node('Sub Suite 1 Fake Test 2')
        path = self._tree.get_label_path()
        self._tree.populate(self._model, select_first=False)
        assert self._tree.controller.find_node_with_label(
            self._tree.root, 'Sub Suite 1 Fake Test 2') is None
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 1 Fake Test 2'

    def test_label_path_ignores_the_dirty_marker(self):
        self._select_node('Sub Suite 1 Fake Test 2')
        self._tree.controller.mark_node_dirty(self._get_node('Top Suite'))
        assert self._tree.get_label_path() == \
               ['Top Suite', 'Sub Suite 1', 'Sub Suite 1 Fake Test 2']

    def test_selection_survives_repopulate_of_a_dirty_datafile(self):
        """The node is dirty when the path is captured and clean once saved and
        repopulated, so neither end may depend on the '*' marker."""
        self._select_node('Sub Suite 1 Fake Test 2')
        self._tree.controller.mark_node_dirty(self._get_node('Top Suite'))
        path = self._tree.get_label_path()
        self._tree.populate(self._model, select_first=False)
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 1 Fake Test 2'

    def test_restores_a_node_that_is_still_dirty(self):
        self._select_node('Sub Suite 1 Fake Test 2')
        path = self._tree.get_label_path()
        self._tree.populate(self._model, select_first=False)
        self._tree.controller.mark_node_dirty(self._get_node('Top Suite'))
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 1 Fake Test 2'

    def test_falls_back_to_deepest_match_when_node_is_gone(self):
        path = ['Top Suite', 'Sub Suite 1', 'Removed Test']
        self._tree.select_node_by_label_path(path)
        assert self._get_selected_label() == 'Sub Suite 1'

    def test_returns_none_when_nothing_matches(self):
        assert self._tree.select_node_by_label_path(['No Such Suite']) is None
