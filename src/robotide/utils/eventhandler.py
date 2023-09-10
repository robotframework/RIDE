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

IS_WINDOWS = os.sep == '\\'


def normalize_windows_path(path):
    return path.lower().replace('\\', '/') if IS_WINDOWS else path


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
        if path.startswith('\\\\') and IS_WINDOWS:
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
                    self._watched_path.add(normalize_windows_path(changing_file))
                    if IS_WINDOWS:  # Here we only add the file parent directory
                        changing_file = os.path.join(os.path.dirname(changing_file), '')
                    try:
                        self._fs_watcher.Add(changing_file)
                    except Exception as e:
                        print(e)
                try:
                    file_search = fs.FindNext()
                except AssertionError:
                    pass
            self._watched_path.add(normalize_windows_path(path))
            self._exclude_paths()
        else:
            self._watched_path.add(normalize_windows_path(path))  # Here we add the file path
            if IS_WINDOWS:
                path = os.path.join(os.path.dirname(path), '') # Here we only add the file parent directory
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
                            self._watched_path.remove(normalize_windows_path(changing_file))
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
                    self._watched_path.remove(normalize_windows_path(item))
                except KeyError:
                    pass
            else:
                if self._is_valid_file_format(item):
                    try:
                        self._watched_path.remove(normalize_windows_path(item))
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
                    self._excluded_path.add(normalize_windows_path(item))
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
                            self._excluded_path.add(normalize_windows_path(fs.URLToFileName(file_search)))
                        try:
                            file_search = fs.FindNext()
                        except AssertionError:
                            pass
                else:
                    if self._is_valid_file_format(item):
                        self._excluded_path.add(normalize_windows_path(item))
        else:
            if self._is_valid_file_format(path):
                self._excluded_path.add(normalize_windows_path(path))

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
        if os.path.isdir(new_path):
            norm_new_path = normalize_windows_path(os.path.join(new_path, ''))
            norm_new_dir = norm_new_path
        else:
            norm_new_path = normalize_windows_path(new_path)
            norm_new_dir = normalize_windows_path(os.path.join(os.path.dirname(new_path), ''))
        previous_path = event.GetPath()
        norm_previous_path = normalize_windows_path(previous_path)
        norm_previous_dir = normalize_windows_path(os.path.join(os.path.dirname(previous_path), ''))
        change_type = event.GetChangeType()

        def is_path_excluded(path):
            if path.endswith('/'):  # We assume it is normalized
                excluded_directories = set()
                for x in self._excluded_path:
                    if x.endswith('/'):
                        excluded_directories.add(x)
                if not excluded_directories:
                    return False
                for excluded in excluded_directories:
                    if path.startswith(excluded):
                        return True
            else:
                return path in self._excluded_path

        """ DEBUG
        def event_name(code):
            table = ['FSW_EVENT_MODIFY', 'FSW_EVENT_CREATE', 'FSW_EVENT_DELETE', 'FSW_EVENT_RENAME']
            value = 0
            if code == wx.FSW_EVENT_MODIFY:
                value = 0
            if code == wx.FSW_EVENT_CREATE:
                value = 1
            if code == wx.FSW_EVENT_DELETE:
                value = 2
            if code == wx.FSW_EVENT_RENAME:
                value = 3
            return table[value]

        print(f"\nDEBUG: eventhandler _is_mark_dirty_needed new_path={new_path} previous_path={previous_path}"
              f" change_type={change_type}=={event_name(change_type)}\n"
              f"norm_previous_path={norm_previous_path} norm_previous_dir={norm_previous_dir}\n"
              f" self._watched_path={self._watched_path} self._excluded_path={self._excluded_path}")
        """
        if change_type == wx.FSW_EVENT_MODIFY:
            if (not is_path_excluded(norm_new_dir) and not is_path_excluded(norm_previous_path)
                    and not is_path_excluded(norm_previous_dir)):
                if os.path.isfile(previous_path):
                    return self._is_valid_file_format(previous_path)
            return False

        if change_type == wx.FSW_EVENT_CREATE:
            if (is_path_excluded(norm_new_dir) or is_path_excluded(norm_previous_path)
                    or is_path_excluded(norm_previous_dir)):
                return False
            if os.path.isfile(new_path):
                return self._is_valid_file_format(new_path)
            elif os.path.isdir(new_path):
                return True
        elif change_type == wx.FSW_EVENT_DELETE:
            if is_path_excluded(norm_previous_path) or is_path_excluded(norm_previous_dir):
                return False
            if norm_previous_path in self._watched_path:
                # workspace root folder / suite file is deleted
                self._watched_path.remove(norm_previous_path)
                return True
            if norm_previous_dir in self._watched_path:
                # workspace root folder / suite file is deleted
                self._watched_path.remove(norm_previous_dir)
                return True
            # We need to check if it was a directory or a valid file, not possible to detect it was a directory
            if norm_previous_path.endswith(os.sep) or norm_previous_path == norm_previous_dir[:-1]:
                return True
            else:
                return self._is_valid_file_format(previous_path)
        elif change_type == wx.FSW_EVENT_RENAME:
            if is_path_excluded(norm_new_path) or is_path_excluded(norm_new_dir):
                return False
            if norm_previous_path in self._watched_path:
                # workspace root folder / suite file is renamed
                self._watched_path.remove(norm_previous_path)
                self._watched_path.add(norm_new_path)
                return True
            if self._is_valid_file_format(previous_path):  # Old name was valid file
                return True
            # We need to check if it is a directory or a valid file
            if os.path.isfile(new_path):
                return self._is_valid_file_format(new_path)
            elif os.path.isdir(new_path):
                return True
        else:
            return False

    @staticmethod
    def _is_valid_file_format(file_path):
        # only watch files with certain extensions
        suffixes = ('.robot', '.txt', '.resource', '.tsv')  # DEBUG: Make these extensions configurable
        return os.path.splitext(file_path)[-1].lower() in suffixes


RideFSWatcherHandler = _RideFSWatcherHandler()
