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
import sys
import wx

from contextlib import contextmanager

from robotide.namespace import Namespace
from robotide.controller import Project
from robotide.spec import librarydatabase
from robotide.ui import LoadProgressObserver
from robotide.ui.mainframe import RideFrame
from robotide import publish
from robotide import context, contrib
from robotide.context import coreplugins
from robotide.preferences import Preferences, RideSettings
from robotide.application.pluginloader import PluginLoader
from robotide.application.editorprovider import EditorProvider
from robotide.application.releasenotes import ReleaseNotes
from robotide.application.updatenotifier import UpdateNotifierController, \
    UpdateDialog
from robotide import utils


class RIDE(wx.App):

    def __init__(self, path=None, updatecheck=True):
        self._initial_path = path
        self._updatecheck = updatecheck
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
        self.frame.Show()
        self.editor = self._get_editor()
        self._load_data()
        self.frame.tree.populate(self.model)
        self.frame.tree.set_editor(self.editor)
        self._find_robot_installation()
        self._publish_system_info()
        if self._updatecheck:
            UpdateNotifierController(
                self.settings).notify_update_if_needed(UpdateDialog)
        wx.CallLater(200, ReleaseNotes(self).bring_to_front)
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
        from robotide.editor import EditorPlugin
        from robotide.editor.texteditor import TextEditorPlugin
        for pl in self._plugin_loader.plugins:
            maybe_editor = pl._plugin
            if (isinstance(maybe_editor, EditorPlugin) or
                isinstance(maybe_editor, TextEditorPlugin)) and \
                maybe_editor.__getattr__("_enabled"):
                return maybe_editor

    def _load_data(self):
        path = self._initial_path or self._get_latest_path()
        if path:
            observer = LoadProgressObserver(self.frame)
            self._controller.load_data(path, observer)

    def _find_robot_installation(self):
        output = utils.run_python_command(
            ['import robot; print(robot.__file__ + \", \" + robot.__version__)'])
        if utils.PY2:
            robot_found = "ImportError" not in output and output
        else:
            robot_found = b"ModuleNotFoundError" not in output and output
        if robot_found:
            # print("DEBUG: output: %s  strip: %s" % (output, output.strip().split(b", ")))
            rf_file, rf_version = output.strip().split(b", ")
            if utils.PY2:
                publish.RideLogMessage(
                    "Found Robot Framework version %s from %s." % (
                        rf_version, os.path.dirname(rf_file))).publish()
            else:
                publish.RideLogMessage(
                    "Found Robot Framework version %s from %s." % (
                        str(rf_version, 'utf-8'),
                        str(os.path.dirname(rf_file), 'utf-8'))).publish()
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
        from robotide.recentfiles import RecentFilesPlugin
        for pl in self.get_plugins():
            if isinstance(pl._plugin, RecentFilesPlugin):
                return pl._plugin

    def get_plugins(self):
        return self._plugin_loader.plugins

    def register_preference_panel(self, panel_class):
        '''Add the given panel class to the list of known preference panels'''
        self.preferences.add(panel_class)

    def unregister_preference_panel(self, panel_class):
        '''Remove the given panel class from the known preference panels'''
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
