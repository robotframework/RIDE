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

import builtins
import wx
from wx.lib.agw.customtreectrl import GenericTreeItem

from robotide import utils
from robotide.action.actioninfo import action_info_collection, ActionInfo
from robotide.context import IS_WINDOWS, ctrl_or_cmd, bind_keys_to_evt_menu
from ..macrocontrollers import TestCaseController
from robotide.controller import ctrlcommands
from robotide.controller.tags import Tag, DefaultTag
from robotide.publish import RideTestSelectedForRunningChanged

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class TreeController(object):

    def __init__(self, tree, action_registerer, settings, test_selection, history=None):
        self._tree = tree
        self._action_registerer = action_registerer
        self.settings = settings
        self._history = history or _History()
        self._test_selection = test_selection

    def register_tree_actions(self):
        tree_actions = _("""[Navigate]
        !Go &Back | Go back to previous location in tree | Alt-%s | ART_GO_BACK
        !Go &Forward | Go forward to next location in tree | Alt-%s | ART_GO_FORWARD
        """) % (('Left', 'Right') if IS_WINDOWS else ('Z', 'X'))
        # Left and right cannot be overridden in tree on non Windows OSses, issue 354

        tree_actions_nt = """[Navigate]
        !Go &Back | Go back to previous location in tree | Alt-%s | ART_GO_BACK
        !Go &Forward | Go forward to next location in tree | Alt-%s | ART_GO_FORWARD
        """ % (('Left', 'Right') if IS_WINDOWS else ('Z', 'X'))

        # print(f"DEBUG: treecontroller.py register_tree_actions ENTER tree_actions={tree_actions}")
        actions = action_info_collection(tree_actions, self, data_nt=tree_actions_nt, container=self._tree)
        self._action_registerer.register_actions(actions)
        self._action_registerer.register_action(ActionInfo(menu_name=_('Edit'), name=_('Add Tag to selected'),
                                                           action=self.on_add_tag_to_selected))
        self._action_registerer.register_action(ActionInfo(menu_name=_('Edit'), name=_('Clear Selected'),
                                                           action=self.on_clear_selected))

    def on_go_back(self, event):
        __ = event
        node = self._history.back()
        if node:
            self._tree.SelectItem(node)

    def on_add_tag_to_selected(self, event):
        __ = event
        if self._test_selection.is_empty():
            return
        name = wx.GetTextFromUser(message=_('Enter Tag Name'), caption=_('Add Tag To Selected'))
        if name:
            self._test_selection.add_tag(name)

    def on_clear_selected(self, event):
        __ = event
        self._test_selection.clear_all(message=None)

    def on_go_forward(self, event):
        __ = event
        node = self._history.forward()
        if node:
            self._tree.SelectItem(node)

    def add_to_history(self, node):
        self._history.change(node)

    def clear_history(self):
        self._history.clear()

    def mark_controller_dirty(self, controller):
        if not controller.dirty:
            return
        node = self.find_node_by_controller(controller)
        if node:
            self.mark_node_dirty(node)

    def mark_node_dirty(self, node):
        text = self._tree.GetItemText(node)
        if not text.startswith('*'):
            self._tree.SetItemText(node, '*' + text)

    def find_node_by_controller(self, controller):
        def match_handler(n):
            handler = self.get_handler(n)
            return handler and controller is handler.controller
        return self._find_node_with_predicate(self._tree.root, match_handler)

    def find_node_with_label(self, node, label):
        # print(f"DEBUG: treecontroller.py TreeController find_node_with_label node={node} LABEL={label}")
        def matcher(n): return utils.eq(self._tree.GetItemText(n), label)
        return self._find_node_with_predicate(node, matcher)

    def _find_node_with_predicate(self, node, predicate):
        # print(f"DEBUG: treecontroller.py TreeController find_node_with_label ENTER node={node}"
        #       f" node is type={type(node)}")
        if node != self._tree.root and isinstance(node, GenericTreeItem) and predicate(node):
            return node
        if not isinstance(node, GenericTreeItem):
            node = self._tree.root
        item, cookie = self._tree.GetFirstChild(node)
        while item:
            if predicate(item):
                return item
            if self._tree.ItemHasChildren(item):
                result = self._find_node_with_predicate(item, predicate)
                if result:
                    return result
            item, cookie = self._tree.GetNextChild(node, cookie)
        return None

    def get_handler(self, node=None):
        return self._tree.GetItemData(node or self._tree.GetSelection())

    def bind_keys(self):
        bind_keys_to_evt_menu(self._tree, self._get_bind_keys())

    def _get_bind_keys(self):
        bindings = [
            (ctrl_or_cmd(), wx.WXK_UP, self._tree.on_move_up),
            (ctrl_or_cmd(), wx.WXK_DOWN, self._tree.on_move_down),
            (wx.ACCEL_NORMAL, wx.WXK_F2, self._tree.label_editor.on_label_edit),
            (wx.ACCEL_NORMAL, wx.WXK_WINDOWS_MENU, self._tree.on_right_click),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('d'), lambda event: self._expanded_handler().on_safe_delete(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('f'),
                lambda event: self._expanded_handler().on_new_suite(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('k'),
                lambda event: self._expanded_handler().on_new_user_keyword(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('t'),
                lambda event: self._expanded_handler().on_new_test_case(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('v'),
                lambda event: self._expanded_handler().on_new_scalar(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('l'),
                lambda event: self._expanded_handler().on_new_list_variable(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('c'),
                lambda event: self._expanded_handler().on_copy(event))
        ]
        if not IS_WINDOWS:
            bindings.append((wx.ACCEL_NORMAL, wx.WXK_LEFT, self._tree.on_left_arrow))
        return bindings

    def _expanded_handler(self):
        handler = self.get_handler()
        if not self._tree.IsExpanded(handler.node):
            self._tree.Expand(handler.node)
        return handler


class _History(object):

    def __init__(self):
        self._back = []
        self._forward = []

    def change(self, state):
        if not self._back or state != self._back[-1]:
            self._back.append(state)
            self._forward = []

    def back(self):
        if not self._back:
            return None
        if len(self._back) > 1:
            self._forward.append(self._back.pop())
        return self._back[-1]

    def forward(self):
        if not self._forward:
            return None
        state = self._forward.pop()
        self._back.append(state)
        return state

    def top(self):
        return self._back and self._back[-1] or None

    def clear(self):
        self._back.clear()
        self._forward.clear()


class TestSelectionController(object):
    __test__ = False

    def __init__(self):
        self._tests: {TestCaseController} = set()

    def is_empty(self):
        return not bool(self._tests)

    def is_test_selected(self, test):
        return test in self._tests

    def clear_all(self, message):
        _ = message
        self._tests = set()
        self._send_selection_changed_message()

    def unselect_all(self, tests):
        self.select_all(tests, selected=False)

    def select_all(self, tests, selected=True):
        for test in tests:
            self.select(test, selected, notify_selection=False)
        self._send_selection_changed_message()

    def select(self, test: TestCaseController, do_select=True, notify_selection=True):
        changed = False
        if do_select and not self.is_test_selected(test):
            self._tests.add(test)
            changed = True
        elif not do_select and self.is_test_selected(test):
            self._tests.remove(test)
            changed = True
        if notify_selection and changed:
            self._send_selection_changed_message()

    def remove_invalid_cases_selection(self, cases_file_controller):
        from .. import ResourceFileController
        invalid_cases = list()
        to_select_cases = list()
        for test in self._tests:
            if test.datafile_controller == cases_file_controller:
                if not isinstance(cases_file_controller, ResourceFileController):
                    for newobj in cases_file_controller.tests:
                        if test.longname == newobj.longname:
                            to_select_cases.append(newobj)
                invalid_cases.append(test)
        for _ in invalid_cases:
            self._tests.remove(_)
        for test in to_select_cases:
            self.select(test, True, False)
        self._send_selection_changed_message()

    def _send_selection_changed_message(self):
        message = RideTestSelectedForRunningChanged(tests=self._tests)
        wx.CallAfter(message.publish)

    def add_tag(self, name):
        for test in self._tests:
            self._add_tag_to_test(name, test)

    def _add_tag_to_test(self, name, test):
        if name not in [t.name for t in test.tags]:
            self._move_default_tags_to_test(test)
            self._add_tag(test, name)

    def _move_default_tags_to_test(self, test):
        for tag in test.tags:
            if isinstance(tag, DefaultTag):
                self._add_tag(test, tag.name)

    @staticmethod
    def _add_tag(test, name):
        test.tags.execute(ctrlcommands.ChangeTag(Tag(None), name))
