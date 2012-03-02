#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org:licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import with_statement
import os
import wx
from contextlib import contextmanager
from robotide.application.updatenotifier import UpdateNotifierController, UpdateDialog
from robotide.context import SETTINGS

from robotide.namespace import Namespace
from robotide.controller import ChiefController
from robotide.ui import RideFrame, LoadProgressObserver
from robotide.pluginapi import RideLogMessage
from robotide import context, contrib

from pluginloader import PluginLoader
from editorprovider import EditorProvider


class RIDE(wx.App):

    def __init__(self, path=None, updatecheck=True):
        self._initial_path = path
        self._updatecheck = updatecheck
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        self.namespace = Namespace()
        self._controller = ChiefController(self.namespace)
        self.frame = RideFrame(self, self._controller)
        self._editor_provider = EditorProvider()
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           context.get_core_plugins())
        self._plugin_loader.enable_plugins()
        self.editor = self._get_editor()
        self.editor.show()
        self._load_data()
        self.frame.tree.populate(self.model)
        self.frame.tree.set_editor(self.editor)
        self._publish_system_info()
        if self._updatecheck:
            UpdateNotifierController(SETTINGS).notify_update_if_needed(UpdateDialog)
        wx.CallLater(200, self._get_release_notes().bring_to_front)
        return True

    def _publish_system_info(self):
        RideLogMessage(context.SYSTEM_INFO).publish()

    @property
    def model(self):
        return self._controller

    def _get_plugin_dirs(self):
        return [context.SETTINGS.get_path('plugins'),
                os.path.join(context.SETTINGS['install root'], 'site-plugins'),
                contrib.CONTRIB_PATH]

    def _get_editor(self):
        from robotide.editor import EditorPlugin
        for pl in self._plugin_loader.plugins:
            if isinstance(pl._plugin, EditorPlugin):
                return pl._plugin

    def _get_release_notes(self):
        from .releasenotes import ReleaseNotesPlugin
        for pl in self._plugin_loader.plugins:
            if isinstance(pl._plugin, ReleaseNotesPlugin):
                return pl._plugin

    def _load_data(self):
        if self._initial_path:
            with self.active_event_loop():
                observer = LoadProgressObserver(self.frame)
                self._controller.load_data(self._initial_path, observer)

    def get_plugins(self):
        return self._plugin_loader.plugins

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
