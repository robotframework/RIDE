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

import wx
import os
from robotide.action.actioninfo import ActionInfoCollection, ActionInfo
from robotide.context import IS_WINDOWS, ctrl_or_cmd, bind_keys_to_evt_menu
from robotide.controller.ctrlcommands import ChangeTag
from robotide.controller.tags import Tag, DefaultTag
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.publish import PUBLISHER, RideTestSelectedForRunningChanged, RideItemNameChanged, RideFileNameChanged, RideNewProject, RideOpenSuite
from robotide.widgets import Dialog
from robotide import utils

tree_actions ="""
[Navigate]
!Go &Back | Go back to previous location in tree | Alt-%s | ART_GO_BACK
!Go &Forward | Go forward to next location in tree | Alt-%s | ART_GO_FORWARD
""" % (('Left', 'Right') if IS_WINDOWS else ('Z', 'X'))
# Left and right cannot be overridden in tree on non Windows OSses, issue 354


class TreeController(object):

    def __init__(self, tree, action_registerer, settings, test_selection, history=None):
        self._tree = tree
        self._action_registerer = action_registerer
        self.settings = settings
        self._history = history or _History()
        self._test_selection = test_selection

    def register_tree_actions(self):
        actions = ActionInfoCollection(tree_actions, self, self._tree)
        self._action_registerer.register_actions(actions)
        self._action_registerer.register_action(ActionInfo(menu_name='Edit', name='Add Tag to selected', action=self.OnAddTagToSelected))
        self._action_registerer.register_action(ActionInfo(menu_name='Edit', name='Clear Selected', action=self.OnClearSelected))

    def OnGoBack(self, event):
        node = self._history.back()
        if node:
            self._tree.SelectItem(node)

    def OnAddTagToSelected(self, event):
        if self._test_selection.is_empty():
            return
        name = wx.GetTextFromUser(message='Enter Tag Name', caption='Add Tag To Selected')
        if name:
            self._test_selection.add_tag(name)

    def OnClearSelected(self, event):
        self._tree.DeselectAllTests(self._tree._root)

    def OnGoForward(self, event):
        node = self._history.forward()
        if node:
            self._tree.SelectItem(node)

    def add_to_history(self, node):
        self._history.change(node)

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
        return self._find_node_with_predicate(self._tree._root, match_handler)

    def find_node_with_label(self, node, label):
        matcher = lambda n: utils.eq(self._tree.GetItemText(n), label)
        return self._find_node_with_predicate(node, matcher)

    def _find_node_with_predicate(self, node, predicate):
        if node != self._tree._root and predicate(node):
            return node
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
        return self._tree.GetItemPyData(node or self._tree.GetSelection())

    def bind_keys(self):
        bind_keys_to_evt_menu(self._tree, self._get_bind_keys())

    def _get_bind_keys(self):
        bindings = [
            (ctrl_or_cmd(), wx.WXK_UP, self._tree.OnMoveUp),
            (ctrl_or_cmd(), wx.WXK_DOWN, self._tree.OnMoveDown),
            (wx.ACCEL_NORMAL, wx.WXK_F2, self._tree.label_editor.OnLabelEdit),
            (wx.ACCEL_NORMAL, wx.WXK_WINDOWS_MENU, self._tree.OnRightClick),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('d'), lambda event: self._expanded_handler().OnSafeDelete(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('f'),
                lambda event: self._expanded_handler().OnNewSuite(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('k'),
                lambda event: self._expanded_handler().OnNewUserKeyword(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('t'),
                lambda event: self._expanded_handler().OnNewTestCase(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('v'),
                lambda event: self._expanded_handler().OnNewScalar(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('l'),
                lambda event: self._expanded_handler().OnNewListVariable(event)),
            (ctrl_or_cmd() | wx.ACCEL_SHIFT, ord('c'),
                lambda event: self._expanded_handler().OnCopy(event))
        ]
        if not IS_WINDOWS:
            bindings.append((wx.ACCEL_NORMAL, wx.WXK_LEFT, self._tree.OnLeftArrow))
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


class TestSelectionController(object):

    def __init__(self):
        self._tests = {}
        self._subscribe()

    def _subscribe(self):
        PUBLISHER.subscribe(self._test_name_changed, RideItemNameChanged)
        PUBLISHER.subscribe(self._suite_name_changed, RideFileNameChanged)

    def _test_name_changed(self, message):
        longname = message.item.longname
        path, new_name = longname.rsplit('.', 1)
        if message.old_name:
            old_name = path + '.' + message.old_name
            self._tests[longname] = new_name
            del self._tests[old_name]

    def _suite_name_changed(self, message):
        df = message.datafile
        if isinstance(df, TestCaseFileController):
            filename = os.path.splitext(os.path.basename(message.old_filename))[0]
            old_name = df.longname[:-len(df.name)] + filename
            for test in self._tests:
                if test.lower().startswith(old_name.lower()):
                    del self._tests[test]

    def is_empty(self):
        return not bool(self._tests)

    def is_test_selected(self, test):
        return test.longname in self._tests.keys()

    def clear_all(self, message=None):
        self._tests = {}
        self.send_selection_changed_message()

    def unselect_all(self, tests):
        for test in tests:
            self.select(test, False)

    def select(self, test, selected=True):
        if selected:
            self._tests[test.longname] = test
        elif self.is_test_selected(test):
            del self._tests[test.longname]
        self.send_selection_changed_message()

    def send_selection_changed_message(self):
        RideTestSelectedForRunningChanged(tests=set([(t.datafile_controller.longname, t.longname)
                                                     for t in self._tests.values()])).publish()

    def add_tag(self, name):
        for test in self._tests.values():
            self._add_tag_to_test(name, test)

    def _add_tag_to_test(self, name, test):
        if name not in [t.name for t in test.tags]:
            self._move_default_tags_to_test(test)
            self._add_tag(test, name)

    def _move_default_tags_to_test(self, test):
        for tag in test.tags:
            if isinstance(tag, DefaultTag):
                self._add_tag(test, tag.name)

    def _add_tag(self, test, name):
        test.tags.execute(ChangeTag(Tag(None), name))
