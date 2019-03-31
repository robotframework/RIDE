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

import wx
import atexit
import sys

from robotide.pluginapi import Plugin, ActionInfo
from robotide import widgets
from robotide.postinstall import __main__ as postinstall


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
        pass

    def enable(self):
        self._create_menu()

    def disable(self):
        self.unregister_actions()
        if self._window:
            self._window.close(self.notebook)

    def _create_menu(self):
        self.unregister_actions()
        self.register_action(ActionInfo('Tools',
                                        'Create RIDE Desktop Shortcut',
                                        self.OnViewShortcutCreate,
                                        position=85))

    def OnViewShortcutCreate(self, event):
        self.call_creator(self.notebook)
        # self.disable()

    def call_creator(self, notebook):
        return postinstall.caller(notebook.GetParent(), sys.platform.lower())