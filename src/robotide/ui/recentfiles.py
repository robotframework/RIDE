#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import os.path

from robotide.publish import RideOpenSuite
from robotide.ui import ActionInfo, SeparatorInfo
from robotide.plugin import Plugin



class RecentFilesPlugin(Plugin):
    """Add recently opened files to the file menu."""

    def __init__(self, application=None):
        settings = {'recent_files':[], 'max_number_of_files':4}
        Plugin.__init__(self, application, default_settings=settings)
        self._files = {}

    def enable(self):
        self._save_currently_loaded_suite()
        self._add_recent_files_to_menu()
        self.subscribe(self.OnSuiteOpened, RideOpenSuite)
        # TODO: This plugin doesn't currently support resources
        # self._frame.subscribe(self.OnSuiteOpened, ('core', 'open','resource'))

    def disable(self):
        self.unregister_actions()
        self.unsubscribe(self.OnSuiteOpened, RideOpenSuite)

    def OnOpenRecent(self, event):
        id = event.GetId()
        if not self.new_suite_can_be_opened():
            return
        path = self._normalize(self._files[id])
        # TODO: There needs to be a better way. This assumes the path is a
        # suite but it could be a resource. There needs to be a
        # generic 'open' command in the application or frame object
        # that Does The Right Thing no matter what the type.
        self.open_suite(path)

    def OnSuiteOpened(self, event):
        self._add_to_recent_files(event.path)

    def _get_file_menu(self):
        menubar = self.get_menu_bar()
        pos = menubar.FindMenu('File')
        file_menu = menubar.GetMenu(pos)
        return file_menu

    def _normalize(self, path):
        if os.path.basename(path).startswith('__init__.'):
            return os.path.dirname(path)
        return os.path.abspath(path)

    def _save_currently_loaded_suite(self):
        model = self.model
        if model and model.suite:
            self._add_to_recent_files(model.suite.source)

    def _add_to_recent_files(self, file):
        if not file:
            return
        file = self._normalize(file)
        if file not in self.recent_files:
            self.recent_files.insert(0, file)
            self.recent_files = self.recent_files[0:self.max_number_of_files]
            self.save_setting('recent_files', self.recent_files)
            self._update_file_menu()

    def _update_file_menu(self):
        self.unregister_actions()
        self._add_recent_files_to_menu()

    def _add_recent_files_to_menu(self):
        if len(self.recent_files) == 0:
            action = ActionInfo('File', 'No recent files')
            action.set_menu_position(before='Exit')
            self.register_action(action)
        else:
            for n, file in enumerate(self.recent_files):
                self._add_file_to_menu(file, n)
        sep = SeparatorInfo('File')
        sep.set_menu_position(before='Exit')
        self.register_action(sep)

    def _add_file_to_menu(self, file, n):
        item = self._normalize(file)
        filename = os.path.basename(file)
        label = '&%s: %s' % (n+1, filename)
        doc = 'Open %s' % item
        action_info = ActionInfo('File', label, self.OnOpenRecent, doc=doc)
        action_info.set_menu_position(before='Exit')
        id = self.register_action(action_info)
        self._files[id] = item
