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

import wx
from wx import Colour
from wx.lib.agw import customtreectrl
from wx.lib.agw.aui import GetManager

from ..controller.project import Project
from ..pluginapi import Plugin
from ..pluginapi.plugin import ActionInfo


class FileExplorerPlugin(Plugin):
    """Provides a tree view for Files and Folders. Opens selected item with mouse right-click."""
    datafile = property(lambda self: self.get_selected_datafile())
    defaults = {"opened": True,
                "docked": True
                }

    def __init__(self, application, controller=None):
        Plugin.__init__(self, application, default_settings=self.defaults)
        self.settings = application.settings._config_obj['Plugins']['File Explorer']
        self._parent = wx.App.Get().GetTopWindow()
        self._filemgr = self.filemgr
        self._filemgr.SetThemeEnabled(True)
        self._mgr = GetManager(self._filemgr)
        self._controller = controller

    def register_frame(self, parent=None):
        if parent:
            self._parent = parent

            if self._mgr.GetPane("file_manager") in self._mgr._panes:
                register = self._mgr.InsertPane
            else:
                register = self._mgr.AddPane

            register(self._filemgr, wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                     Caption("Files").LeftDockable(True).CloseButton(True))

            self._mgr.Update()

    def enable(self):
        self.register_action(ActionInfo('View','View File Explorer', self.OnShowFileExplorer,
                                        shortcut='F11',
                                        doc='Show File Explorer panel',
                                        position=1))
        # self.save_setting('opened', True)
        if self.opened:
            self.OnShowFileExplorer(None)

    def close_tree(self):
        self._mgr.DetachPane(self._filemgr)
        self._filemgr.Hide()
        self._mgr.Update()
        self.save_setting('opened', False)

    def disable(self):
        self.close_tree()
        # self.save_setting('opened', False)
        self.unsubscribe_all()
        self.unregister_actions()

    def is_focused(self):
        return self._filemgr.HasFocus()

    def OnShowFileExplorer(self, event):
        if not self._parent:
            self._parent = wx.App.Get().GetWindow()  # self.frame
        if not self._filemgr:  # This is not needed because file explorer is always created
            self._filemgr = FileExplorer(self._parent, self._controller)

        self._pane = self._mgr.GetPane(self._filemgr)
        HTML_BACKGROUND = self.settings.get('background help', (240, 242, 80))
        HTML_FOREGROUND = self.settings.get('foreground text', (7, 0, 70))
        HTML_FONT_FACE = self.settings.get('font face', '')
        HTML_FONT_SIZE = self.settings.get('font size', 11)
        self._filetreectrl = self._filemgr.GetTreeCtrl()
        self._filemgr.Show(True)
        self._filemgr.SetMinSize(wx.Size(200, 225))
        self._mgr.DetachPane(self._filemgr)
        self._mgr.AddPane(self.filemgr,
                          wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                          Caption("Files").LeftDockable(True).
                          CloseButton(True))
        self._filemgr.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self._filemgr.SetBackgroundColour(HTML_BACKGROUND)
        self._filemgr.SetForegroundColour(HTML_FOREGROUND)
        self.font = self._filemgr.GetFont()
        self.font.SetFaceName(HTML_FONT_FACE)
        self.font.SetPointSize(HTML_FONT_SIZE)
        self._filemgr.SetFont(self.font)
        self._filemgr.Refresh()
        self._filetreectrl.SetBackgroundColour(HTML_BACKGROUND)
        self._filetreectrl.SetForegroundColour(HTML_FOREGROUND)
        self._filetreectrl.SetFont(self.font)
        self._filetreectrl.Refresh()
        self._filemgr.Raise()
        self._mgr.Update()
        self.save_setting('opened', True)
        self._update_tree()

    def _update_tree(self):
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
