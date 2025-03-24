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
import os

import wx
from wx import Colour
from wx.lib.agw import customtreectrl
from wx.lib.agw.aui import GetManager
from wx.lib.agw.customtreectrl import GenericTreeItem
from wx.lib.mixins import treemixin

from ..context import IS_WINDOWS
from ..publish.messages import (RideTestRunning, RideTestPaused, RideTestPassed, RideTestFailed, RideTestSkipped,
                                RideTestExecutionStarted, RideTestStopped, RideImportSetting, RideExcludesChanged,
                                RideIncludesChanged, RideOpenSuite, RideNewProject)
from ..ui.images import (RUNNING_IMAGE_INDEX, PASSED_IMAGE_INDEX, FAILED_IMAGE_INDEX, PAUSED_IMAGE_INDEX,
                         SKIPPED_IMAGE_INDEX, ROBOT_IMAGE_INDEX)
from ..ui.treenodehandlers import TestCaseHandler, TestDataDirectoryHandler, TestCaseFileHandler
from ..publish import (PUBLISHER, RideTreeSelection, RideFileNameChanged, RideItem, RideUserKeywordAdded,
                       RideTestCaseAdded, RideUserKeywordRemoved, RideUserKeywordRenamed,  RideTestCaseRemoved,
                       RideDataFileRemoved, RideDataChangedToDirty, RideDataDirtyCleared, RideVariableRemoved,
                       RideVariableAdded, RideVariableMovedUp, RideVariableMovedDown, RideVariableUpdated,
                       RideOpenResource, RideSuiteAdded, RideSelectResource, RideDataFileSet, RideItemNameChanged)
from ..controller.ctrlcommands import MoveTo
from ..pluginapi import Plugin
from ..action import ActionInfo
from ..widgets import PopupCreator
from .. import utils
from .treenodehandlers import ResourceRootHandler, action_handler_class, ResourceFileHandler
from .images import TreeImageList

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


TREETEXTCOLOUR = Colour(0xA9, 0xA9, 0xA9)

_TREE_ARGS = {'style': wx.HSCROLL | wx.VSCROLL,
              'agwStyle': customtreectrl.TR_DEFAULT_STYLE | customtreectrl.TR_HIDE_ROOT | customtreectrl.TR_EDIT_LABELS}
_TREE_ARGS['agwStyle'] |= customtreectrl.TR_TOOLTIP_ON_LONG_ITEMS | customtreectrl.TR_HAS_VARIABLE_ROW_HEIGHT

if IS_WINDOWS:
    _TREE_ARGS['style'] |= wx.TR_EDIT_LABELS


class TreePlugin(Plugin):
    __doc__ = _("""Provides a tree view for Test Suites """)

    datafile = property(lambda self: self.get_selected_datafile())
    defaults = {"opened": True,
                "docked": True,
                "own colors": False
                }

    def __init__(self, application):
        Plugin.__init__(self, application, default_settings=self.defaults)
        # print("DEBUG: treeplugin.py TreePlugin __init__")
        self._app = application
        self.settings = self._app.settings.config_obj['Plugins']['Tree']
        self._parent = None
        self._tree = self.tree
        """
        self._tree.SetBackgroundColour(Colour(200, 222, 40))
        self._tree.SetOwnBackgroundColour(Colour(200, 222, 40))
        self._tree.SetForegroundColour(Colour(7, 0, 70))
        self._tree.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        self._mgr = GetManager(self._tree)
        """
        self._action_registerer = action_registerer
        self.tree = parent.tree
        """
        self.pane_id = self._tree.GetId()
        self._model = self.model
        # DEBUG: self.frame.Bind(wx.EVT_MOVE, self.OnShowTree) self.frame.Bind(wx.EVT_SHOW, self.OnShowTree)
        self._tree.Bind(wx.EVT_SHOW, self.on_show_tree)
        self._tree.Bind(wx.EVT_MOVE, self.on_tab_changed)
        # parent, action_registerer, , default_settings={'collapsed':True}
        self._pane = self._mgr.GetPane(self._tree)
        self.font = wx.Font(self._app.fontinfo)  # self._tree.GetFont()
        self._tree.SetFont(self.font)
        # print(f"DEBUG: TreePlugin init self.pane_id={self.pane_id} \n"
        #      f"self._pane = {self._pane}")

    def register_frame(self, parent=None):
        if parent:
            self._parent = parent
            if self._mgr.GetPane("tree_content") in self._mgr._panes:
                register = self._mgr.InsertPane
            else:
                register = self._mgr.AddPane
            register(self._tree, wx.lib.agw.aui.AuiPaneInfo().Name("tree_content").
                     Caption(_("Test Suites")).LeftDockable(True))
            self._mgr.Update()

    def enable(self):
        # DEBUG this does not work, the panel has no tree, when we dock from floating
        # DEBUG: Attempt to create Panel and then calling self.OnShowTree
        """
        self.register_action(ActionInfo('View','View Test Suites Explorer', self.OnShowTree,
                                        shortcut='F12',
                                        doc='Show Test Suites tree panel',
                                        position=1))
        """
        self.subscribe(self.on_tree_selection, RideTreeSelection)
        # self.save_setting('opened', True)
        # DEBUG: Add toggle checkbox to menu View/Hide Tree
        if self.opened:
            self.on_show_tree(None)

    def close_tree(self):
        self._mgr.DetachPane(self._tree)
        self._tree.Hide()
        self._mgr.Update()
        self.save_setting('opened', False)

    def disable(self):
        self.close_tree()
        # self.save_setting('opened', False)
        self.unsubscribe_all()
        self.unregister_actions()

    def is_focused(self):
        return self._tree.HasFocus()

    def populate(self, model):
        if model:  # DEBUG: Always populate ... and model != self._model:
            self._model = model
        # print(f"DEBUG: Populating model... {self._model}\n\n")
        self._tree.populate(self._model)

    def set_editor(self, editor):
        self._tree.set_editor(editor)

    def on_show_tree(self, event):
        __ = event
        if not self._parent:
            self._parent = self.frame
        if not self._tree:  # This is not needed because tree is always created
            return  # On Windows this code is executed when closing the app, we return now

        global_settings = self._app.settings.config_obj['General']
        apply_global = global_settings['apply to panels']
        use_own = self.settings['own colors']
        if apply_global or not use_own:
            html_background = self.settings.get('background help', (240, 242, 80))
            html_foreground = self.settings.get('foreground text', (7, 0, 70))
        else:
            html_background = self.settings.get('background', (240, 242, 80))
            html_foreground = self.settings.get('foreground', (7, 0, 70))
        html_font_face = self.settings.get('font face', '')
        html_font_size = self.settings.get('font size', 11)
        self._tree.Show(True)
        # print(f"DEBUG: treeplugin on_show_tree {html_font_face=}  {html_font_size=}")
        self._tree.SetMinSize(wx.Size(200, 225))
        # self.aui_mgr.DetachPane(self._tree)
        # self.aui_mgr.Update()
        # DEBUG: Let's use own method
        # self.aui_mgr.AddPane(self._tree,
        #                   wx.lib.agw.aui.AuiPaneInfo().Name("tree_content").
        #                   Caption("Test Suites").LeftDockable(True).
        #                   CloseButton(True))
        # self.register_frame(self._parent)
        self._tree.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self._tree.SetBackgroundColour(html_background)
        self._tree.SetForegroundColour(html_foreground)
        # self.font = self._tree.GetFont()
        self._tree.SetFont(self.font)
        if html_font_face is not None:
            self.font.SetFaceName(html_font_face)
            self.font.SetPointSize(html_font_size)
            self._tree.SetFont(self.font)
        self._tree.Refresh()
        self._tree.Raise()
        self.save_setting('opened', True)
        self._tree.populate(self._model)
        self._update_tree()
        self._mgr.Update()

    def on_tree_selection(self, message):
        if self.is_focused():
            self._tree.tree_node_selected(message.item)

    def on_tab_changed(self, event):
        __ = event
        self._update_tree()

    def _update_tree(self, event=None):
        __ = event
        self._tree.populate(self._model)
        self._tree.refresh_view()
        self._tree.Update()


class Tree(treemixin.DragAndDrop, customtreectrl.CustomTreeCtrl, wx.Panel):

    def __init__(self, parent, action_registerer, settings=None):
        from ..controller.ui.treecontroller import TreeController
        self._RESOURCES_NODE_LABEL = _('External Resources')
        # print(f"DEBUG: treeplugin.py Tree after importing TreeController  __init__ "
        #       f"translated label={self._RESOURCES_NODE_LABEL}")
        self._checkboxes_for_tests = False
        self._test_selection_controller = self._create_test_selection_controller()
        self.controller = TreeController(self, action_registerer, settings=settings,
                                         test_selection=self._test_selection_controller)
        treemixin.DragAndDrop.__init__(self, parent, **_TREE_ARGS)
        self.controller.register_tree_actions()
        self._bind_tree_events()
        self._images = TreeImageList()
        self._animctrl = None
        self._silent_mode = False
        self.SetImageList(self._images)
        self.label_editor = TreeLabelEditListener(self, action_registerer)
        self.controller.bind_keys()
        self._subscribe_to_messages()
        self._popup_creator = PopupCreator()
        self._dragging = False
        self._clear_tree_data()
        self._editor = None
        self._execution_results = None
        self._resources = []
        self._right_click = False
        self.dirty = False
        # DEBUG: This menu is not working because is being attached to main frame
        # self._menu = wx.Menu()
        # self._menu.Append(wx.ID_CLOSE, item="&Close", helpString="Closes panel")
        # self._mb = wx.MenuBar()
        # self._mb.Append(self._menu, "Menu")
        # self.GetParent().SetMenuBar(self._mb)
        # print(f"DEBUG: Tree tried to add menu to {self.GetParent().__repr__()}  parent={parent}")
        self.pane_id = self.GetId()
        if not hasattr(self, 'OnCancelEdit'):
            self.OnCancelEdit = self._on_cancel_edit

    @staticmethod
    def _create_test_selection_controller():
        from ..controller.ui.treecontroller import TestSelectionController

        tsc = TestSelectionController()
        PUBLISHER.subscribe(tsc.clear_all, RideOpenSuite)
        PUBLISHER.subscribe(tsc.clear_all, RideNewProject)
        return tsc

    def _on_cancel_edit(self, item):
        le = customtreectrl.TreeEvent(
            customtreectrl.wxEVT_TREE_END_LABEL_EDIT, self.GetId())
        le._item = item
        le.SetEventObject(self)
        le._label = ""
        le._editCancelled = True
        self.GetEventHandler().ProcessEvent(le)

    def _bind_tree_events(self):
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_changed)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.on_tree_item_expanding)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_selection)
        # self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(customtreectrl.EVT_TREE_ITEM_CHECKED, self.on_tree_item_checked)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.on_tree_item_collapsing)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_selection(self, event):
        if self._right_click:
            event.Skip()

    def on_double_click(self, event):
        item, _ = self.HitTest(self.ScreenToClient(wx.GetMousePosition()))
        if item:
            handler = self.controller.get_handler(item)
            handler.double_clicked()
        event.Skip()

    def set_editor(self, editor):
        self._editor = editor

    def StartDragging(self):  # Overrides wx method
        self._dragging = True
        treemixin.DragAndDrop.StartDragging(self)

    def OnEndDrag(self, event):  # Overrides wx method
        self._dragging = False
        treemixin.DragAndDrop.OnEndDrag(self, event)

    def register_context_menu_hook(self, callable_m):
        self._popup_creator.add_hook(callable_m)

    def unregister_context_menu_hook(self, callable_m):
        self._popup_creator.remove_hook(callable_m)

    def _subscribe_to_messages(self):
        subscriptions = [
            (self._item_renamed, RideItemNameChanged),
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
            (self._test_result, RideTestPaused),
            (self._test_result, RideTestPassed),
            (self._test_result, RideTestFailed),
            (self._test_result, RideTestSkipped),
            (self._test_result, RideTestStopped),
            (self._handle_import_setting_message, RideImportSetting),
            (self._mark_excludes, RideExcludesChanged),
            (self._mark_excludes, RideIncludesChanged),
        ]
        for listener, topic in subscriptions:
            PUBLISHER.subscribe(listener, topic)

    def _mark_excludes(self, message):
        tree = self.controller.find_node_by_controller(message.old_controller)
        self._render_datafile(self.GetItemParent(tree), message.new_controller)
        self._remove_datafile_node(tree)

    def _set_item_excluded(self, node):
        self.SetItemTextColour(node, wx.TheColourDatabase.Find(colourName="GREY"))
        self.SetItemItalic(node, True)
        self.SetItemText(node, _("%s (excluded)") % self.GetItemText(node))

    def _handle_import_setting_message(self, message):
        if message.is_resource():
            self._set_resource_color(
                message.import_controller.get_imported_controller())
            self._set_resource_color(
                message.import_controller.get_previous_imported_controller())

    def _set_resource_color(self, resource_controller):
        if not resource_controller:
            return
        node = self.controller.find_node_by_controller(resource_controller)
        if node:
            self.SetItemTextColour(
                node, self._get_resource_text_color(resource_controller))

    def _get_resource_text_color(self, resource_controller):
        if resource_controller.is_used():
            return self.GetDefaultAttributes().colFg
        else:
            return wx.LIGHT_GREY

    def _testing_started(self, message):
        self._for_all_drawn_tests(
            self.root, lambda t: self.SetItemImage(t, ROBOT_IMAGE_INDEX))
        self._execution_results = message.results
        self._images.set_execution_results(message.results)

    def _test_result(self, message):
        from ..controller.macrocontrollers import TestCaseController

        test: TestCaseController = message.item
        if not test:
            # test object will be None when running with DataDriver
            # when runner is interrupted, is also None, so let's stop animation
            if self._animctrl:
                self._animctrl.Stop()
                self._animctrl.Animation.Destroy()
                self._animctrl.Destroy()
                self._animctrl = None
            return
        if isinstance(message, RideTestPassed):
            test.run_passed = True
        elif isinstance(message, RideTestFailed):
            test.run_passed = False
        elif isinstance(message, RideTestSkipped):
            test.run_passed = False
        else:
            test.run_passed = None
        wx.CallAfter(self._set_icon_from_execution_results, message.item)

    def _set_icon_from_execution_results(self, controller):
        node = self.controller.find_node_by_controller(controller)
        if not node:
            return
        img_index = self._get_icon_index_for(controller)
        # Always set the static icon
        self.SetItemImage(node, img_index)
        if self._animctrl:
            self._animctrl.Stop()
            self._animctrl.Animation.Destroy()
            self._animctrl.Destroy()
            self._animctrl = None
            self.DeleteItemWindow(node)
        if img_index in (RUNNING_IMAGE_INDEX, PAUSED_IMAGE_INDEX):
            from wx.adv import Animation, AnimationCtrl
            import os
            _BASE = os.path.join(os.path.dirname(__file__), '..', 'widgets')
            if img_index == RUNNING_IMAGE_INDEX:
                img = os.path.join(_BASE, 'robot-running.gif')
            else:
                img = os.path.join(_BASE, 'robot-pause.gif')
            ani = Animation(img)
            obj = self
            rect = (node.GetX()+20, node.GetY())  # Overlaps robot icon
            self._animctrl = AnimationCtrl(obj, -1, ani, rect)
            """
            self._animctrl.SetBackgroundColour(obj.GetBackgroundColour())
            """
            self._animctrl.SetBackgroundColour('white')
            self.SetItemWindow(node, self._animctrl, False)
            self._animctrl.Play()
        # Make visible the running or paused test
        parent = node.GetParent()
        self.EnsureVisible(parent)  # DEBUG add animation to parent if suite setup/teardown started
        self.ExpandAllChildren(parent)
        self.EnsureVisible(node)
        self.ExpandAllChildren(node)
        self.Update()

    def _get_icon_index_for(self, controller):
        if not self._execution_results:
            return ROBOT_IMAGE_INDEX
        if self._execution_results.is_paused(controller):
            return PAUSED_IMAGE_INDEX
        if self._execution_results.is_running(controller):
            return RUNNING_IMAGE_INDEX
        if self._execution_results.has_passed(controller):
            return PASSED_IMAGE_INDEX
        if self._execution_results.has_failed(controller):
            return FAILED_IMAGE_INDEX
        if self._execution_results.has_skipped(controller):
            return SKIPPED_IMAGE_INDEX
        return ROBOT_IMAGE_INDEX

    def populate(self, model):
        self._clear_tree_data()
        self._populate_model(model)
        self.refresh_view()
        self.SetFocus()  # Needed for keyboard shortcuts

    def _clear_tree_data(self):
        self.DeleteAllItems()
        self.root = self.AddRoot('')
        self._resource_root = self._create_resource_root()
        self.datafile_nodes = []
        self._resources = []
        self.controller.clear_history()

    def _create_resource_root(self):
        return self._create_node(self.root, self._RESOURCES_NODE_LABEL,
                                 self._images.directory)

    def _populate_model(self, model):
        handler = ResourceRootHandler(model, self, self._resource_root,
                                      self.controller.settings)
        # print(f"DEBUG: _populate_model model={model} self._resource_root={self._resource_root}"
        #       f" self._controller.settings={self._controller.settings}")
        self.SetPyData(self._resource_root, handler)
        if model.data:
            self._render_datafile(self.root, model.data, 0)
        for res in model.external_resources:
            if not res.parent:
                self._render_datafile(self._resource_root, res)

    def _resource_added(self, message):
        ctrl = message.datafile
        if self.controller.find_node_by_controller(ctrl):
            return
        if ctrl.parent:
            parent = self._get_dir_node(ctrl.parent)
        else:
            parent = self._resource_root
        self._render_datafile(parent, ctrl)

    def _get_dir_node(self, ctrl):
        if ctrl is None:
            return self.root
        dir_node = self._get_datafile_node(ctrl.data)
        if dir_node is None:
            parent = self._get_dir_node(ctrl.parent)
            self._render_datafile(parent, ctrl)
            dir_node = self._get_datafile_node(ctrl.data)
        return dir_node

    def _select_resource(self, message):
        self.select_controller_node(message.item)

    def select_controller_node(self, controller):
        self.SelectItem(self.controller.find_node_by_controller(controller))

    def _suite_added(self, message):
        self.add_datafile(message.parent, message.suite)

    def refresh_view(self):
        self.Show()
        self.Refresh()
        # print(f"DEBUG: Called Tree._refresh_view {self.GetParent().GetClassName()}")
        if self._resource_root:
            self.Expand(self._resource_root)
        if self.datafile_nodes:
            self._expand_and_render_children(self.datafile_nodes[0])
            wx.CallAfter(self.SelectItem, self.datafile_nodes[0])
        self.Update()
        # print(f"DEBUG: Called Tree._refresh_view parent={self.GetParent().GetClassName()} self={self}")

    def _render_datafile(self, parent_node, controller, index=None):
        node = self._create_node_with_handler(parent_node, controller, index)
        if not node:
            return None
        if controller.dirty:
            self.controller.mark_node_dirty(node)
        self.datafile_nodes.append(node)
        self.SetItemHasChildren(node, True)

        for child in controller.children:
            self._render_datafile(node, child)
        return node

    @staticmethod
    def _normalize(path):
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))

    def _create_node_with_handler(self, parent_node, controller, index=None):
        from ..controller.filecontrollers import ResourceFileController
        if (controller.display_name.startswith("#") or
                controller.display_name.startswith("...")):  # If it is a comment or continuation marker don't create
            return None

        handler_class = action_handler_class(controller)
        with_checkbox = (handler_class == TestCaseHandler and self._checkboxes_for_tests)
        node = self._create_node(parent_node, controller.display_name, self._images[controller],
                                 index, with_checkbox=with_checkbox)
        if isinstance(controller, ResourceFileController) and not controller.is_used():
            self.SetItemTextColour(node, TREETEXTCOLOUR)  # wxPython3 hack
        action_handler = handler_class(controller, self, node, self.controller.settings)
        self.SetPyData(node, action_handler)

        # if we have a TestCase node we have to make sure that
        # we retain the checked state
        if (handler_class == TestCaseHandler and self._checkboxes_for_tests) \
                and self._test_selection_controller.is_test_selected(controller):
            self.CheckItem(node, True)
        if controller.is_excluded():
            self._set_item_excluded(node)
        return node

    def set_checkboxes_for_tests(self):
        self._checkboxes_for_tests = True

    def _expand_and_render_children(self, node):
        assert node is not None
        self._render_children(node)
        self.Expand(node)

    def _render_children(self, node):
        handler = self.controller.get_handler(node)
        if not handler or not handler.can_be_rendered:
            return
        self._create_child_nodes(
            node, handler, lambda item: item.is_test_suite)
        handler.set_rendered()

    def _create_child_nodes(self, node, handler, predicate):
        for childitem in self._children_of(handler):
            index = self._get_insertion_index(node, predicate)
            self._create_node_with_handler(node, childitem, index)

    @staticmethod
    def _children_of(handler):
        return [v for v in handler.variables if v.has_data()] + list(handler.tests) + list(handler.keywords)

    def _create_node(self, parent_node, label, img, index=None, with_checkbox=False):
        node = self._wx_node(parent_node, index, label, with_checkbox)
        self.SetItemImage(node, img.normal, wx.TreeItemIcon_Normal)
        self.SetItemImage(node, img.expanded, wx.TreeItemIcon_Expanded)
        return node

    def _wx_node(self, parent_node, index, label, with_checkbox):
        ct_type = 1 if with_checkbox else 0
        if index is not None:
            # blame wxPython for this ugliness
            if isinstance(index, int):
                return self.InsertItemByIndex(
                    parent_node, index, label, ct_type=ct_type)
            else:
                return self.InsertItem(
                    parent_node, index, label, ct_type=ct_type)
        return self.AppendItem(parent_node, label, ct_type=ct_type)

    def add_datafile(self, parent, suite):
        snode = self._render_datafile(
            self._get_datafile_node(parent.data), suite)
        self.SelectItem(snode)

    def add_test(self, parent_node, test):
        self._add_dataitem(
            parent_node, test, lambda item: item.is_user_keyword)

    def add_keyword(self, parent_node, kw):
        self._add_dataitem(parent_node, kw, lambda item: item.is_test_suite)

    def _add_dataitem(self, parent_node, dataitem, predicate):
        node = self._get_or_create_node(parent_node, dataitem, predicate)
        self._select(node)
        self.controller.mark_node_dirty(parent_node)

    def _get_or_create_node(self, parent_node, dataitem, predicate):
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
            return self.controller.find_node_with_label(
                parent_node, dataitem.display_name)

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
            if predicate(self.controller.get_handler(item)):
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
        self._get_or_create_node(
            self._get_datafile_node(self.get_selected_datafile()),
            message.item,
            lambda item: not item.is_variable or item.index > message.index)

    def _leaf_item_removed(self, message):
        node = self.controller.find_node_by_controller(message.item)
        parent_node = self._get_datafile_node(message.datafile)
        # DEBUG The below call causes not calling delete_node
        # self._test_selection_controller.select(message.item, False)
        self.controller.mark_node_dirty(parent_node)
        self.delete_node(node)

    def _test_added(self, message):
        self.add_test(self._get_datafile_node(self.get_selected_datafile()),
                      message.item)

    def _datafile_removed(self, message):
        dfnode = self._get_datafile_node(message.datafile.data)
        self.datafile_nodes.remove(dfnode)
        self.DeleteChildren(dfnode)
        self.Delete(dfnode)

    def _datafile_set(self, message):
        wx.CallAfter(self._refresh_datafile_when_file_set, message.item)

    def _filename_changed(self, message):
        from ..controller import ResourceFileController
        df = message.datafile
        node = self.controller.find_node_by_controller(df)
        if not node:
            raise AssertionError('No node found with controller "%s"' % df)
        old_name = node.GetText()
        # print(f"DEBUG: treeplugin.py Tree _filename_changed message={message} df={df}"
        #       f" node={node} {old_name=} df.display_name={df.display_name}")
        wx.CallAfter(self.SetItemText, node, df.display_name)
        if isinstance(df, ResourceFileController):
            RideItemNameChanged(item=node, old_name=old_name, new_name=df.display_name).publish()

    def add_keyword_controller(self, controller):
        parent = self._get_datafile_node(self.get_selected_datafile())
        self.add_keyword(parent, controller)

    def delete_node(self, node):
        if node is None:
            return
        parent = self.GetItemParent(node)
        self.controller.mark_node_dirty(parent)
        self.Delete(node)
        wx.CallAfter(self.SelectItem, parent)

    def _data_dirty(self, message):
        # print("DEBUG: TreePlugin tree _data_dirty ENTER")
        if not self.dirty:
            self.dirty = True
            self.controller.mark_controller_dirty(message.datafile)

    def _data_undirty(self, message):
        _ = message
        # print("DEBUG: TreePlugin tree _data_undirty")
        self.unset_dirty()

    def unset_dirty(self):
        for node in self.datafile_nodes:
            text = self.GetItemText(node)
            handler = self.controller.get_handler(node)
            if text.startswith('*') and not handler.controller.dirty:
                self.SetItemText(node, text[1:])
                self.dirty = False

    def select_node_by_data(self, controller):
        """Find and select the tree item associated with the given controller.

        Controller can be any of the controllers that are represented in the
        tree."""
        parent_node = self._get_datafile_node(controller.datafile)
        # print(f"DEBUG: treeplugin.py Tree select_node_by_data parent_node={parent_node}")
        if not parent_node:
            return None
        # if not self.IsExpanded(parent_node):
        self.EnsureVisible(parent_node)
        self._expand_and_render_children(parent_node)
        node = self.controller.find_node_by_controller(controller)
        if node and node != self.GetSelection():
            self.SelectItem(node)
        return node

    def select_user_keyword_node(self, uk):
        parent_node = self._get_datafile_node(uk.parent.parent)
        if not parent_node:
            return
        self.EnsureVisible(parent_node)
        if not self.IsExpanded(parent_node):
            self._expand_and_render_children(parent_node)
        node = self.controller.find_node_with_label(parent_node, utils.normalize(uk.name))
        # print(f"DEBUG: treeplugin.py Tree select_user_keyword_node node= {node}")
        if node != self.GetSelection():
            self.SelectItem(node)

    def _get_datafile_node(self, datafile):
        # print(f"DEBUG: treeplugin.py Tree _get_datafile_node ENTER dataffile= {datafile}")
        for node in self.datafile_nodes:
            item = self.controller.get_handler(node).item
            if item == datafile:  # This only works before editing a resource item because the obj id changes
                return node
            if type(item) == type(datafile) and hasattr(item, 'name') and item.name == datafile.name:
                return node
        return None

    def get_selected_datafile(self):
        """Returns currently selected data file.

        If a test or user keyword node is selected, returns parent of that
        item."""
        datafile = self._get_selected_datafile_node()
        if not datafile:
            return None
        return self.controller.get_handler(datafile).item

    def get_selected_datafile_controller(self):
        """Returns controller associated with currently active data file.

        If a test or user keyword node is selected, returns parent of that
        item."""
        dfnode = self._get_selected_datafile_node()

        if dfnode:
            return self.controller.get_handler(dfnode).controller
        else:
            return None

    def _get_selected_datafile_node(self):
        node = self.GetSelection()
        if not node or node in (self._resource_root, self.root):
            return None
        while node not in self.datafile_nodes:
            node = self.GetItemParent(node)
        return node

    def get_selected_item(self):
        """Returns model object associated with currently selected tree node.
        """
        selection = self.GetSelection()
        if not selection:
            return None
        handler = self.controller.get_handler(selection)
        return handler and handler.controller or None

    def tree_node_selected(self, node):
        # print(f"DEBUG: TreePlugin tree node selected {str(node)}")
        pass

    def move_up(self, node):
        prev = self.GetPrevSibling(node)
        if prev.IsOk():
            self._switch_items(prev, node, node)

    def move_down(self, node):
        _next = self.GetNextSibling(node)
        if _next.IsOk():
            self._switch_items(node, _next, node)

    def _switch_items(self, first, second, currently_selected):
        """Changes the order of given items, first is expected to be directly
        above the second"""
        selection = self.GetItemData(currently_selected).controller
        controller = self.controller.get_handler(first).controller
        self.Delete(first)
        self._create_node_with_handler(self.GetItemParent(second), controller, second)
        self.select_node_by_data(selection)

    def _refresh_datafile_when_file_set(self, controller):
        # remove invalid cases selection when data file is changed in text editor
        self._test_selection_controller.remove_invalid_cases_selection(controller)
        # Prevent tab selections based on tree item selected events
        self._start_silent_mode()
        current = self.get_selected_datafile_controller()
        if not current:  # If tree is not yet in use - do not expand anything.
            self._end_silent_mode()
            return

        item = self.GetSelection()
        current_txt = self.GetItemText(item) if item.IsOk() else ''
        # after refresh current and current_txt might have been changed
        node = self._refresh_datafile(controller)
        if node is None:
            # DEBUG: Find out why this sometimes happens
            return
        self._expand_and_render_children(node)
        if current == controller:
            select_item = self.controller.find_node_with_label(
                node, current_txt)
            if select_item is None:
                select_item = node
            wx.CallAfter(self.SelectItem, select_item)
            wx.CallAfter(self._end_silent_mode)
        else:
            self._end_silent_mode()

    def _uncheck_tests(self, controller):
        self._test_selection_controller.unselect_all(controller.tests)

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
            parent = self.GetItemParent(orig_node)
            self._remove_datafile_node(orig_node)
            return self._render_datafile(parent, controller, insertion_index)

    def _get_pending_selection(self, event):
        if hasattr(event, 'Item'):
            item = event.GetItem()
            event.Veto()
        elif hasattr(event, 'Position'):
            item, flags = self.HitTest(event.Position)
            if not self._click_on_item(item, flags):
                return
        else:
            return
        return self.GetItemText(item)

    def _get_data_controller_node(self, controller):
        for node in self.datafile_nodes:
            if self.GetItemData(node).controller == controller:
                return node
        return None

    @staticmethod
    def _click_on_item(item, flags):
        return item is not None and item.IsOk() and flags & wx.TREE_HITTEST_ONITEM

    def _get_datafile_index(self, node):
        insertion_index = self.GetPrevSibling(node)
        if not insertion_index:
            insertion_index = 0
        return insertion_index

    def _remove_datafile_node(self, node):
        for child in self.GetItemChildren(node):
            if child in self.datafile_nodes:
                self._remove_datafile_node(child)
        self.datafile_nodes.remove(node)
        self.Delete(node)

    def _handle_pending_selection(self, to_be_selected, parent_node):
        if to_be_selected:
            self._expand_and_render_children(parent_node)
            select_item = self.controller.find_node_with_label(
                parent_node, to_be_selected)
            wx.CallAfter(self.SelectItem, select_item)

    def on_sel_changed(self, event):
        node = event.GetItem()
        if not node.IsOk() or self._dragging:
            event.Skip()
            return
        self.controller.add_to_history(node)
        handler = self.controller.get_handler(node)
        if handler and handler.item:
            self._update_data_file_namespace(node)
            RideTreeSelection(
                node=node,
                item=handler.controller,
                silent=self._silent_mode).publish()
        self.SetFocus()

    def _update_data_file_namespace(self, node):
        while True:
            if not node:
                return
            handler = self.controller.get_handler(node)
            if hasattr(handler.controller, 'get_namespace'):
                data_file_ns = handler.controller.get_namespace()
                if not data_file_ns:
                    return
                cur_dir = handler.controller.directory
                if data_file_ns:
                    data_file_ns.update_cur_dir_global_var(cur_dir)
                return
            else:
                node = node.GetParent()

    def on_tree_item_expanding(self, event):
        node = event.GetItem()
        if node.IsOk():
            self._render_children(node)

    # This exists because CustomTreeItem does not remove animations
    def on_tree_item_collapsing(self, event):
        item = event.GetItem()
        self._hide_item(item)
        event.Skip()

    def _hide_item(self, item):
        for item in item.GetChildren():
            itemwindow = item.GetWindow()
            if itemwindow:
                itemwindow.Hide()
            if self.ItemHasChildren(item):
                self._hide_item(item)

    def SelectAllTests(self, item: GenericTreeItem, selected=True):
        """
        Select tests for execution
        :param item: The node of the graphical tree where the user triggered the action from
        :param selected: Whether we want to select or un-select for execution
        :return: Nothing
        """
        test_controllers = self.retrieveTestCaseControllers(item)
        self._test_selection_controller.select_all(test_controllers, selected)

    @staticmethod
    def retrieveTestCaseControllers(item: GenericTreeItem):
        from ..controller.filecontrollers import TestDataDirectoryController, TestCaseFileController

        data = item.GetData()
        if isinstance(data, TestDataDirectoryHandler):
            item_controller: TestDataDirectoryController = data.tests.parent
        elif isinstance(data, TestCaseFileHandler):
            item_controller: TestCaseFileController = data.controller
        else:
            raise AttributeError("Unexpected type of handler: " + str(data))
        test_controllers = item_controller.retrieve_test_controllers()
        return test_controllers

    def SelectTests(self, tests):
        self._test_selection_controller.select_all(tests)

    def ExpandAllSubNodes(self, item):
        self._expand_or_collapse_nodes(item, self.Expand)

    def CollapseAllSubNodes(self, item):
        self._expand_or_collapse_nodes(item, self.Collapse)

    def _expand_or_collapse_nodes(self, item, callback):
        if not self.HasAGWFlag(customtreectrl.TR_HIDE_ROOT) or item != self.GetRootItem():
            callback(item)
            for child in item.GetChildren():
                self._expand_or_collapse_nodes(child, callback)

    def _for_all_drawn_tests(self, item, func):
        if self._is_test_node(item):
            func(item)
        for child in item.GetChildren():
            self._for_all_drawn_tests(child, func)

    @staticmethod
    def _is_test_node(node):
        return node.GetType() == 1

    def DeselectTests(self, tests):
        self._test_selection_controller.unselect_all(tests)

    def SelectFailedTests(self, item):
        all_controllers = self.retrieveTestCaseControllers(item)
        test_controllers = filter(
            lambda ctrl: ctrl.run_passed is False,
            all_controllers)
        self._test_selection_controller.unselect_all(all_controllers)
        self._test_selection_controller.select_all(test_controllers)

    def SelectPassedTests(self, item):
        all_controllers = self.retrieveTestCaseControllers(item)
        test_controllers = filter(
            lambda ctrl: ctrl.run_passed is True,
            all_controllers)
        self._test_selection_controller.unselect_all(all_controllers)
        self._test_selection_controller.select_all(test_controllers)

    def on_close(self, event):
        __ = event
        print("DEBUG: Tree OnClose hidding")
        self.Hide()

    def on_tree_item_checked(self, event):
        node: GenericTreeItem = event.GetItem()
        handler: TestCaseHandler = self.controller.get_handler(node=node)
        self._test_selection_controller.select(
                handler.controller, node.IsChecked())

    def on_item_activated(self, event):
        node = event.GetItem()
        if self.IsExpanded(node):
            self.Collapse(node)
        elif self.ItemHasChildren(node):
            self._expand_and_render_children(node)

    def on_left_arrow(self, event):
        node = self.GetSelection()
        if self.IsExpanded(node):
            self.Collapse(node)
        else:
            event.Skip()

    def on_right_click(self, event):
        __ = event
        if not self._right_click:
            self._right_click = True
        handler = None
        item, _ = self.HitTest(self.ScreenToClient(wx.GetMousePosition()), wx.TREE_HITTEST_ONITEMLABEL)
        if item:
            # print(f"DEBUG: tree mouse RightClick pos={pos}")
            handler = self.GetItemData(item)
        if handler:
            handler.show_popup()
            self._right_click = False

    def on_new_test_case(self, event):
        handler = self.controller.get_handler()
        if handler:
            handler.on_new_test_case(event)

    def OnDrop(self, target, dragged):  # Overrides wx method
        dragged = self.controller.get_handler(dragged)
        target = self.controller.get_handler(target)
        if target and target.accepts_drag(dragged):
            dragged.controller.execute(MoveTo(target.controller))
        self.Refresh()  # DEBUG Always refresh

    def IsValidDragItem(self, item):  # Overrides wx method
        return self.controller.get_handler(item).is_draggable

    def on_move_up(self, event):
        handler = self.controller.get_handler()
        if handler.is_draggable:
            handler.on_move_up(event)

    def on_move_down(self, event):
        handler = self.controller.get_handler()
        if handler.is_draggable:
            handler.on_move_down(event)

    def _item_changed(self, message):
        # print(f"DEBUG: treeplugin.py Tree _item_changed ENTER message={message}")
        if isinstance(message, RideItemNameChanged):
            return
        controller = message.item
        node = self.controller.find_node_by_controller(controller)
        if node:
            self.SetItemText(node, message.item.name)
            self.controller.mark_node_dirty(self._get_datafile_node(controller.datafile))
        # if controller.dirty:

    def _item_renamed(self, message):
        from ..lib.robot.parsing.settings import Resource
        # print(f"DEBUG: treeplugin.py Tree _item_renamed ENTER message={message}")
        if not isinstance(message, RideItemNameChanged):
            return
        controller = message.item
        # print(f"DEBUG: treeplugin.py Tree _item_renamed DEFINED controller={controller}"
        #       f" old_name={message.old_name}  new_name={message.new_name}\n")
        node = (self.controller.find_node_by_controller(controller) or
                self.controller.find_node_with_label(controller, message.old_name))
        # print(f"DEBUG: treeplugin.py Tree _item_renamed ENTER controller={controller}"
        #       f" NODE={node}")
        if hasattr(controller, 'datafile') and hasattr(controller.datafile, 'setting_table'):
            imports = controller.datafile.setting_table.imports
            # print(f"DEBUG: treeplugin.py Tree _item_renamed HAS IMPORTS imports={imports}")
            for imp in imports:
                if isinstance(imp, Resource) and hasattr(message.item, 'keyword'):
                    # print(f"DEBUG: treeplugin.py Tree _item_renamed IMPORT message.item.name={message.item.keyword},"
                    #       f" old_name={message.old_name} resource name={imp.name}")
                    # print(f"DEBUG: treeplugin.py Tree _item_renamed IMPORT message.item.name={message},"
                    #       f" old_name={message.old_name} import={imp}")
                    self._rename_resource_kw(new_name=message.item.keyword, old_name=message.old_name, resource=imp)
        # if node and hasattr(message, 'old_name'):
            # print(f"DEBUG: treeplugin.py Tree _item_renamed RENAMED node={node}, old_name={message.old_name}\n"
            #      f"new_name={message.new_name}")
            # Here we need to rename all resourc prefixed occurrencees

        self.Refresh()
        if node and hasattr(message.item, 'name'):
            self.EnsureVisible(node)
            self.SelectItem(node)
            self.SetItemText(node, message.item.name)
            new_name=self.GetItemText(node)
            # print(f"DEBUG: treeplugin.py Tree _item_renamed AFTER RENAMED new_name={new_name}"
            #       f" controller={controller.datafile}")
        else:
            return
        if controller.dirty:
            self.controller.mark_node_dirty(
                self._get_datafile_node(controller.datafile))

    def _rename_resource_kw(self, new_name, old_name, resource):
        prefix_new = new_name.split('.')[0]
        prefix_old = old_name.split('.')[0]
        prefix_res = os.path.basename(resource.name).split('.')[0]
        if not prefix_new == prefix_old == prefix_res:
            return
        keyword_name = old_name.split('.')[-1]
        new_keyword_name = new_name.split('.')[-1]
        # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw {prefix_res=} {keyword_name=}")
        res_name=os.path.basename(resource.name)
        # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw {res_name=}")
        res_node=self.FindItem(self._resource_root, res_name)
        if res_node:
            self.EnsureVisible(res_node)
            # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw root node {res_node=}")
            # node = self.controller.find_node_with_label(res_node, keyword_name)
            self._expand_and_render_children(res_node)
            node = self.FindItem(res_node, keyword_name)
            if node:
                from ..controller.ctrlcommands import RenameKeywordOccurrences
                from ..ui.progress import RenameProgressObserver
                nlabel = node.GetText()
                # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw node label {nlabel} {keyword_name}")
                if nlabel == keyword_name:
                    # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw {node=} {nlabel} change to {new_keyword_name=}")
                    self.EnsureVisible(node)
                    # self.SetItemText(node, new_keyword_name)
                    self.SelectItem(node)
                    controller = self.get_selected_datafile_controller()
                    keywords = controller.keywords
                    keyword_names = controller.get_keyword_names()
                    # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw already changed to {new_keyword_name=}"
                    #       f" controller={controller} keywords={keywords} \n"
                    #       f"{keyword_names=}")
                    for k in keywords.items:
                        # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw keywords: {k=}")
                        if k.name == keyword_name:
                            # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw CHANGING: {k.name=},"
                            #       f" {k.source=} ")  # {k.details=}")
                            if controller.validate_keyword_name(new_keyword_name):
                                k.name = new_keyword_name
                                node.SetText(new_keyword_name)
                                RideUserKeywordRenamed(datafile=controller.datafile, item=k,
                                                       old_name=keyword_name).publish()
                                controller.mark_dirty()
                                # print(f"DEBUG: treeplugin.py Tree _rename_resource_kw DONE CHANGING: {k.name=}")
                                # self.controller.mark_node_dirty(self._get_datafile_node(controller.datafile))
                                self.observer = RenameProgressObserver(self.GetParent())
                                RenameKeywordOccurrences(keyword_name, new_keyword_name, self.observer)
                                self.observer.finish()
                                self.Collapse(res_node)
                                self.Expand(res_node)
                                self.Refresh()
                                self.SelectItem(node)
                            else:
                                wx.MessageBox(f"Invalid keyword name: {new_keyword_name}",
                                              "Failed Keyword Name Validation")
                                return

    def _variable_moved_up(self, message):
        if self._should_update_variable_positions(message):
            self._do_action_if_datafile_node_is_expanded(self.move_up, message)

    def _variable_moved_down(self, message):
        if self._should_update_variable_positions(message):
            self._do_action_if_datafile_node_is_expanded(self.move_down, message)

    @staticmethod
    def _should_update_variable_positions(message):
        return message.item != message.other and message.item.has_data() and message.other.has_data()

    def _do_action_if_datafile_node_is_expanded(self, action, data):
        if self.IsExpanded(self._get_datafile_node(data.item.datafile)):
            node = self.controller.find_node_by_controller(data.item)
            action(node)

    def _variable_updated(self, message):
        self._item_changed(message)

    def highlight(self, data, text):
        self.select_node_by_data(data)
        self._editor.highlight(text)

    def node_is_resource_file(self, node):
        return self.controller.get_handler(node).__class__ == \
            ResourceFileHandler


class TreeLabelEditListener(object):

    def __init__(self, tree, action_registerer):
        self._tree = tree
        tree.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_begin_label_edit)
        tree.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_label_edited)
        tree.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        if IS_WINDOWS:
            # Delete key does not work in windows without registration
            delete_key_action = ActionInfo(
                None, None, action=self.on_delete, shortcut='Del')
            action_registerer.register_shortcut(delete_key_action)
        self._editing_label = False
        self._on_label_edit_called = False

    def on_begin_label_edit(self, event):
        # See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        self._editing_label = True
        if not self._on_label_edit_called:
            self.on_label_edit()
            event.Veto()
            # On windows CustomTreeCtrl will create Editor component
            # And we want this to be done by the handler -- as it knows if
            # there should be one or not. And because this will make it work
            # the same way as when pressing F2  so in other words there is
            # a bug if we don't Veto this event

    def on_label_edit(self, event=None):
        __ = event
        if not self._on_label_edit_called:
            self._on_label_edit_called = True
            handler = self._tree.controller.get_handler()
            if handler and not handler.begin_label_edit():
                self._on_label_edit_called = False
                self._editing_label = False

    def on_label_edited(self, event):
        self._editing_label = False
        self._on_label_edit_called = False
        self._tree.controller.get_handler(event.GetItem()).end_label_edit(event)

        # Reset edit control as it doesn't seem to reset it in case the focus
        # goes directly away from the tree control
        # Use CallAfter to prevent messing up the current end label edit
        # and the another CallAfter because of
        # customtreectrl.TreeTextCtrl#OnChar will call CallAfter(self.Finish)
        # when Enter is pressed --> Results in PyDeadObject if called after
        # ResetEditControl
        wx.CallAfter(wx.CallAfter, self._stop_editing)

    def _stop_editing(self):
        control = self._tree.GetEditControl()
        if control and wx.Window.FindFocus():
            control.StopEditing()

    def on_delete(self, event):
        __ = event
        editor = self._tree.GetEditControl()
        if editor and wx.Window.FindFocus() == editor:
            start, end = editor.GetSelection()
            editor.Remove(start, max(end, start + 1))

    def on_left_down(self, event):
        # See http://code.google.com/p/robotframework-ride/issues/detail?id=756
        if IS_WINDOWS and self._editing_label:
            # This method works only on Windows, luckily the issue 756 exists
            # only on Windows
            self._tree.OnCancelEdit(self._tree.GetSelection())
        event.Skip()

    def get_handler(self, item=None):
        return self._tree.get_handler(item)
