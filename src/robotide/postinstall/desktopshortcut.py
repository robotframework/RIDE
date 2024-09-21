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

import atexit
import builtins
import sys
import wx

from ..pluginapi import Plugin
from ..action import ActionInfo

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class ShortcutPlugin(Plugin):
    """Creator of RIDE Desktop Shortcuts."""

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={
            'desktop_shortcut_exists': False,
            'initial_project': None
        })
        self._window = None
        atexit.register(self._close)

    def _close(self):
        """ Just ignore it """
        pass

    def enable(self):
        self._create_menu()

    def disable(self):
        self.unregister_actions()
        if self._window:
            self._window.close(self.notebook)

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo(_('Tools'),
                                        _('Create RIDE Desktop Shortcut'),
                                        self.on_view_shortcut_create,
                                        position=85))

    def on_view_shortcut_create(self, event):
        __ = event
        self.call_creator(self.notebook)
        # self.disable()

    @staticmethod
    def call_creator(notebook):
        from . import caller
        return caller(notebook.GetParent(), sys.platform.lower())
