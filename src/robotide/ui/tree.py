#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

from filedialogs import AddSuiteDialog, ChangeFormatDialog
from images import TreeImageList
from robotide import utils
from robotide.action import ActionInfoCollection
from robotide.controller import NewDatafile
from robotide.editor.editordialogs import (TestCaseNameDialog,
                                           UserKeywordNameDialog,
    ScalarVariableDialog, ListVariableDialog, CopyUserKeywordDialog)
from robotide.publish import RideTreeSelection, PUBLISHER
from robotide.context import ctrl_or_cmd, IS_WINDOWS, bind_keys_to_evt_menu
from robotide.publish.messages import RideItem, RideUserKeywordAdded,\
    RideTestCaseAdded, RideUserKeywordRemoved, RideTestCaseRemoved, RideDataFileRemoved,\
    RideDataChangedToDirty, RideDataDirtyCleared, RideVariableRemoved,\
    RideVariableAdded, RideVariableMovedUp, RideVariableMovedDown, RideVariableUpdated, \
    RideOpenResource, RideSuiteAdded, RideSelectResource
from robotide.controller.commands import RenameKeywordOccurrences, RemoveMacro,\
    AddKeyword, AddTestCase, RenameTest, CopyMacroAs, MoveTo,\
    AddVariable, AddSuite, UpdateVariableName
from robotide.widgets import PopupCreator, PopupMenuItems
from robotide.ui.filedialogs import NewResourceDialog
from robotide.usages.UsageRunner import Usages
from robotide.ui.progress import RenameProgressObserver

try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin


tree_actions ="""
[Navigate]
!Go &Back | Go back to previous location in tree | Alt-%s | ART_GO_BACK
!Go &Forward | Go forward to next location in tree | Alt-%s | ART_GO_FORWARD
""" % (('Left', 'Right') if IS_WINDOWS else ('Z', 'X'))
# Left and right cannot be overridden in tree on non Windows OSses, issue 354


class Tree(treemixin.DragAndDrop, wx.TreeCtrl, utils.RideEventHandler):

    def __init__(self, parent, action_registerer):
        style = wx.TR_DEFAULT_STYLE
        if IS_WINDOWS:
            style = style|wx.TR_EDIT_LABELS
        treemixin.DragAndDrop.__init__(self, parent, style=style)
        actions = ActionInfoCollection(tree_actions, self, self)
        action_registerer.register_actions(actions)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnTreeItemExpanding)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self._images = TreeImageList()
        self.SetImageList(self._images)
        self._history = _History()
        self._label_editor = LabelEditor(self)
        self._bind_keys()
        self._subscribe_to_messages()
        self._popup_creator = PopupCreator()
        self._dragging = False
        self._clear_tree_data()
        self._editor = None

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
        for listener, topic in [ (self._item_changed, RideItem),
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
                                 (self._data_dirty, RideDataChangedToDirty),
                                 (self._data_undirty, RideDataDirtyCleared),
                                 (self._variable_moved_up, RideVariableMovedUp),
                                 (self._variable_moved_down, RideVariableMovedDown),
                                 (self._variable_updated, RideVariableUpdated) ]:
            PUBLISHER.subscribe(listener, topic)

    def _bind_keys(self):
        bind_keys_to_evt_menu(self, self._get_bind_keys())

    def _get_bind_keys(self):
        bindings = [(ctrl_or_cmd(), wx.WXK_UP, self.OnMoveUp),
                    (ctrl_or_cmd(), wx.WXK_DOWN, self.OnMoveDown),
                    (wx.ACCEL_NORMAL, wx.WXK_F2, self._label_editor.OnLabelEdit),
                    (wx.ACCEL_NORMAL, wx.WXK_WINDOWS_MENU, self.OnRightClick)]
        if not IS_WINDOWS:
            bindings.append((wx.ACCEL_NORMAL, wx.WXK_LEFT, self.OnLeftArrow))
        return bindings

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
        return self._create_node(self._root, 'Resources',
                                 self._images['TestDataDirectory'])

    def _populate_model(self, model):
        self.SetPyData(self._resource_root, ResourceRootHandler(model, self, self._resource_root))
        if model.data:
            self._render_datafile(self._root, model.data, 0)
        for res in model.resources:
            self._render_datafile(self._resource_root, res)

    def _resource_added(self, message):
        ctrl = message.datafile
        if self._find_node_by_controller(ctrl):
            return
        self._render_datafile(self._resource_root, ctrl)

    def _select_resource(self, message):
        node = self._find_node_by_controller(message.item)
        self.SelectItem(node)

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
        self._datafile_nodes.append(node)
        self.SetItemHasChildren(node, True)
        for child in controller.children:
            self._render_datafile(node, child, None)
        return node

    def _create_node_with_handler(self, parent_node, controller, index=None):
        name = controller.data.__class__.__name__
        node = self._create_node(parent_node, controller.display_name, self._images[name],
                                 index)
        handler_class = globals()[name + 'Handler']
        self.SetPyData(node, handler_class(controller, self, node))
        return node

    def _expand_and_render_children(self, node):
        self._render_children(node)
        self.Expand(node)

    def _render_children(self, node):
        handler = self._get_handler(node)
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

    def _create_node(self, parent_node, label, img, index=None):
        if index is not None:
            # blame wxPython for this ugliness
            if isinstance(index, int):
                node = self.InsertItemBefore(parent_node, index, label)
            else:
                node = self.InsertItem(parent_node, index, label)
        else:
            node = self.AppendItem(parent_node, label)
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
        self._mark_dirty(parent_node)

    def _get_or_create_node(self, parent_node, dataitem, predicate):
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
            return self._get_node_with_label(parent_node, dataitem.display_name)
        index = self._get_insertion_index(parent_node, predicate)
        return self._create_node_with_handler(parent_node, dataitem, index)

    def _select(self, node):
        wx.CallAfter(self.SelectItem, node)

    def _get_insertion_index(self, parent_node, predicate):
        if not predicate:
            return None
        item, cookie = self.GetFirstChild(parent_node)
        while item:
            if predicate(self._get_handler(item)):
                index = self.GetPrevSibling(item)
                if not index.IsOk:
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
        node = self._find_node_by_controller(message.item)
        self.delete_node(node)

    def _test_added(self, message):
        self.add_test(self._get_datafile_node(self.get_selected_datafile()),
                      message.item)

    def _datafile_removed(self, message):
        dfnode = self._get_datafile_node(message.datafile.data)
        self._datafile_nodes.remove(dfnode)
        self.DeleteChildren(dfnode)
        self.Delete(dfnode)

    def add_keyword_controller(self, controller):
        parent = self._get_datafile_node(self.get_selected_datafile())
        self.add_keyword(parent, controller)

    def delete_node(self, node):
        if node is None:
            return
        parent = self.GetItemParent(node)
        self._mark_dirty(parent)
        if self.IsSelected(node):
            wx.CallAfter(self.SelectItem, parent)
        wx.CallAfter(self.Delete, node)

    def _data_dirty(self, message):
        self.mark_dirty(message.datafile)

    def _data_undirty(self, message):
        self.unset_dirty()

    def mark_dirty(self, controller):
        if controller.dirty:
            self._mark_dirty(self._get_datafile_node(controller.datafile))

    def _mark_dirty(self, node):
        text = self.GetItemText(node)
        if not text.startswith('*'):
            self.SetItemText(node, '*' + text)

    def unset_dirty(self):
        for node in self._datafile_nodes:
            text = self.GetItemText(node)
            handler = self._get_handler(node)
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
        node = self._find_node_by_controller(controller)
        if node != self.GetSelection():
            self.SelectItem(node)
        return node

    def select_user_keyword_node(self, uk):
        parent_node = self._get_datafile_node(uk.parent.parent)
        if not parent_node:
            return
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
        node = self._get_node_with_label(parent_node, utils.normalize(uk.name))
        if node != self.GetSelection():
            self.SelectItem(node)

    def _get_datafile_node(self, datafile):
        for node in self._datafile_nodes:
            if self._get_handler(node).item == datafile:
                return node
        return None

    def _get_node_with_label(self, node, label):
        return self._find_node_with_predicate(node,
                                              lambda n: utils.eq(self.GetItemText(n), label))

    def _find_node_with_predicate(self, node, predicate):
        if node != self._root and predicate(node):
            return node
        item, cookie = self.GetFirstChild(node)
        while item:
            if predicate(item):
                return item
            if self.ItemHasChildren(item):
                result = self._find_node_with_predicate(item, predicate)
                if result:
                    return result
            item, cookie = self.GetNextChild(node, cookie)
        return None

    def _find_node_by_controller(self, controller):
        def match_handler(n):
            handler = self._get_handler(n)
            if not handler : return False
            return controller == handler.controller
        return self._find_node_with_predicate(self._root, match_handler)

    def get_selected_datafile(self):
        """Returns currently selected data file.

        If a test or user keyword node is selected, returns parent of that item.
        """
        datafile = self._get_selected_datafile_node()
        if not datafile:
            return None
        return self._get_handler(datafile).item

    def get_selected_datafile_controller(self):
        """Returns controller associated with currently active data file.

        If a test or user keyword node is selected, returns parent of that item.
        """
        dfnode = self._get_selected_datafile_node()
        return self._get_handler(dfnode).controller if dfnode else None

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
        handler = self._get_handler(selection)
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
        controller = self._get_handler(first).controller
        self.Delete(first)
        self._create_node_with_handler(self.GetItemParent(second),
                                              controller, second)
        self.select_node_by_data(selection)

    def _refresh_datafile(self, controller):
        orig_node = self._get_data_controller_node(controller)
        insertion_index = self._get_datafile_index(orig_node)
        parent = self._get_parent(orig_node)
        self._remove_datafile_node(orig_node)
        return self._render_datafile(parent, controller, insertion_index)

    def refresh_datafile(self, controller, event):
        to_be_selected = self._get_pending_selection(event)
        new_node = self._refresh_datafile(controller)
        self._handle_pending_selection(to_be_selected, new_node)

    def _get_pending_selection(self, event):
        if hasattr(event, 'Item'):
            item= event.Item
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
        if not insertion_index.IsOk():
            insertion_index = 0
        return insertion_index

    def _get_parent(self, node):
        return self.GetItemParent(node)

    def _get_handler(self, node=None):
        return self.GetItemPyData(node or self.Selection)

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
                         self._get_node_with_label(parent_node, to_be_selected))

    def OnGoBack(self, event):
        node = self._history.back()
        if node:
            self.SelectItem(node)

    def OnGoForward(self, event):
        node = self._history.forward()
        if node:
            self.SelectItem(node)

    def OnSelChanged(self, event):
        node = event.Item
        if not node.IsOk() or self._dragging:
            event.Skip()
            return
        self._history.change(node)
        handler = self._get_handler(node)
        if handler and handler.item:
            RideTreeSelection(node=node, item=handler.controller,
                              text=self.GetItemText(node)).publish()
        self.SetFocus()

    def OnTreeItemExpanding(self, event):
        node = event.Item
        if node.IsOk():
            self._render_children(node)

    def OnItemActivated(self, event):
        node = event.Item
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
        handler = self._get_handler(event.Item if hasattr(event, 'Item') else None)
        if handler:
            handler.show_popup()

    def OnNewTestCase(self, event):
        handler = self._get_handler()
        if handler:
            handler.OnNewTestCase(event)

    def OnDrop(self, target, dragged):
        dragged = self._get_handler(dragged)
        target = self._get_handler(target)
        if target and target.accepts_drag(dragged):
            dragged.controller.execute(MoveTo(target.controller))

    def IsValidDragItem(self, item):
        return self._get_handler(item).is_draggable

    def OnMoveUp(self, event):
        handler = self._get_handler()
        if handler.is_draggable:
            handler.OnMoveUp(event)

    def OnMoveDown(self, event):
        handler = self._get_handler()
        if handler.is_draggable:
            handler.OnMoveDown(event)

    def _item_changed(self, data):
        controller = data.item
        node = self._find_node_by_controller(controller)
        if node:
            self.SetItemText(node, data.item.name)
        if controller.dirty:
            self._mark_dirty(self._get_datafile_node(controller.datafile))

    def _variable_moved_up(self, data):
        self._do_action_if_datafile_node_is_expanded(self.move_up, data)

    def _variable_moved_down(self, data):
        self._do_action_if_datafile_node_is_expanded(self.move_down, data)

    def _do_action_if_datafile_node_is_expanded(self, action, data):
        if self.IsExpanded(self._get_datafile_node(data.item.datafile)):
            node = self._find_node_by_controller(data.item)
            action(node)

    def _variable_updated(self, data):
        self._item_changed(data)

    def highlight(self, data, text):
        self.select_node_by_data(data)
        self._editor.highlight(text)


class _ActionHandler(wx.Window):
    is_user_keyword = False
    is_test_suite = False
    is_variable = False

    def __init__(self, controller, tree, node):
        wx.Window.__init__(self, tree)
        self.controller = controller
        item = controller.data
        #self.name = item.name
        self.item = item
        self._tree = tree
        self._node = node
        self._rendered = False
        self.Show(False)
        self._popup_creator = tree._popup_creator

    def show_popup(self):
        self._popup_creator.show(self, PopupMenuItems(self, self._actions),
                                 self.controller)


class TestDataHandler(_ActionHandler):
    accepts_drag = lambda self, dragged: (isinstance(dragged, UserKeywordHandler) or
                                          isinstance(dragged, VariableHandler))

    is_draggable = False
    is_renameable = False
    is_test_suite = True
    _actions = ['Add Suite', 'New User Keyword', 'New Scalar', 'New List Variable', '---', 'Change Format']

    @property
    def tests(self):
        return self.controller.tests

    @property
    def keywords(self):
        return self.controller.keywords

    @property
    def variables(self):
        return self.controller.variables

    def has_been_modified_on_disk(self):
        return self.item.has_been_modified_on_disk()

    def do_drop(self, item):
        self.controller.add_test_or_keyword(item)

    def rename(self, new_name):
        return False

    @property
    def can_be_rendered(self):
        if not self._has_children():
            return False
        return not self._rendered

    def _has_children(self):
        return (self.item.keyword_table or self.item.testcase_table or
                self.item.variable_table)

    def set_rendered(self):
        self._rendered = True

    def OnChangeFormat(self, event):
        format =self.controller.get_format() or 'txt'
        dlg = ChangeFormatDialog(format, self.controller.is_directory_suite())
        if dlg.ShowModal() == wx.ID_OK:
            self._handle_format_change(dlg)
        dlg.Destroy()

    def _handle_format_change(self, dialog):
        if dialog.get_recursive():
            self.controller.save_with_new_format_recursive(dialog.get_format())
        else:
            self.controller.save_with_new_format(dialog.get_format())

    def OnAddSuite(self, event):
        dlg = AddSuiteDialog(self.controller.directory)
        if dlg.ShowModal() == wx.ID_OK:
            data = NewDatafile(dlg.get_path(), dlg.is_dir_type())
            self.controller.execute(AddSuite(data))
        dlg.Destroy()

    def OnNewUserKeyword(self, event):
        dlg = UserKeywordNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(AddKeyword(dlg.get_name(), dlg.get_args()))
        dlg.Destroy()

    def OnNewScalar(self, event):
        self._new_var(ScalarVariableDialog)

    def OnNewListVariable(self, event):
        self._new_var(ListVariableDialog)

    def _new_var(self, dialog_class):
        dlg = dialog_class(self._var_controller)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self.controller.execute(AddVariable(name, value, comment))

    @property
    def _var_controller(self):
        return self.controller.datafile_controller.variables


class TestDataDirectoryHandler(TestDataHandler):
    pass


class ResourceFileHandler(TestDataHandler):
    is_test_suite = False
    _actions = ['New User Keyword', 'New Scalar', 'New List Variable', '---', 'Change Format']


class TestCaseFileHandler(TestDataHandler):
    accepts_drag = lambda *args: True
    _actions = ['New Test Case', 'New User Keyword', 'New Scalar', 'New List Variable', '---', 'Change Format']

    def OnNewTestCase(self, event):
        dlg = TestCaseNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(AddTestCase(dlg.get_name()))
        dlg.Destroy()


class _TestOrUserKeywordHandler(_ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    is_renameable = True
    _actions = ['Copy', 'Move Up\tCtrl-Up', 'Move Down\tCtrl-Down',
                'Rename\tF2', '---', 'Delete']

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self._rename(new_name)

    def OnCopy(self, event):
        dlg = self._copy_name_dialog_class(self.controller, self.item)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(CopyMacroAs(dlg.get_name()))
        dlg.Destroy()

    def OnMoveUp(self, event):
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def OnMoveDown(self, event):
        if self.controller.move_down():
            self._tree.move_down(self._node)

    def OnRename(self, event):
        self._tree.EditLabel(self._node)

    def OnDelete(self, event):
        self.controller.execute(RemoveMacro(self.controller))


class TestCaseHandler(_TestOrUserKeywordHandler):
    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = TestCaseNameDialog

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_test(parent_node, copied)

    def _rename(self, new_name):
        self.controller.execute(RenameTest(new_name))


class UserKeywordHandler(_TestOrUserKeywordHandler):
    is_user_keyword = True
    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = CopyUserKeywordDialog
    _actions = _TestOrUserKeywordHandler._actions + ['Find Usages']

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_keyword(parent_node, copied)

    def _rename(self, new_name):
        self.controller.execute(RenameKeywordOccurrences(self.controller.name,
            new_name, RenameProgressObserver(self.GetParent().GetParent()),
            self.controller.info))

    def OnFindUsages(self, event):
        Usages(self.controller, self._tree.highlight).show()


class VariableHandler(_ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    is_variable = True
    is_renameable = True
    OnMoveUp = OnMoveDown = lambda *args: None
    _actions = ['Rename', 'Delete']

    def OnDelete(self, event):
        self.remove()

    def remove(self):
        self.controller.delete()

    def OnRename(self, event):
        self._tree.EditLabel(self._node)

    def rename(self, new_name):
        self.controller.execute(UpdateVariableName(new_name))


class ResourceRootHandler(_ActionHandler):
    is_renameable = is_draggable = is_user_keyword = is_test_suite = False
    item = None
    rename = lambda self, new_name: False
    accepts_drag = lambda self, dragged: False
    _actions = ['New Resource']

    @property
    def can_be_rendered(self):
        return False

    def OnNewResource(self, event):
        NewResourceDialog(self.controller).doit()


class LabelEditor(object):

    def __init__(self, tree):
        self._tree = tree
        tree.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnLabelEdited)
        tree.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self._editing_label = False

    def OnBeginLabelEdit(self, event):
        #See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        self._editing_label = True

    def OnLabelEdit(self, event):
        handler = self._get_handler()
        if handler and handler.is_renameable:
            self._tree.EditLabel(self._tree.Selection)

    def OnLabelEdited(self, event):
        self._editing_label = False
        handler = self._get_handler(event.Item)
        if event.IsEditCancelled() or \
                not self._is_valid_rename(handler.controller, event.Label):
            event.Veto()
        else:
            handler.rename(event.Label)

    def _is_valid_rename(self, controller, label):
        validation = controller.validate_name(label)
        if validation.error_message:
            self._show_validation_error(validation.error_message)
            return False
        return True

    def OnLeftDown(self, event):
        #See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        if IS_WINDOWS and self._editing_label:
            # This method works only on Windows, luckily the issue 756 exists
            # only on Windows
            self._tree.EndEditLabel(self.Selection, discardChanges=True)
        event.Skip()

    def _get_handler(self, item=None):
        return self._tree._get_handler(item)

    def _show_validation_error(self, err_msg):
        wx.MessageBox(err_msg, 'Validation Error', style=wx.ICON_ERROR)


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
