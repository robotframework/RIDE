#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import os
import sys
import wx

from robotide.robotapi import ROBOT_VERSION
from robotide.namespace import Namespace
from robotide.controller import ChiefController
from robotide.ui import RideFrame, LoadProgressObserver
from robotide import context

from pluginloader import PluginLoader
from editorprovider import EditorProvider


class RIDE(wx.App):

    def __init__(self, path=None):
        self._initial_path = path
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        self._check_robot_version()
        self.namespace = Namespace()
        self._controller = ChiefController(self.namespace)
        self.frame = RideFrame(self, self._controller)
        self._editor_provider = EditorProvider()
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           context.get_core_plugins())
        self._plugin_loader.enable_plugins()
        self._load_data()
        self.frame.tree.populate(self.model)
        return True

    def _check_robot_version(self):
        if ROBOT_VERSION < '2.5':
            context.LOG.error('You are using an old version (%s) of Robot Framework.\n\n'
                              'RIDE does not work correctly with this version. '
                              'Please upgrade to Robot Framework 2.5 or newer from\n'
                              'http://robotframework.org/.' % ROBOT_VERSION)
            sys.exit(1)

    @property
    def model(self):
        return self._controller

    def _get_plugin_dirs(self):
        return [context.SETTINGS.get_path('plugins'),
                os.path.join(context.SETTINGS['install root'], 'site-plugins')]

    def _load_data(self):
        if self._initial_path:
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
