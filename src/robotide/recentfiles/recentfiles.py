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

import builtins
import os.path

import wx

from ..pluginapi import Plugin
from ..action import ActionInfo, SeparatorInfo
from ..publish import RideOpenSuite, RideFileNameChanged
from ..publish.messages import RideNewProject, RideSaved

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


def normalize_path(path):
    if os.path.basename(path).startswith('__init__.'):
        return os.path.dirname(path)
    return os.path.abspath(path)


def remove_non_existing_paths(paths):
    return [f for f in paths if os.path.exists(f)]


class RecentFilesPlugin(Plugin):
    __doc__ = _("""Add recently opened files to the file menu.""")

    def __init__(self, application=None):
        settings = {'recent_files': [], 'max_number_of_files': 4}
        Plugin.__init__(self, application, default_settings=settings)
        self.recent_files = remove_non_existing_paths(self.recent_files)
        self._new_project_path = None

    def enable(self):
        self._save_currently_loaded_suite()
        self._add_recent_files_to_menu()
        self._new_project_path = None
        self.subscribe(self.on_suite_opened, RideOpenSuite)
        self.subscribe(self.on_file_name_changed, RideFileNameChanged)
        self.subscribe(self.on_new_project_opened, RideNewProject)
        self.subscribe(self.on_saved, RideSaved)

    def disable(self):
        self.unregister_actions()
        self.unsubscribe_all()

    def on_suite_opened(self, message):
        # Update menu with CallAfter to ensure ongoing menu selection
        # handling has finished before menu is changed
        wx.CallAfter(self._add_to_recent_files, message.path)
        self._new_project_path = None

    def on_file_name_changed(self, message):
        self._new_project_path = None
        if not message.old_filename:
            return
        old_filename = normalize_path(message.old_filename)
        new_filename = normalize_path(message.datafile.filename)
        if old_filename not in self.recent_files:
            return
        index = self.recent_files.index(old_filename)
        self.recent_files[index] = new_filename
        self._save_settings_and_update_file_menu()

    def on_new_project_opened(self, message):
        self._new_project_path = message.path

    def on_saved(self, message):
        _ = message
        if self._new_project_path is not None:
            wx.CallAfter(self._add_to_recent_files, self._new_project_path)
            self._new_project_path = None

    def _get_file_menu(self):
        menubar = self.get_menu_bar()
        pos = menubar.FindMenu('File')
        file_menu = menubar.GetMenu(pos)
        return file_menu

    def _save_currently_loaded_suite(self):
        model = self.model
        if model and model.suite:
            self._add_to_recent_files(model.suite.source)

    def _add_to_recent_files(self, path):
        if not path:
            return
        path = normalize_path(path)
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self._save_settings_and_update_file_menu()

    def _save_settings_and_update_file_menu(self):
        self.recent_files = remove_non_existing_paths(self.recent_files)
        self.recent_files = self.recent_files[:self.max_number_of_files]
        self.save_setting('recent_files', self.recent_files)
        self.unregister_actions()
        self._add_recent_files_to_menu()

    def _add_recent_files_to_menu(self):
        if not self.recent_files:
            action = ActionInfo(_('File'), _('No recent files'))
            action.set_menu_position(before=_('Exit'))
            self.register_action(action)
        else:
            for n, path in enumerate(self.recent_files):
                self._add_file_to_menu(path, n)
        sep = SeparatorInfo(_('File'))
        sep.set_menu_position(before=_('Exit'))
        self.register_action(sep)

    def _add_file_to_menu(self, path, n):
        entry = RecentFileEntry(n+1, path, self)
        self.register_action(entry.get_action_info())


class RecentFileEntry(object):

    def __init__(self, index, file, plugin):
        self.file = file
        self.index = index
        self.path = normalize_path(self.file)
        self.filename = os.path.basename(file)
        self.plugin = plugin
        self.label = '&%s: %s' % (index, self.filename)
        self.doc = _('Open %s') % self.path

    def on_open_recent(self, event):
        __ = event
        if not self.plugin.frame.check_unsaved_modifications():
            return
        self.plugin.open_suite(self.path)

    def get_action_info(self):
        action_info = ActionInfo(_('File'), self.label, self.on_open_recent,
                                 doc=self.doc)
        action_info.set_menu_position(before=_('Exit'))
        return action_info
