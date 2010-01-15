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
try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin

from robotide.action import ActionInfoCollection
from robotide.model.tcuk import UserKeyword
from robotide.publish import RideTreeSelection
from robotide import utils

from images import TreeImageList
from filedialogs import AddSuiteDialog, ChangeFormatDialog
from namedialogs import TestCaseNameDialog, UserKeywordNameDialog


tree_actions ="""
[Navigate]
!Go &Back | Go back to previous location in tree | Alt-Left | ART_GO_BACK
!Go &Forward | Go forward to next location in tree | Alt-Right | ART_GO_FORWARD
"""


class Tree(treemixin.DragAndDrop, wx.TreeCtrl, utils.RideEventHandler):

    def __init__(self, parent, action_registerer):
        style = wx.TR_DEFAULT_STYLE
        if utils.is_windows:
            style = style|wx.TR_EDIT_LABELS
        treemixin.DragAndDrop.__init__(self, parent, style=style)
        actions = ActionInfoCollection(tree_actions, self, self)
        action_registerer.register_actions(actions)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnLabelEdited)
        self._images = TreeImageList()
        self.SetImageList(self._images)
        self._history = _History()
        self._bind_keys()

    def _bind_keys(self):
        accelrators = []
        for keycode, handler in [(wx.WXK_F2, self.OnLabelEdit),
                                 (wx.WXK_LEFT, self.OnLeftArrow)]:
            if utils.is_windows and keycode == wx.WXK_LEFT:
                continue
            id = wx.NewId()
            self.Bind(wx.EVT_MENU, handler, id=id)
            accelrators.append((wx.ACCEL_NORMAL, keycode, id))
        self.SetAcceleratorTable(wx.AcceleratorTable(accelrators))

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
        resource_root = self._create_node(self._root, 'Resources',
                                          self._images['InitFile'])
        self.SetPyData(resource_root, NoneHandler())
        return resource_root

    def _populate_model(self, model):
        if model.suite:
            self._render_datafile(self._root, model.suite, 0)
        for res in model.resources:
            self._render_datafile(self._resource_root, res)

    def _refresh_view(self):
        self.Refresh()
        if self._resource_root:
            self.Expand(self._resource_root)
        if self._datafile_nodes:
            self.SelectItem(self._datafile_nodes[0])
            self._expand_and_render_children(self._datafile_nodes[0],
                                             lambda item: item.is_test_suite)

    def _render_datafile(self, parent_node, datafile, index=None):
        node = self._create_node_with_handler(parent_node, datafile, index)
        self.SetItemHasChildren(node, True)
        self._datafile_nodes.append(node)
        for suite in datafile.suites:
            self._render_datafile(node, suite, None)
        return node

    def _expand_and_render_children(self, node, predicate=None):
        self._render_children(node, predicate)
        self.Expand(node)

    def _render_children(self, node, predicate):
        if self.GetChildrenCount(node) > 0:
            return
        item = self.GetItemPyData(node).item
        for test in item.tests:
            self._create_node_with_handler(node, test)
        for kw in item.keywords:
            if predicate:
                index = self._get_insertion_index(node, predicate)
            else:
                index = None
            self._create_node_with_handler(node, kw, index)

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

    def _create_node_with_handler(self, parent_node, dataitem, index=None):
        name = dataitem.__class__.__name__
        node = self._create_node(parent_node, dataitem.name, self._images[name],
                                 index)
        handler_class = globals()[name + 'Handler']
        self.SetPyData(node, handler_class(dataitem, self, node))
        return node

    def add_suite(self, parent, suite):
        snode = self._render_datafile(self._get_datafile_node(parent), suite)
        self.SelectItem(snode)

    def add_resource(self, resource):
        self._render_datafile(self._resource_root, resource)

    def add_test(self, parent_node, test):
        self._add_dataitem(parent_node, test, lambda item: item.is_user_keyword)

    def add_keyword(self, parent_node, kw):
        self._add_dataitem(parent_node, kw, lambda item: item.is_test_suite)

    def _add_dataitem(self, parent_node, dataitem, predicate):
        index = self._get_insertion_index(parent_node, predicate)
        node = self._create_node_with_handler(parent_node, dataitem, index)
        self.SelectItem(node)
        self._mark_dirty(parent_node)

    def _get_insertion_index(self, parent_node, predicate):
        item, cookie = self.GetFirstChild(parent_node)
        while item:
            if predicate(self.GetItemPyData(item)):
                index = self.GetPrevSibling(item)
                if not index.IsOk:
                    index = 0
                return index
            item, cookie = self.GetNextChild(parent_node, cookie)
        return None

    def delete_node(self, node):
        parent = self.GetItemParent(node)
        self._mark_dirty(parent)
        self.Delete(node)

    def mark_dirty(self, datafile):
        self._mark_dirty(self._get_datafile_node(datafile))

    def _mark_dirty(self, node):
        text = self.GetItemText(node)
        if not text.startswith('*'):
            self.SetItemText(node, '*' + text)

    def unset_dirty(self):
        for node in self._datafile_nodes:
            text = self.GetItemText(node)
            item = self.GetItemPyData(node).item
            if text.startswith('*') and not item.dirty:
                self.SetItemText(node, text[1:])

    def select_user_keyword_node(self, uk):
        parent_node = self._get_datafile_node(uk.datafile)
        if not parent_node:
            return
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
        node = self._get_node_with_label(parent_node, utils.normalize(uk.name))
        if node != self.GetSelection():
            self.SelectItem(node)

    def _get_datafile_node(self, datafile):
        for node in self._datafile_nodes:
            if self.GetItemPyData(node).item == datafile:
                return node
        return None

    def _get_node_with_label(self, node, label):
        if node != self._root and utils.eq(self.GetItemText(node), label):
            return node
        item, cookie = self.GetFirstChild(node)
        while item:
            if utils.eq(self.GetItemText(item), label):
                return item
            if self.ItemHasChildren(item):
                result = self._get_node_with_label(item, label)
                if result:
                    return result
            item, cookie = self.GetNextChild(node, cookie)
        return None

    def get_selected_datafile(self):
        """Returns currently selected data file.

        If a test or user keyword node is selected, returns parent of that item.
        """
        node = self.GetSelection()
        if not node or node in (self._resource_root, self._root):
            return None
        while node not in self._datafile_nodes:
            node = self.GetItemParent(node)
        return self.GetItemPyData(node).item

    def get_selected_item(self):
        """Returns model object associated with currently selected tree node."""
        selection = self.GetSelection()
        if not selection:
            return None
        data = self.GetItemPyData(selection)
        return data and data.item or None

    def move_up(self, node):
        prev = self.GetPrevSibling(node)
        if prev.IsOk():
            self._switch_items(prev, node)

    def move_down(self, node):
        next = self.GetNextSibling(node)
        if next.IsOk():
            self.SelectItem(self._switch_items(node, next))

    def _switch_items(self, first, second):
        """Changes the order of given items, first is expected to be directly above the second"""
        parent = self.GetItemParent(first)
        self._mark_dirty(parent)
        dataitem = self.GetItemPyData(first).item
        self.Delete(first)
        node = self._create_node_with_handler(self.GetItemParent(second),
                                              dataitem, second)
        return node

    def refresh_datafile(self, datafile, event):
        to_be_selected = self._get_pending_selection(event)
        orig_node = self._get_datafile_node(datafile)
        insertion_index = self._get_datafile_index(orig_node)
        parent = self._get_parent(orig_node)
        self._remove_datafile_node(orig_node)
        new_node = self._render_datafile(parent, datafile, insertion_index)
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

    def _click_on_item(self, flags):
        return flags & wx.TREE_HITTEST_ONITEM

    def _get_datafile_index(self, node):
        insertion_index = self.GetPrevSibling(node)
        if not insertion_index.IsOk():
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
            self.SelectItem(self._get_node_with_label(parent_node, to_be_selected))

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
        if not node.IsOk():
            event.Skip()
            return
        self._history.change(node)
        handler = self.GetItemPyData(node)
        if handler and handler.item:
            RideTreeSelection(node=node, item=handler.item,
                              text=self.GetItemText(node)).publish()
        self.SetFocus()

    def OnItemExpanded(self, event):
        node = event.Item
        if node.IsOk() and self.ItemHasChildren(node):
            self._expand_and_render_children(node)

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

    def OnLabelEdit(self, event):
        selection = self.GetSelection()
        item = self.GetItemPyData(selection)
        if item and item.is_renameable:
            self.EditLabel(selection)

    def OnLabelEdited(self, event):
        handler = self.GetItemPyData(event.Item)
        if handler.rename(event.Label):
            self._mark_dirty(self.GetItemParent(event.Item))
        else:
            event.Veto()

    def OnRightClick(self, event):
        handler = self.GetItemPyData(event.GetItem())
        if handler:
            handler.show_popup()

    def OnDrop(self, target, dragged):
        dragged = self.GetItemPyData(dragged)
        target = self.GetItemPyData(target)
        if target and target.accepts_drag(dragged):
            dragged.remove()
            target.do_drop(dragged.item)

    def do_drop(self, datafilehandler, test_or_uk):
        for node in self._datafile_nodes:
            if self.GetItemPyData(node) == datafilehandler:
                self._mark_dirty(node)
                if isinstance(test_or_uk, UserKeyword):
                    self.add_keyword(node, test_or_uk)
                else:
                    self.add_test(node, test_or_uk)

    def IsValidDragItem(self, item):
        return self.GetItemPyData(item).is_draggable


class _ActionHandler(wx.Window):
    is_user_keyword = False
    is_test_suite = False

    def __init__(self, item, tree, node):
        wx.Window.__init__(self, tree)
        self.name = item.name
        self.item = item
        self._tree = tree
        self._node = node
        self.Show(False)

    def show_popup(self):
        utils.PopupMenu(self, self._actions)

    def OnChangeFormat(self, event):
        dlg = ChangeFormatDialog(self, self.item.get_format(),
                                 self.item.is_directory_suite)
        if dlg.ShowModal() == wx.ID_OK:
            self.item.serialize(format=dlg.get_format(),
                                recursive=dlg.get_recursive())
        dlg.Destroy()


class InitFileHandler(_ActionHandler):
    accepts_drag = lambda self, dragged: isinstance(dragged, UserKeywordHandler)
    is_draggable = False
    is_renameable = False
    is_test_suite = True
    _actions = ['Add Suite', 'New User Keyword', '---', 'Change Format']

    def has_been_modified_on_disk(self):
        return self.item.has_been_modified_on_disk()

    def do_drop(self, test_or_kw):
        self.item.add_test_or_user_keyword(test_or_kw)
        self._tree.do_drop(self, test_or_kw)

    def rename(self, new_name):
        return False

    def OnAddSuite(self, event):
        dlg = AddSuiteDialog(self.item.get_dir_path())
        if dlg.ShowModal() == wx.ID_OK:
            subsuite = self.item.add_suite(dlg.get_path())
            self._tree.add_suite(self.item, subsuite)
        dlg.Destroy()

    def OnNewUserKeyword(self, event):
        dlg = UserKeywordNameDialog(self.item)
        if dlg.ShowModal() == wx.ID_OK:
            kw = self.item.new_keyword(dlg.get_value())
            self._tree.add_keyword(self._node, kw)
        dlg.Destroy()


class ResourceFileHandler(InitFileHandler):
    is_test_suite = False
    _actions = ['New User Keyword', '---', 'Change Format']


class TestCaseFileHandler(InitFileHandler):
    accepts_drag = lambda *args: True
    _actions = ['New Test Case', 'New User Keyword', '---', 'Change Format']

    def OnNewTestCase(self, event):
        dlg = TestCaseNameDialog(self.item)
        if dlg.ShowModal() == wx.ID_OK:
            test = self.item.new_test(dlg.get_value())
            self._tree.add_test(self._node, test)
        dlg.Destroy()


class _TestOrUserKeywordHandler(_ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    is_renameable = True
    _actions = ['Copy', 'Move Up', 'Move Down' , 'Rename\tF2', '---', 'Delete']

    def remove(self):
        self._tree.delete_node(self._node)
        self.item.delete()

    def rename(self, new_name):
        # new_name is empty also when the value is not changed
        if not new_name.strip():
            return False
        msg = self._datalist.validate_name(new_name, self.item.name)
        if msg:
            wx.MessageBox(msg, 'Validation Error', style=wx.ICON_ERROR)
            return False
        self.item.rename(new_name)
        return True

    def OnCopy(self, event):
        dlg = self._dialog_class(self.item.datafile, self.item)
        if dlg.ShowModal() == wx.ID_OK:
            copied = self._datalist.copy(self.item, dlg.get_value())
            self._add_copy_to_tree(self._tree.GetItemParent(self._node), copied)
        dlg.Destroy()

    def OnMoveUp(self, event):
        if self._datalist.move_up(self.item):
            self._tree.move_up(self._node)

    def OnMoveDown(self, event):
        if self._datalist.move_down(self.item):
            self._tree.move_down(self._node)

    def OnRename(self, event):
        self._tree.EditLabel(self._node)

    def OnDelete(self, event):
        self.item.delete()
        self._tree.delete_node(self._node)


class TestCaseHandler(_TestOrUserKeywordHandler):
    _datalist = property(lambda self: self.item.datalist)
    _dialog_class = TestCaseNameDialog

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_test(parent_node, copied)


class UserKeywordHandler(_TestOrUserKeywordHandler):
    is_user_keyword = True
    _datalist = property(lambda self: self.item.datalist)
    _dialog_class = UserKeywordNameDialog

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_keyword(parent_node, copied)


class NoneHandler(object):
    """Null object (pattern)"""
    is_renameable = is_draggable = is_user_keyword = is_test_suite = False
    item = None
    show_popup = lambda self: None
    rename = lambda self, new_name: False
    accepts_drag = lambda self, dragged: False


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
