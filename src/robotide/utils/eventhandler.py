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


class _RideFSWatcherHandler:

    def __init__(self):
        self._fs_watcher = None
        self._is_workspace_dirty = False
        self._initial_watched_path = None
        self._watched_path = set()
        self._excluded_path = set()

    def create_fs_watcher(self, path):
        if self._fs_watcher:
            return
        self._initial_watched_path = path
        try:
            self._fs_watcher = wx.FileSystemWatcher()
        except Exception as e:
            print(e)
            return
        self._fs_watcher.Bind(wx.EVT_FSWATCHER, self._on_fs_event)

    def start_listening(self, path):
        if self._initial_watched_path != path:
            self._initial_watched_path = path
        self.stop_listening()
        # on MSW, we get a popup from wxWidgets
        # (https://github.com/wxWidgets/wxWidgets/blob/master/src/msw/fswatcher.cpp#L165)
        # when the path is a network share, like for example WSL: \\wsl.localhost\docker-desktop\tmp\
        # We avoid the popup by ignoring it
        if path.startswith('\\\\') and os.sep == '\\':
            print(f"INFO: Not watching file system changes for path: {path}")
            return
        if os.path.isdir(path):
            # only watch folders
            # MSW do not support watch single file
            path = os.path.join(path, '')
            try:
                self._fs_watcher.AddTree(path)
            except Exception as e:
                print(e)
                return
            # Add all files to the monitoring list
            from wx import FileSystem
            fs = FileSystem()
            fs.ChangePathTo(path, True)
            # An assertion error happens when chinese chars named directories, so we try to ignore it
            # wx._core.wxAssertionError: C++ assertion "Assert failure" failed at ../src/common/unichar.cpp(65) in
            # ToHi8bit(): character cannot be converted to single byte
            file_search = None
            try:
                file_search = fs.FindFirst("*")
            except AssertionError:
                pass
            while file_search:
                if self._is_valid_file_format(file_search):
                    changing_file = fs.URLToFileName(file_search)
                    self._watched_path.add(changing_file)
                    try:
                        self._fs_watcher.Add(changing_file)
                    except Exception as e:
                        print(e)
                try:
                    file_search = fs.FindNext()
                except AssertionError:
                    pass
            self._watched_path.add(path)
            self._exclude_paths()
        else:
            self._watched_path.add(path)  # Here we add the file path
            # DEBUG path = os.path.join(os.path.dirname(path), '') # Here we only add the file parent directory
            try:
                self._fs_watcher.Add(path)
            except Exception as e:
                print(e)
                return
            self._exclude_paths()

    def stop_listening(self):
        self._is_workspace_dirty = False
        self._fs_watcher.RemoveAll()
        self._watched_path = set()

    def _exclude_paths(self):
        for item in self._excluded_path:
            if os.path.isdir(item):
                item = os.path.join(item, '')
                try:
                    self._fs_watcher.RemoveTree(item)
                except Exception:
                    pass
                # Remove all files to the monitoring list
                from wx import FileSystem
                fs = FileSystem()
                fs.ChangePathTo(item, True)
                file_search = None
                try:
                    file_search = fs.FindFirst("*")
                except AssertionError:
                    pass
                while file_search:
                    if self._is_valid_file_format(file_search):
                        changing_file = fs.URLToFileName(file_search)
                        try:
                            self._watched_path.remove(changing_file)
                        except KeyError:
                            pass
                        try:
                            self._fs_watcher.Remove(changing_file)
                        except Exception:
                            pass
                    try:
                        file_search = fs.FindNext()
                    except AssertionError:
                        pass
                try:
                    self._watched_path.remove(item)
                except KeyError:
                    pass
            else:
                if self._is_valid_file_format(item):
                    try:
                        self._watched_path.remove(item)
                    except KeyError:
                        pass
                    try:
                        self._fs_watcher.Remove(item)
                    except Exception:
                        pass

    def exclude_listening(self, path):
        self._excluded_path = set()
        if isinstance(path, list):
            for item in path:
                if os.path.isdir(item):
                    item = os.path.join(item, '')
                    self._excluded_path.add(item)
                    # Remove all files to the monitoring list
                    from wx import FileSystem
                    fs = FileSystem()
                    fs.ChangePathTo(item, True)
                    file_search = None
                    try:
                        file_search = fs.FindFirst("*")
                    except AssertionError:
                        pass
                    while file_search:
                        if self._is_valid_file_format(file_search):
                            self._excluded_path.add(fs.URLToFileName(file_search))
                        try:
                            file_search = fs.FindNext()
                        except AssertionError:
                            pass
                else:
                    if self._is_valid_file_format(item):
                        self._excluded_path.add(item)
        else:
            if self._is_valid_file_format(path):
                self._excluded_path.add(path)

    def is_workspace_dirty(self):
        if self._watched_path:
            return self._is_workspace_dirty
        else:
            return False

    def is_watcher_created(self):
        return self._fs_watcher is not None

    def get_workspace_new_path(self):
        return self._initial_watched_path  # Returning file or directory name

    def _on_fs_event(self, event):
        if self._is_mark_dirty_needed(event):
            self._is_workspace_dirty = True

    def _is_mark_dirty_needed(self, event):
        new_path = event.GetNewPath()
        previous_path = event.GetPath()
        change_type = event.GetChangeType()

        if change_type == wx.FSW_EVENT_MODIFY:
            if previous_path in self._watched_path and previous_path not in self._excluded_path:
                return True
            return False

        if change_type == wx.FSW_EVENT_CREATE:
            if previous_path in self._excluded_path:
                return False
            if os.path.isdir(previous_path):
                return True
            elif os.path.isfile(previous_path):
                return self._is_valid_file_format(previous_path)
        elif change_type == wx.FSW_EVENT_DELETE:
            if previous_path in self._excluded_path:
                return False
            if previous_path in self._watched_path:
                # workspace root folder / suite file is deleted
                self._watched_path.remove(previous_path)
                return True
            """ DEBUG: Why we are considering not monitored files or directories?
            if previous_path.endswith(os.sep):
                return True
            else:
                return self._is_valid_file_format(previous_path)
            """
        elif change_type == wx.FSW_EVENT_RENAME:
            if new_path in self._excluded_path:
                return False
            if previous_path in self._watched_path:
                # workspace root folder / suite file is renamed
                self._watched_path.remove(previous_path)
                self._watched_path.add(new_path)
                return True
            """ DEBUG: Why we are considering not monitored files or directories?
            if os.path.isdir(new_path):
                return True
            elif os.path.isfile(new_path):
                return self._is_valid_file_format(new_path)
            """
        else:
            return False

    @staticmethod
    def _is_valid_file_format(file_path):
        # only watch files with certain extensions
        suffixes = ('.robot', '.txt', '.resource', '.tsv')  # DEBUG: Make these extensions configurable
        return os.path.splitext(file_path)[-1].lower() in suffixes


RideFSWatcherHandler = _RideFSWatcherHandler()
