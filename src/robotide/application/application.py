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

import os
import wx
import locale
locale.setlocale(locale.LC_ALL, 'C')

from contextlib import contextmanager

from ..namespace import Namespace
from ..controller import Project
from ..spec import librarydatabase
from ..ui import LoadProgressObserver
from ..ui.mainframe import RideFrame
from .. import publish
from .. import context, contrib
from ..context import coreplugins
from ..preferences import Preferences, RideSettings
from ..application.pluginloader import PluginLoader
from ..application.editorprovider import EditorProvider
from ..application.releasenotes import ReleaseNotes
from ..application.updatenotifier import UpdateNotifierController, UpdateDialog
from ..ui.treeplugin import TreePlugin
from ..ui.fileexplorerplugin import FileExplorerPlugin
from ..utils import RideFSWatcherHandler, run_python_command


class RIDE(wx.App):

    def __init__(self, path=None, updatecheck=True):
        self._updatecheck = updatecheck
        self.workspace_path = path
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        # DEBUG To test RTL
        # self._initial_locale = wx.Locale(wx.LANGUAGE_ARABIC)
        self._initial_locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        # Needed for SetToolTipString to work
        wx.HelpProvider.Set(wx.SimpleHelpProvider())  # TODO adjust to wx versions 
        self.settings = RideSettings()
        librarydatabase.initialize_database()
        self.preferences = Preferences(self.settings)
        self.namespace = Namespace(self.settings)
        self._controller = Project(self.namespace, self.settings)
        self.frame = RideFrame(self, self._controller)
        self._editor_provider = EditorProvider()
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           coreplugins.get_core_plugins())
        self._plugin_loader.enable_plugins()
        perspective = self.settings.get('AUI Perspective', None)
        if perspective:
            self.frame._mgr.LoadPerspective(perspective, True)
        self.treeplugin = TreePlugin(self)
        if self.treeplugin.settings['_enabled']:
            self.treeplugin.register_frame(self.frame)
        self.fileexplorerplugin = FileExplorerPlugin(self, self._controller)
        if self.fileexplorerplugin.settings['_enabled']:
            self.fileexplorerplugin.register_frame(self.frame)
        self.frame.Show()
        if not self.treeplugin.opened:
            self.treeplugin.close_tree()
        if not self.fileexplorerplugin.opened:
            self.fileexplorerplugin.close_tree()
        self.editor = self._get_editor()
        self._load_data()
        self.treeplugin.populate(self.model)
        self.treeplugin.set_editor(self.editor)
        self._find_robot_installation()
        self._publish_system_info()
        if self._updatecheck:
            UpdateNotifierController(self.settings).notify_update_if_needed(UpdateDialog)
        wx.CallLater(200, ReleaseNotes(self).bring_to_front)
        wx.CallLater(200, self.fileexplorerplugin._update_tree)
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnAppActivate)
        return True

    def _publish_system_info(self):
        publish.RideLogMessage(context.SYSTEM_INFO).publish()

    @property
    def model(self):
        return self._controller

    def _get_plugin_dirs(self):
        return [self.settings.get_path('plugins'),
                os.path.join(self.settings['install root'], 'site-plugins'),
                contrib.CONTRIB_PATH]

    def _get_editor(self):
        from ..editor import EditorPlugin
        from ..editor.texteditor import TextEditorPlugin
        for pl in self._plugin_loader.plugins:
            maybe_editor = pl._plugin
            if (isinstance(maybe_editor, EditorPlugin) or
                isinstance(maybe_editor, TextEditorPlugin)) and \
                maybe_editor.__getattr__("_enabled"):
                return maybe_editor

    def _load_data(self):
        self.workspace_path = self.workspace_path or self._get_latest_path()
        if self.workspace_path:
            self._controller.update_default_dir(self.workspace_path)
            observer = LoadProgressObserver(self.frame)
            self._controller.load_data(self.workspace_path, observer)

    def _find_robot_installation(self):
        output = run_python_command(
            ['import robot; print(robot.__file__ + \", \" + robot.__version__)'])
        robot_found = b"ModuleNotFoundError" not in output and output
        if robot_found:
            rf_file, rf_version = output.strip().split(b", ")
            publish.RideLogMessage("Found Robot Framework version %s from %s." % (
                str(rf_version, 'utf-8'), str(os.path.dirname(rf_file), 'utf-8'))).publish()
            return rf_version
        else:
            publish.RideLogMessage(
                publish.get_html_message('no_robot'), notify_user=True
            ).publish()

    def _get_latest_path(self):
        recent = self._get_recentfiles_plugin()
        if not recent or not recent.recent_files:
            return None
        return recent.recent_files[0]

    def _get_recentfiles_plugin(self):
        from ..recentfiles import RecentFilesPlugin
        for pl in self.get_plugins():
            if isinstance(pl._plugin, RecentFilesPlugin):
                return pl._plugin

    def get_plugins(self):
        return self._plugin_loader.plugins

    def register_preference_panel(self, panel_class):
        """Add the given panel class to the list of known preference panels"""
        self.preferences.add(panel_class)

    def unregister_preference_panel(self, panel_class):
        """Remove the given panel class from the known preference panels"""
        self.preferences.remove(panel_class)

    def register_editor(self, object_class, editor_class, activate):
        self._editor_provider.register_editor(object_class, editor_class,
                                              activate)

    def unregister_editor(self, object_class, editor_class):
        self._editor_provider.unregister_editor(object_class, editor_class)

    def activate_editor(self, object_class, editor_class):
        self._editor_provider.set_active_editor(object_class, editor_class)

    def get_editors(self, object_class):
        return self._editor_provider.get_editors(object_class)

    def get_editor(self, object_class):
        return self._editor_provider.get_editor(object_class)

    @contextmanager
    def active_event_loop(self):
        # With wxPython 2.9.1, ProgressBar.Pulse breaks if there's no active
        # event loop.
        # See http://code.google.com/p/robotframework-ride/issues/detail?id=798
        loop = wx.EventLoop()
        wx.EventLoop.SetActive(loop)
        yield
        del loop

    def OnEventLoopEnter(self, loop):
        if loop and wx.EventLoopBase.IsMain(loop):
            RideFSWatcherHandler.create_fs_watcher(self.workspace_path)

    def OnAppActivate(self, event):
        if self.workspace_path is not None and RideFSWatcherHandler.is_watcher_created():
            if event.GetActive():
                if self._controller.is_project_changed_from_disk() or \
                        RideFSWatcherHandler.is_workspace_dirty():
                    self.frame.show_confirm_reload_dlg(event)
                RideFSWatcherHandler.stop_listening()
            else:
                RideFSWatcherHandler.start_listening(self.workspace_path)
        event.Skip()
