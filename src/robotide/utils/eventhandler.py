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
import os
from robotide.context import IS_WINDOWS

class _RideFSWatcherHandler:

    _TYPE_ATTRIBUTE = 32
    _TYPE_CREATE = 1
    _TYPE_DELETE = 2
    _TYPE_RENAME = 4

    def __init__(self):
        self._fs_watcher = None
        self._is_workspace_dirty = False
        self._watched_path = None

    def create_fs_watcher(self):
        if self._fs_watcher:
            return
        self._fs_watcher = wx.FileSystemWatcher()
        self._fs_watcher.Bind(wx.EVT_FSWATCHER, self._on_fs_event)

    def start_listening(self, path):
        self.stop_listening()
        path = os.path.join(path, '')
        if os.path.isdir(path):
            self._fs_watcher.AddTree(path)
        else:
            self._fs_watcher.Add(path)
        self._watched_path = path

    def stop_listening(self):
        self._is_workspace_dirty = False
        self._fs_watcher.RemoveAll()

    def is_workspace_dirty(self):
        if self._is_workspace_dirty and IS_WINDOWS:
            # for windows, rename workspace cannot be detected
            # use this workaround if watched path not exists
            if not os.path.exists(self._watched_path):
                self._is_workspace_dirty = False
        return self._is_workspace_dirty

    def is_watcher_created(self):
        return self._fs_watcher is not None

    def get_workspace_new_path(self):
        return self._watched_path

    def _on_fs_event(self, event):
        # TODO skip access / attribute event
        new_path = event.GetNewPath()
        previous_path = event.GetPath()
        change_type = event.GetChangeType()

        if change_type == _RideFSWatcherHandler._TYPE_ATTRIBUTE:
            return

        if os.path.isdir(previous_path) or os.path.isdir(new_path):
            self._is_workspace_dirty = True
            return

        if previous_path.endswith(os.sep) and change_type == _RideFSWatcherHandler._TYPE_DELETE:
            # folder is deleted:
            self._is_workspace_dirty = True
            if previous_path == self._watched_path:
                # current workspace folder has been removed
                self._watched_path = None
            return

        # only watch files with certain extensions
        suffixes = ('.robot', '.txt', '.resource', '.tsv')
        if os.path.splitext(previous_path)[-1].lower() in suffixes:
            self._is_workspace_dirty = True


RideFSWatcherHandler = _RideFSWatcherHandler()
