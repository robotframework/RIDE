#  Copyright 2020-     Robot Framework Foundation
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
from wx.lib.agw import customtreectrl
from wx.lib.agw.aui import GetManager

from ..controller import ctrlcommands
from ..controller.filecontrollers import start_filemanager
from ..controller.project import Project
from ..pluginapi import Plugin
from ..pluginapi.plugin import ActionInfo
from ..widgets import PopupCreator, PopupMenuItems

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

FILE_MANAGER = 'file manager'
LABEL_OPEN = 'Open'
LABEL_OPEN_FOLDER = 'Open Containing Folder'


class FileExplorerPlugin(Plugin):
    __doc__ = _("""Provides a tree view for Files and Folders. Opens selected item with mouse right-click.""")

    datafile = property(lambda self: self.get_selected_datafile())
    defaults = {"opened": True,
                "docked": True,
                "own colors": False
                }

    def __init__(self, application, controller=None):
        Plugin.__init__(self, application, default_settings=self.defaults)
        self._app = application
        self.settings = self._app.settings.config_obj['Plugins']['File Explorer']
        self._parent = wx.App.Get().GetTopWindow()
        self._controller = controller
        # if self.filemgr is None:
        self._filemgr = FileExplorer(self._parent, self._controller, self)
        # self.__setattr__('filemgr', self._filemgr)
        # else:
        # self._filemgr = self.filemgr
        self._filemgr.SetThemeEnabled(True)
        self._mgr = GetManager(self._filemgr)
        self._pane = None
        self._filetreectrl = None
        self.opened = self.settings['opened']
        self.font = self._filemgr.GetFont()
        self._popup_creator = PopupCreator()
        self._actions = [
            _('Open'),
            '---',
            _('Open Containing Folder')
        ]
        self._actions_nt = [
            LABEL_OPEN,
            '---',
            LABEL_OPEN_FOLDER
        ]

    def register_frame(self, parent=None):
        if parent:
            self._parent = parent

            if self._mgr.GetPane("file_manager") in self._mgr._panes:
                register = self._mgr.InsertPane
            else:
                register = self._mgr.AddPane

            register(self._filemgr, wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                     Caption(_("Files")).LeftDockable(True).CloseButton(False))

            self._mgr.Update()

    def enable(self):
        self.register_action(ActionInfo(_('View'), _('View File Explorer'), self.toggle_view,
                                        shortcut='F11',
                                        doc=_('Show File Explorer panel'),
                                        position=1))
        self.show_file_explorer()
        if not self.opened:
            self.close_tree()

    def close_tree(self):
        # self.save_setting('opened', False)
        self.opened = False
        self._mgr.DetachPane(self._filemgr)
        self._filemgr.Hide()
        self._mgr.Update()

    def is_focused(self):
        return self._filemgr.HasFocus()

    def toggle_view(self, event):
        __ = event
        self.save_setting('opened', not self.opened)
        if not self.opened:
            self.opened = True
            self.show_file_explorer()
        else:
            self.close_tree()

    def show_file_explorer(self):
        if not self._parent:
            self._parent = wx.App.Get().GetWindow()  # self.frame
        if not self._filemgr:  # This is not needed because file explorer is always created
            self._filemgr = FileExplorer(self._parent, self._controller, self)

        self._pane = self._mgr.GetPane(self._filemgr)
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
        self._filetreectrl = self._filemgr.GetTreeCtrl()
        self._filemgr.Show(True)
        self._filemgr.SetMinSize(wx.Size(200, 225))
        self._mgr.DetachPane(self._filemgr)
        self._mgr.AddPane(self.filemgr,
                          wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                          Caption(_("Files")).LeftDockable(True).
                          CloseButton(False))
        self._filemgr.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self._filemgr.SetBackgroundColour(html_background)
        self._filemgr.SetForegroundColour(html_foreground)
        self.font = self._filemgr.GetFont()
        self.font.SetFaceName(html_font_face)
        self.font.SetPointSize(html_font_size)
        self._filemgr.SetFont(self.font)
        self._filemgr.Refresh()
        self._filetreectrl.SetBackgroundColour(html_background)
        self._filetreectrl.SetForegroundColour(html_foreground)
        self._filetreectrl.SetFont(self.font)
        self._filetreectrl.Refresh()
        self._filemgr.Raise()
        self._mgr.Update()
        self.update_tree()

    def update_tree(self):
        if not self._filemgr:
            return
        self._filemgr.update_tree()

    def show_popup(self):
        self._popup_creator.show(self._filemgr, PopupMenuItems(self, self._actions, self._actions_nt), self._controller)

    def on_open(self, event):
        # __ = event
        print(f"DEBUG: FileExplorerPlugin call on_open_file={event}")
        # self._controller.execute(
        self._parent.on_open_file(event)

    def on_open_containing_folder(self, event):
        __ = event
        print(f"DEBUG: FileExplorerPlugin call on_open_containing_folder={event}")
        try:
            file_manager = self.settings['General'][FILE_MANAGER]
        except KeyError:
            file_manager = None
        #  self._controller.execute(
        # ctrlcommands.OpenContainingFolder(file_manager, self._filemgr.current_path)
        start_filemanager(self._filemgr.current_path, file_manager)


class FileExplorer(wx.GenericDirCtrl):

    def __init__(self, parent, controller=None, plugin=None):
        wx.GenericDirCtrl.__init__(self, parent, id=-1, size=(200, 225), style=wx.DIRCTRL_3D_INTERNAL)
        self._controller = controller
        self.plugin = plugin or self
        self._right_click = False
        self.current_path = None
        # self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_click)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_right_click)
        self.SetThemeEnabled(True)
        self.Refresh()

    def update_tree(self):
        if isinstance(self._controller, Project):
            if self._controller.data and len(self._controller.data.directory) > 1:
                self.SelectPath(self._controller.data.source)
                try:
                    self.ExpandPath(self._controller.data.source)
                except Exception:
                    pass
                self.Refresh()
                self.Update()

    def on_right_click(self, event):
        # __ = event
        # event.Skip()
        print(f"DEBUG: FileExplorer mouse RightClick event={event} controller={self._controller}")
        if not self._right_click:
            self._right_click = True
        handler = None
        # item = self.HitTest(self.ScreenToClient(wx.GetMousePosition()))  #  wx.TREE_HITTEST_ONITEMLABEL)
        tc = self.GetTreeCtrl()
        item, _ = tc.HitTest(self.ScreenToClient(wx.GetMousePosition()))
        if item:
            print(f"DEBUG: FileExplorer mouse RightClick item={item} type={type(item)}")
            # id=self.GetPopupMenuSelectionFromUser()
            handler = self.GetPath(item)  # self.GetItemData(item)
        if handler:
            # handler.show_popup()
            self.current_path = handler
            print(f"DEBUG: FileExplorer PATH={handler}")
            if self.plugin:
                self.plugin.show_popup()
            self._right_click = False
