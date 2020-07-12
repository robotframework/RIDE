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


class _RideFSWatcherHandler:

    def __init__(self):
        self._fs_watcher = None
        self._is_workspace_dirty = False
        self._watched_path = None

    def create_fs_watcher(self, path):
        if self._fs_watcher:
            return
        self._watched_path = path
        self._fs_watcher = wx.FileSystemWatcher()
        self._fs_watcher.Bind(wx.EVT_FSWATCHER, self._on_fs_event)

    def start_listening(self, path):
        self.stop_listening()
        if not os.path.exists(path):
            return
        if os.path.isdir(path):
            # only watch folders
            # MSW do not support watch single file
            path = os.path.join(path, '')
            self._fs_watcher.AddTree(path)
        self._watched_path = path

    def stop_listening(self):
        self._is_workspace_dirty = False
        self._fs_watcher.RemoveAll()
        self._watched_path = None

    def is_workspace_dirty(self):
        if self._watched_path:
            return self._is_workspace_dirty
        else:
            return True

    def is_watcher_created(self):
        return self._fs_watcher is not None

    def get_workspace_new_path(self):
        return self._watched_path

    def _on_fs_event(self, event):
        if self._is_mark_dirty_needed(event):
            self._is_workspace_dirty = True

    def _is_mark_dirty_needed(self, event):
        new_path = event.GetNewPath()
        previous_path = event.GetPath()
        change_type = event.GetChangeType()

        if change_type == wx.FSW_EVENT_CREATE:
            if os.path.isdir(previous_path):
                return True
            elif os.path.isfile(previous_path):
                return self._is_valid_file_format(previous_path)

        elif change_type == wx.FSW_EVENT_DELETE:
            if previous_path == self._watched_path:
                # workspace root folder / suite file is deleted
                self._watched_path = None
                return True

            if previous_path.endswith(os.sep):
                return True
            else:
                return self._is_valid_file_format(previous_path)

        elif change_type == wx.FSW_EVENT_RENAME:
            if previous_path == self._watched_path:
                # workspace root folder / suite file is renamed
                self._watched_path = new_path
                return True

            if os.path.isdir(new_path):
                return True
            elif os.path.isfile(new_path):
                return self._is_valid_file_format(new_path)
        else:
            return False

    @staticmethod
    def _is_valid_file_format(file_path):
        # only watch files with certain extensions
        suffixes = ('.robot', '.txt', '.resource', '.tsv')
        return os.path.splitext(file_path)[-1].lower() in suffixes


RideFSWatcherHandler = _RideFSWatcherHandler()
