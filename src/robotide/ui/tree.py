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

import wx
from robotide.publish.messages import RideTestRunning, RideTestPassed, RideTestFailed, RideTestExecutionStarted
from robotide.ui.images import RUNNING_IMAGE_INDEX, PASSED_IMAGE_INDEX, FAILED_IMAGE_INDEX, ROBOT_IMAGE_INDEX

tree_args = {}
try:
    import wx.lib.agw.customtreectrl as customtreectrl
    if wx.VERSION_STRING >= '2.8.11.0':
        tree_args['agwStyle']=customtreectrl.TR_DEFAULT_STYLE | customtreectrl.TR_HIDE_ROOT | customtreectrl.TR_EDIT_LABELS
except ImportError:
    import wx.lib.customtreectrl as customtreectrl
from robotide.controller.ui.treecontroller import TreeController

try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin

from robotide.context import ctrl_or_cmd, IS_WINDOWS, bind_keys_to_evt_menu
from robotide.publish import (PUBLISHER, RideTreeSelection, RideFileNameChanged,
    RideTestSelectedForRunningChanged, RideItem, RideUserKeywordAdded, RideTestCaseAdded,
    RideUserKeywordRemoved, RideTestCaseRemoved, RideDataFileRemoved, RideDataChangedToDirty,
    RideDataDirtyCleared, RideVariableRemoved, RideVariableAdded,
    RideVariableMovedUp, RideVariableMovedDown, RideVariableUpdated,
    RideOpenResource, RideSuiteAdded, RideSelectResource, RideDataFileSet)
from robotide.controller.commands import MoveTo
from robotide.widgets import PopupCreator
from robotide import utils

from .treenodehandlers import ResourceRootHandler, action_handler_class
from .images import TreeImageList


class Tree(treemixin.DragAndDrop, customtreectrl.CustomTreeCtrl, utils.RideEventHandler):

    _RESOURCES_NODE_LABEL = 'External Resources'

    def __init__(self, parent, action_registerer, settings=None):
        self._controller = TreeController(self, action_registerer, settings=settings)
        tree_args['style'] = wx.TR_DEFAULT_STYLE | (IS_WINDOWS and wx.TR_EDIT_LABELS)
        treemixin.DragAndDrop.__init__(self, parent, **tree_args)
        self._controller.register_tree_actions()
        self._bind_tree_events()
        self._images = TreeImageList()
        self._silent_mode = False
        self.SetImageList(self._images)
        self._label_editor = TreeLabelEditListener(self)
        self._controller.bind_keys()
        self._subscribe_to_messages()
        self._popup_creator = PopupCreator()
        self._dragging = False
        self._clear_tree_data()
        self._editor = None
        self._execution_results = None

    def _bind_tree_events(self):
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnTreeItemExpanding)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(customtreectrl.EVT_TREE_ITEM_CHECKED, self.OnTreeItemChecked)

    def set_editor(self, editor):
        self._editor = editor

    def StartDragging(self):
        self._dragging = True
        treemixin.DragAndDrop.StartDragging(self)

    def OnEndDrag(self, event):
        self._dragging = False
        treemixin.DragAndDrop.OnEndDrag(self, event)

    def register_context_menu_hook(self, callable):
        self._popup_creator.add_hook(callable)

    def unregister_context_menu_hook(self, callable):
        self._popup_creator.remove_hook(callable)

    def _subscribe_to_messages(self):
        subscriptions = [
            (self._item_changed, RideItem),
            (self._resource_added, RideOpenResource),
            (self._select_resource, RideSelectResource),
            (self._suite_added, RideSuiteAdded),
            (self._keyword_added, RideUserKeywordAdded),
            (self._test_added, RideTestCaseAdded),
            (self._variable_added, RideVariableAdded),
            (self._leaf_item_removed, RideUserKeywordRemoved),
            (self._leaf_item_removed, RideTestCaseRemoved),
            (self._leaf_item_removed, RideVariableRemoved),
            (self._datafile_removed, RideDataFileRemoved),
            (self._datafile_set, RideDataFileSet),
            (self._data_dirty, RideDataChangedToDirty),
            (self._data_undirty, RideDataDirtyCleared),
            (self._variable_moved_up, RideVariableMovedUp),
            (self._variable_moved_down, RideVariableMovedDown),
            (self._variable_updated, RideVariableUpdated),
            (self._filename_changed, RideFileNameChanged),
            (self._testing_started, RideTestExecutionStarted),
            (self._test_result, RideTestRunning),
            (self._test_result, RideTestPassed),
            (self._test_result, RideTestFailed)
        ]
        for listener, topic in subscriptions:
            PUBLISHER.subscribe(listener, topic)

    def _testing_started(self, message):
        self._for_all_drawn_tests(self._root, lambda t: self.SetItemImage(t, ROBOT_IMAGE_INDEX))
        self._execution_results = message.results
        self._images.set_execution_results(message.results)

    def _test_result(self, message):
        self._set_icon_from_execution_results(message.item)

    def _set_icon_from_execution_results(self, controller):
        node = self._controller.find_node_by_controller(controller)
        if not node:
            return
        self.SetItemImage(node, self._get_icon_index_for(controller))

    def _get_icon_index_for(self, controller):
        if not self._execution_results:
            return ROBOT_IMAGE_INDEX
        if self._execution_results.is_running(controller):
            return RUNNING_IMAGE_INDEX
        if self._execution_results.has_passed(controller):
            return PASSED_IMAGE_INDEX
        if self._execution_results.has_failed(controller):
            return FAILED_IMAGE_INDEX
        return ROBOT_IMAGE_INDEX

    def populate(self, model):
        self._clear_tree_data()
        self._populate_model(model)
        self._refresh_view()
        self.SetFocus() # Needed for keyboard shortcuts

    def _clear_tree_data(self):
        self.DeleteAllItems()
        self._root = self.AddRoot('')
        self._resource_root = self._create_resource_root()
        self._datafile_nodes = []

    def _create_resource_root(self):
        return self._create_node(self._root, self._RESOURCES_NODE_LABEL,
                                 self._images.directory)

    def _populate_model(self, model):
        handler = ResourceRootHandler(model, self, self._resource_root,
                                      self._controller.settings)
        self.SetPyData(self._resource_root, handler)
        if model.data:
            self._render_datafile(self._root, model.data, 0)
        for res in model.external_resources:
            if not res.parent:
                self._render_datafile(self._resource_root, res)

    def _resource_added(self, message):
        ctrl = message.datafile
        if self._controller.find_node_by_controller(ctrl):
            return
        parent = self._get_dir_node(ctrl.parent) if ctrl.parent else self._resource_root
        self._render_datafile(parent, ctrl)

    def _get_dir_node(self, ctrl):
        if ctrl is None:
            return self._root
        dir_node = self._get_datafile_node(ctrl.data)
        if dir_node is None:
            parent = self._get_dir_node(ctrl.parent)
            self._render_datafile(parent, ctrl)
            dir_node = self._get_datafile_node(ctrl.data)
        return dir_node

    def _select_resource(self, message):
        self.select_controller_node(message.item)

    def select_controller_node(self, controller):
        self.SelectItem(self._controller.find_node_by_controller(controller))

    def _suite_added(self, message):
        self.add_datafile(message.parent, message.suite)

    def _refresh_view(self):
        self.Refresh()
        if self._resource_root:
            self.Expand(self._resource_root)
        if self._datafile_nodes:
            self.SelectItem(self._datafile_nodes[0])
            self._expand_and_render_children(self._datafile_nodes[0])

    def _render_datafile(self, parent_node, controller, index=None):
        node = self._create_node_with_handler(parent_node, controller, index)
        if controller.dirty:
            self._controller.mark_node_dirty(node)
        self._datafile_nodes.append(node)
        self.SetItemHasChildren(node, True)
        for child in controller.children:
            self._render_datafile(node, child)
        return node

    def _create_node_with_handler(self, parent_node, controller, index=None):
        handler_class = action_handler_class(controller)
        node = self._create_node(parent_node, controller.display_name, self._images[controller],
                                 index, with_checkbox=handler_class.with_checkbox)
        self.SetPyData(node, handler_class(controller, self, node, self._controller.settings))
        return node

    def _expand_and_render_children(self, node):
        assert node is not None
        self._render_children(node)
        self.Expand(node)

    def _render_children(self, node):
        handler = self._controller.get_handler(node)
        if not handler or not handler.can_be_rendered:
            return
        self._create_child_nodes(node, handler, lambda item: item.is_test_suite)
        handler.set_rendered()

    def _create_child_nodes(self, node, handler, predicate):
        for childitem in self._children_of(handler):
            index = self._get_insertion_index(node, predicate)
            self._create_node_with_handler(node, childitem, index)

    def _children_of(self, handler):
        return list(handler.variables) + list(handler.tests) + \
                list(handler.keywords)

    def _create_node(self, parent_node, label, img, index=None, with_checkbox=False):
        ct_type = 1 if with_checkbox else 0
        if index is not None:
            # blame wxPython for this ugliness
            if isinstance(index, int):
                node = self.InsertItemByIndex(parent_node, index, label, ct_type=ct_type)
            else:
                node = self.InsertItem(parent_node, index, label, ct_type=ct_type)
        else:
            node = self.AppendItem(parent_node, label, ct_type=ct_type)
        self.SetItemImage(node, img.normal, wx.TreeItemIcon_Normal)
        self.SetItemImage(node, img.expanded, wx.TreeItemIcon_Expanded)
        return node

    def add_datafile(self, parent, suite):
        snode = self._render_datafile(self._get_datafile_node(parent.data), suite)
        self.SelectItem(snode)

    def add_test(self, parent_node, test):
        self._add_dataitem(parent_node, test, lambda item: item.is_user_keyword)

    def add_keyword(self, parent_node, kw):
        self._add_dataitem(parent_node, kw, lambda item: item.is_test_suite)

    def _add_dataitem(self, parent_node, dataitem, predicate):
        node = self._get_or_create_node(parent_node, dataitem, predicate)
        self._select(node)
        self._controller.mark_node_dirty(parent_node)

    def _get_or_create_node(self, parent_node, dataitem, predicate):
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
            return self._controller.find_node_with_label(parent_node, dataitem.display_name)
        index = self._get_insertion_index(parent_node, predicate)
        return self._create_node_with_handler(parent_node, dataitem, index)

    def _select(self, node):
        if node:
            wx.CallAfter(self.SelectItem, node)

    def _get_insertion_index(self, parent_node, predicate):
        if not predicate:
            return None
        item, cookie = self.GetFirstChild(parent_node)
        while item:
            if predicate(self._controller.get_handler(item)):
                index = self.GetPrevSibling(item)
                if not index:
                    index = 0
                return index
            item, cookie = self.GetNextChild(parent_node, cookie)
        return None

    def _keyword_added(self, message):
        self.add_keyword(self._get_datafile_node(self.get_selected_datafile()),
                         message.item)

    def _variable_added(self, message):
        self._get_or_create_node(self._get_datafile_node(self.get_selected_datafile()),
                           message.item, lambda item: not item.is_variable)

    def _leaf_item_removed(self, message):
        node = self._controller.find_node_by_controller(message.item)
        self.delete_node(node)

    def _test_added(self, message):
        self.add_test(self._get_datafile_node(self.get_selected_datafile()),
                      message.item)

    def _datafile_removed(self, message):
        dfnode = self._get_datafile_node(message.datafile.data)
        self._datafile_nodes.remove(dfnode)
        self.DeleteChildren(dfnode)
        self.Delete(dfnode)

    def _datafile_set(self, message):
        wx.CallAfter(self._refresh_datafile_when_file_set, message.item)

    def _filename_changed(self, message):
        df = message.datafile
        node = self._controller.find_node_by_controller(df)
        if not node:
            raise AssertionError('No node found with controller "%s"' % df)
        wx.CallAfter(self.SetItemText, node, df.display_name)

    def add_keyword_controller(self, controller):
        parent = self._get_datafile_node(self.get_selected_datafile())
        self.add_keyword(parent, controller)

    def delete_node(self, node):
        if node is None:
            return
        parent = self.GetItemParent(node)
        self._controller.mark_node_dirty(parent)
        if self.IsSelected(node):
            wx.CallAfter(self.SelectItem, parent)
        wx.CallAfter(self.Delete, node)

    def _data_dirty(self, message):
        self._controller.mark_controller_dirty(message.datafile)

    def _data_undirty(self, message):
        self.unset_dirty()

    def unset_dirty(self):
        for node in self._datafile_nodes:
            text = self.GetItemText(node)
            handler = self._controller.get_handler(node)
            if text.startswith('*') and not handler.controller.dirty:
                self.SetItemText(node, text[1:])

    def select_node_by_data(self, controller):
        '''Find and select the tree item associated with the given controller.

        Controller can be any of the controllers that are represented in the tree.'''
        parent_node = self._get_datafile_node(controller.datafile)
        if not parent_node:
            return None
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
        node = self._controller.find_node_by_controller(controller)
        if node != self.GetSelection():
            self.SelectItem(node)
        return node

    def select_user_keyword_node(self, uk):
        parent_node = self._get_datafile_node(uk.parent.parent)
        if not parent_node:
            return
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
        node = self._controller.find_node_with_label(parent_node, utils.normalize(uk.name))
        if node != self.GetSelection():
            self.SelectItem(node)

    def _get_datafile_node(self, datafile):
        for node in self._datafile_nodes:
            if self._controller.get_handler(node).item == datafile:
                return node
        return None

    def get_selected_datafile(self):
        """Returns currently selected data file.

        If a test or user keyword node is selected, returns parent of that item.
        """
        datafile = self._get_selected_datafile_node()
        if not datafile:
            return None
        return self._controller.get_handler(datafile).item

    def get_selected_datafile_controller(self):
        """Returns controller associated with currently active data file.

        If a test or user keyword node is selected, returns parent of that item.
        """
        dfnode = self._get_selected_datafile_node()
        return self._controller.get_handler(dfnode).controller if dfnode else None

    def _get_selected_datafile_node(self):
        node = self.GetSelection()
        if not node or node in (self._resource_root, self._root):
            return None
        while node not in self._datafile_nodes:
            node = self.GetItemParent(node)
        return node

    def get_selected_item(self):
        """Returns model object associated with currently selected tree node."""
        selection = self.GetSelection()
        if not selection:
            return None
        handler = self._controller.get_handler(selection)
        return handler and handler.controller or None

    def move_up(self, node):
        prev = self.GetPrevSibling(node)
        if prev.IsOk():
            self._switch_items(prev, node, node)

    def move_down(self, node):
        next = self.GetNextSibling(node)
        if next.IsOk():
            self._switch_items(node, next, node)

    def _switch_items(self, first, second, currently_selected):
        """Changes the order of given items, first is expected to be directly above the second"""
        selection = self.GetItemPyData(currently_selected).controller
        controller = self._controller.get_handler(first).controller
        self.Delete(first)
        self._create_node_with_handler(self.GetItemParent(second),
                                              controller, second)
        self.select_node_by_data(selection)

    def _refresh_datafile_when_file_set(self, controller):
        self._start_silent_mode() #Prevent tab selections based on tree item selected events
        current = self.get_selected_datafile_controller()
        if not current: # If tree is not yet in use - do not expand anything.
            self._end_silent_mode()
            return
        item = self.GetSelection()
        current_txt = self.GetItemText(item) if item.IsOk() else ''
        # after refresh current and current_txt might have been changed
        node = self._refresh_datafile(controller)
        if node is None:
            #TODO: Find out why this sometimes happens
            return
        self._expand_and_render_children(node)
        if current == controller:
            wx.CallAfter(self.SelectItem, self._controller.find_node_with_label(node, current_txt) or node)
            wx.CallAfter(self._end_silent_mode)
        else:
            self._end_silent_mode()

    def _start_silent_mode(self):
        self._silent_mode = True

    def _end_silent_mode(self):
        self._silent_mode = False

    def refresh_datafile(self, controller, event):
        to_be_selected = self._get_pending_selection(event)
        new_node = self._refresh_datafile(controller)
        self._handle_pending_selection(to_be_selected, new_node)

    def _refresh_datafile(self, controller):
        orig_node = self._get_data_controller_node(controller)
        if orig_node is not None:
            insertion_index = self._get_datafile_index(orig_node)
            parent = self._get_parent(orig_node)
            self._remove_datafile_node(orig_node)
            return self._render_datafile(parent, controller, insertion_index)

    def _get_pending_selection(self, event):
        if hasattr(event, 'Item'):
            item = event.GetItem()
            event.Veto()
        elif hasattr(event, 'Position'):
            item, flags = self.HitTest(event.Position)
            if not (item.IsOk() and self._click_on_item(flags)):
                return
        else:
            return
        return self.GetItemText(item)

    def _get_data_controller_node(self, controller):
        for node in self._datafile_nodes:
            if self.GetItemPyData(node).controller == controller:
                return node
        return None

    def _click_on_item(self, flags):
        return flags & wx.TREE_HITTEST_ONITEM

    def _get_datafile_index(self, node):
        insertion_index = self.GetPrevSibling(node)
        if not insertion_index:
            insertion_index = 0
        return insertion_index

    def _get_parent(self, node):
        return self.GetItemParent(node)

    def _remove_datafile_node(self, node):
        for child in self.GetItemChildren(node):
            if child in self._datafile_nodes:
                self._remove_datafile_node(child)
        self._datafile_nodes.remove(node)
        self.Delete(node)

    def _handle_pending_selection(self, to_be_selected, parent_node):
        if to_be_selected:
            self._expand_and_render_children(parent_node)
            wx.CallAfter(self.SelectItem,
                         self._controller.find_node_with_label(parent_node, to_be_selected))


    def OnSelChanged(self, event):
        node = event.GetItem()
        if not node.IsOk() or self._dragging:
            event.Skip()
            return
        self._controller.add_to_history(node)
        handler = self._controller.get_handler(node)
        if handler and handler.item:
            RideTreeSelection(node=node, item=handler.controller, silent=self._silent_mode).publish()
        self.SetFocus()

    def OnTreeItemExpanding(self, event):
        node = event.GetItem()
        if node.IsOk():
            self._render_children(node)

    def SelectAllTests(self, item):
        self._for_all_tests(item, lambda t: self.CheckItem(t))

    def _for_all_tests(self, item, func):
        if not self.HasAGWFlag(customtreectrl.TR_HIDE_ROOT) or item != self.GetRootItem():
            self.Expand(item)
            if self._is_test_node(item):
                func(item)
            if not self.IsExpanded(item):
                return
        for child in item.GetChildren():
            self._for_all_tests(child, func)

    def _for_all_drawn_tests(self, item, func):
        if self._is_test_node(item):
            func(item)
        for child in item.GetChildren():
            self._for_all_drawn_tests(child, func)

    def _is_test_node(self, node):
        return node.GetType() == 1

    def DeselectAllTests(self, item):
        self._for_all_tests(item, lambda t: self.CheckItem(t, checked=False))

    def SelectFailedTests(self, item):
        def func(t):
            # FIXME: This information should be in domain model!
            self.CheckItem(t, checked=(self.GetItemImage(t) == FAILED_IMAGE_INDEX))
        self._for_all_tests(item, func)

    def OnTreeItemChecked(self, event):
        node = event.GetItem()
        handler = self._controller.get_handler(node=node)
        RideTestSelectedForRunningChanged(item=handler.controller, running=node.IsChecked()).publish()

    def OnItemActivated(self, event):
        node = event.GetItem()
        if self.IsExpanded(node):
            self.Collapse(node)
        elif self.ItemHasChildren(node):
            self._expand_and_render_children(node)

    def OnLeftArrow(self, event):
        node = self.GetSelection()
        if self.IsExpanded(node):
            self.Collapse(node)
        else:
            event.Skip()

    def OnRightClick(self, event):
        handler = self._controller.get_handler(event.GetItem() if hasattr(event, 'GetItem') else None)
        if handler:
            if not self.IsExpanded(handler.node):
                self.Expand(handler.node)
            handler.show_popup()

    def OnNewTestCase(self, event):
        handler = self._controller.get_handler()
        if handler:
            handler.OnNewTestCase(event)

    def OnDrop(self, target, dragged):
        dragged = self._controller.get_handler(dragged)
        target = self._controller.get_handler(target)
        if target and target.accepts_drag(dragged):
            dragged.controller.execute(MoveTo(target.controller))
        else:
            self.Refresh()

    def IsValidDragItem(self, item):
        return self._controller.get_handler(item).is_draggable

    def OnMoveUp(self, event):
        handler = self._controller.get_handler()
        if handler.is_draggable:
            handler.OnMoveUp(event)

    def OnMoveDown(self, event):
        handler = self._controller.get_handler()
        if handler.is_draggable:
            handler.OnMoveDown(event)

    def _item_changed(self, data):
        controller = data.item
        node = self._controller.find_node_by_controller(controller)
        if node:
            self.SetItemText(node, data.item.name)
        if controller.dirty:
            self._controller.mark_node_dirty(self._get_datafile_node(controller.datafile))

    def _variable_moved_up(self, data):
        self._do_action_if_datafile_node_is_expanded(self.move_up, data)

    def _variable_moved_down(self, data):
        self._do_action_if_datafile_node_is_expanded(self.move_down, data)

    def _do_action_if_datafile_node_is_expanded(self, action, data):
        if self.IsExpanded(self._get_datafile_node(data.item.datafile)):
            node = self._controller.find_node_by_controller(data.item)
            action(node)

    def _variable_updated(self, data):
        self._item_changed(data)

    def highlight(self, data, text):
        self.select_node_by_data(data)
        self._editor.highlight(text)


class TreeLabelEditListener(object):

    def __init__(self, tree):
        self._tree = tree
        tree.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnLabelEdited)
        tree.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self._editing_label = False
        self._on_label_edit_called = False

    def OnBeginLabelEdit(self, event):
        #See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        self._editing_label = True
        if not self._on_label_edit_called:
            self.OnLabelEdit(None)

    def OnLabelEdit(self, event):
        if not self._on_label_edit_called:
            self._on_label_edit_called = True
            handler = self._tree._controller.get_handler()
            if handler:
                handler.begin_label_edit()

    def OnLabelEdited(self, event):
        self._editing_label = False
        self._on_label_edit_called = False
        self._tree._controller.get_handler(event.GetItem()).end_label_edit(event)

    def OnLeftDown(self, event):
        #See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        if IS_WINDOWS and self._editing_label:
            # This method works only on Windows, luckily the issue 756 exists
            # only on Windows
            self._tree.OnCancelEdit(self._tree.GetSelection())
        event.Skip()

    def _get_handler(self, item=None):
        return self._tree._get_handler(item)
