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

from ..controller.project import Project
from ..pluginapi import Plugin
from ..pluginapi.plugin import ActionInfo

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


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
        self._filemgr = self.filemgr
        self._filemgr.SetThemeEnabled(True)
        self._mgr = GetManager(self._filemgr)
        self._controller = controller
        self._pane = None
        self._filetreectrl = None
        self.opened = self.settings['opened']
        self.font = self._filemgr.GetFont()

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
            self._filemgr = FileExplorer(self._parent, self._controller)

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


class FileExplorer(wx.GenericDirCtrl):

    def __init__(self, parent, controller=None):
        wx.GenericDirCtrl.__init__(self, parent, id=-1, size=(200, 225), style=wx.DIRCTRL_3D_INTERNAL)
        self._controller = controller
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
