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
from wx.lib.agw import customtreectrl
from wx.lib.agw.aui import GetManager
from robotide.pluginapi import Plugin, ActionInfo
from robotide.controller import Project


class FileExplorerPlugin(Plugin):
    """Provides a tree view for Files and Folders. Opens selected item with mouse right-click."""
    datafile = property(lambda self: self.get_selected_datafile())
    defaults = {"opened": True,
                "docked": True
                }

    def __init__(self, application, controller=None):
        Plugin.__init__(self, application, default_settings=self.defaults)
        self.settings = application.settings._config_obj['Plugins']['File Explorer']
        self._parent = None
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
            self._parent = self.frame
        if not self._filemgr:  # This is not needed because file explorer is always created
            self._filemgr = FileExplorer(self._parent, self._controller)

        self._pane = self._mgr.GetPane(self._filemgr)
        self._filemgr.Show(True)
        self._mgr.DetachPane(self._filemgr)
        self._mgr.AddPane(self.filemgr,
                          wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                          Caption("Files").LeftDockable(True).
                          CloseButton(True))
        self._filemgr.Raise()
        self._filemgr.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self._filemgr.SetBackgroundColour('white')  # TODO get background color from def
        self._filemgr.Refresh()
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
        self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self.SetBackgroundColour('white')  # TODO get background color from def
        self.Refresh()

    def update_tree(self):
        if isinstance(self._controller, Project):
            # print("DEBUG: FileExplorer called _update_tree")
            if self._controller.data and len(self._controller.data.directory) > 1:
                self.SelectPath(self._controller.data.source)
                try:
                    self.ExpandPath(self._controller.data.source)
                except Exception:
                    pass
                self.Refresh()
                self.Update()
