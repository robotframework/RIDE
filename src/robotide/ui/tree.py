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
from namedialogs import TestCaseNameDialog, UserKeywordNameDialog
from robotide import utils
from robotide.action import ActionInfoCollection
from robotide.controller import UserKeywordController, NewDatafile
from robotide.publish import RideTreeSelection
from robotide.context import ctrl_or_cmd, IS_WINDOWS
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
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnLabelEdited)
        self._images = TreeImageList()
        self.SetImageList(self._images)
        self._history = _History()
        self._bind_keys()

    def _bind_keys(self):
        accelrators = []
        for accel, keycode, handler in self._get_bind_keys():
            if IS_WINDOWS and keycode == wx.WXK_LEFT:
                continue
            id = wx.NewId()
            self.Bind(wx.EVT_MENU, handler, id=id)
            accelrators.append((accel, keycode, id))
        self.SetAcceleratorTable(wx.AcceleratorTable(accelrators))

    def _get_bind_keys(self):
        return [(ctrl_or_cmd(), wx.WXK_UP, self.OnMoveUp),
                (ctrl_or_cmd(), wx.WXK_DOWN, self.OnMoveDown),
                (wx.ACCEL_NORMAL, wx.WXK_F2, self.OnLabelEdit),
                (wx.ACCEL_NORMAL, wx.WXK_LEFT, self.OnLeftArrow)]

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
                                          self._images['TestDataDirectory'])
        self.SetPyData(resource_root, NoneHandler())
        return resource_root

    def _populate_model(self, model):
        if model.data:
            self._render_datafile(self._root, model.data, 0)
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

    def _render_datafile(self, parent_node, controller, index=None):
        node = self._create_node_with_handler(parent_node, controller, index)
        self.SetItemHasChildren(node, True)
        self._datafile_nodes.append(node)
        for child in controller.children:
            self._render_datafile(node, child, None)
        return node

    def _create_node_with_handler(self, parent_node, controller, index=None):
        name = controller.data.__class__.__name__
        node = self._create_node(parent_node, controller.data.name, self._images[name],
                                 index)
        handler_class = globals()[name + 'Handler']
        self.SetPyData(node, handler_class(controller, self, node))
        return node

    def _expand_and_render_children(self, node, predicate=None):
        self._render_children(node, predicate)
        self.Expand(node)

    def _render_children(self, node, predicate=None):
        handler = self._get_handler(node)
        if not handler or handler.children_rendered():
            return
        for test in handler.tests:
            self._create_node_with_handler(node, test)
        for kw in handler.keywords:
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

    def add_datafile(self, parent, suite):
        snode = self._render_datafile(self._get_datafile_node(parent.data), suite)
        self.SelectItem(snode)

    def add_resource(self, controller):
        self._render_datafile(self._resource_root, controller)

    def add_test(self, parent_node, test):
        self._add_dataitem(parent_node, test, lambda item: item.is_user_keyword)

    def add_keyword(self, parent_node, kw):
        self._add_dataitem(parent_node, kw, lambda item: item.is_test_suite)

    def _add_dataitem(self, parent_node, dataitem, predicate):
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
            node = self._get_node_with_label(parent_node, dataitem.name)
        else:
            index = self._get_insertion_index(parent_node, predicate)
            node = self._create_node_with_handler(parent_node, dataitem, index)
        self.SelectItem(node)
        self._mark_dirty(parent_node)

    def _get_insertion_index(self, parent_node, predicate):
        item, cookie = self.GetFirstChild(parent_node)
        while item:
            if predicate(self._get_handler(item)):
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
        return self._get_handler(self._get_selected_datafile_node()).item

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
            self._switch_items(prev, node)

    def move_down(self, node):
        next = self.GetNextSibling(node)
        if next.IsOk():
            self.SelectItem(self._switch_items(node, next))

    def _switch_items(self, first, second):
        """Changes the order of given items, first is expected to be directly above the second"""
        parent = self.GetItemParent(first)
        self._mark_dirty(parent)
        controller = self._get_handler(first).controller
        self.Delete(first)
        node = self._create_node_with_handler(self.GetItemParent(second),
                                              controller, second)
        return node

    def refresh_datafile(self, controller, event):
        to_be_selected = self._get_pending_selection(event)
        orig_node = self._get_data_controller_node(controller)
        insertion_index = self._get_datafile_index(orig_node)
        parent = self._get_parent(orig_node)
        self._remove_datafile_node(orig_node)
        new_node = self._render_datafile(parent, controller, insertion_index)
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
        handler = self._get_handler(node)
        if handler and handler.item:
            RideTreeSelection(node=node, item=handler.item,
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

    def OnLabelEdit(self, event):
        handler = self._get_handler()
        if handler and handler.is_renameable:
            self.EditLabel(self.Selection)

    def OnLabelEdited(self, event):
        handler = self._get_handler(event.Item)
        if handler.rename(event.Label):
            self._mark_dirty(self.GetItemParent(event.Item))
        else:
            event.Veto()

    def OnRightClick(self, event):
        handler = self._get_handler(event.Item)
        if handler:
            handler.show_popup()

    def OnDrop(self, target, dragged):
        dragged = self._get_handler(dragged)
        target = self._get_handler(target)
        if target and target.accepts_drag(dragged):
            dragged.remove()
            target.do_drop(dragged.controller)

    def do_drop(self, datafilehandler, test_or_uk):
        for node in self._datafile_nodes:
            if self._get_handler(node) == datafilehandler:
                self._mark_dirty(node)
                if isinstance(test_or_uk, UserKeywordController):
                    self.add_keyword(node, test_or_uk)
                else:
                    self.add_test(node, test_or_uk)

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


class _ActionHandler(wx.Window):
    is_user_keyword = False
    is_test_suite = False

    def __init__(self, controller, tree, node):
        wx.Window.__init__(self, tree)
        self.controller = controller
        item = controller.data
        self.name = item.name
        self.item = item
        self._tree = tree
        self._node = node
        self._rendered = False
        self._mainframe = wx.GetTopLevelParent(self._tree)
        self.Show(False)

    def show_popup(self):
        utils.PopupMenu(self, self._actions)

    def OnChangeFormat(self, event):
        format =self.controller.get_format() or 'txt'
        dlg = ChangeFormatDialog(self, format,
                                 self.controller.is_directory_suite())
        if dlg.ShowModal() == wx.ID_OK:
            self._handle_format_change(dlg)
        dlg.Destroy()

    def _handle_format_change(self, dialog):
        if dialog.get_recursive():
            self.controller.save_with_new_format_recursive(dialog.get_format())
        else:
            self.controller.save_with_new_format(dialog.get_format())


class TestDataDirectoryHandler(_ActionHandler):
    accepts_drag = lambda self, dragged: isinstance(dragged, UserKeywordHandler)
    is_draggable = False
    is_renameable = False
    is_test_suite = True
    _actions = ['Add Suite', 'New User Keyword', '---', 'Change Format']

    @property
    def tests(self):
        return self.controller.tests

    @property
    def keywords(self):
        return self.controller.keywords

    def has_been_modified_on_disk(self):
        return self.item.has_been_modified_on_disk()

    def do_drop(self, test_or_kw_ctrl):
        self.controller.add_test_or_keyword(test_or_kw_ctrl)
        self._tree.do_drop(self, test_or_kw_ctrl)

    def rename(self, new_name):
        return False

    def children_rendered(self):
        if not (self.item.keyword_table or self.item.testcase_table):
            return True
        elif not self._rendered:
            self._rendered = True
            return False
        return True

    def OnAddSuite(self, event):
        dlg = AddSuiteDialog(self.controller.directory)
        if dlg.ShowModal() == wx.ID_OK:
            data = NewDatafile(dlg.get_path(), dlg.is_dir_type())
            ctrl = self.controller.new_datafile(data)
            self._tree.add_datafile(self.controller, ctrl)
        dlg.Destroy()

    def OnNewUserKeyword(self, event):
        dlg = UserKeywordNameDialog(self._mainframe, self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            kw = self.controller.new_keyword(dlg.get_value())
            self._tree.add_keyword(self._node, kw)
        dlg.Destroy()


class ResourceFileHandler(TestDataDirectoryHandler):
    is_test_suite = False
    _actions = ['New User Keyword', '---', 'Change Format']


class TestCaseFileHandler(TestDataDirectoryHandler):
    accepts_drag = lambda *args: True
    _actions = ['New Test Case', 'New User Keyword', '---', 'Change Format']

    def OnNewTestCase(self, event):
        dlg = TestCaseNameDialog(self._mainframe, self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            test = self.controller.new_test(dlg.get_value())
            self._tree.add_test(self._node, test)
        dlg.Destroy()


class _TestOrUserKeywordHandler(_ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    is_renameable = True
    _actions = ['Copy', 'Move Up\tCtrl-Up', 'Move Down\tCtrl-Down',
                'Rename\tF2', '---', 'Delete']

    def remove(self):
        self._tree.delete_node(self._node)
        self.controller.delete()

    def rename(self, new_name):
        # new_name is empty also when the value is not changed
        if not new_name.strip():
            return False
        msg = self.controller.validate_name(new_name)
        if msg:
            wx.MessageBox(msg, 'Validation Error', style=wx.ICON_ERROR)
            return False
        self.controller.rename(new_name)
        return True

    def OnCopy(self, event):
        dlg = self._dialog_class(self._mainframe, self.controller, self.item)
        if dlg.ShowModal() == wx.ID_OK:
            copied = self.controller.copy(dlg.get_value())
            self._add_copy_to_tree(self._tree.GetItemParent(self._node), copied)
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
        self.controller.delete()
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
    __len__ = lambda self: 0


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
