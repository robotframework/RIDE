#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from datetime import datetime
from fnmatch import fnmatch
import os
from robotide.context import IS_WINDOWS
import wx
from .widgets import PreferencesPanel

class Excludes():

    def __init__(self, directory):
        self._settings_directory = directory
        self._exclude_file_path = os.path.join(self._settings_directory, 'excludes')

    def get_excludes(self, separator='\n'):
        return separator.join(self._get_excludes())

    def _get_excludes(self):
        with self._get_exclude_file('r') as exclude_file:
            if not exclude_file:
                return set()
            return set(exclude_file.read().split())

    def remove_path(self, path):
        path = self._normalize(path)
        excludes = self._get_excludes()
        self.write_excludes(set([e for e in excludes if e != path]))

    def write_excludes(self, excludes):
        excludes = [self._normalize(e) for e in excludes]
        with self._get_exclude_file(read_write='w') as exclude_file:
            for exclude in excludes:
                exclude_file.write("%s\n" % exclude)

    def update_excludes(self, new_excludes):
        excludes = self._get_excludes()
        self.write_excludes(excludes.union(new_excludes))

    def _get_exclude_file(self, read_write):
        if not os.path.exists(self._exclude_file_path) and read_write.startswith('r'):
            if not os.path.isdir(self._settings_directory):
                os.makedirs(self._settings_directory)
            return open(self._exclude_file_path, 'w+')
        if os.path.isdir(self._exclude_file_path):
            raise NameError('"%s" is a directory, not file' % self._exclude_file_path)
        try:
            return open(self._exclude_file_path, read_write)
        except IOError as e:
            raise e #TODO FIXME

    def contains(self, path, excludes=None):
        if not path:
            return False
        excludes = excludes or self._get_excludes()
        if len(excludes) < 1:
            return False
        path = self._normalize(path)
        excludes = [self._normalize(e) for e in excludes]
        return any(self._match(path, e) for e in excludes)

    def _match(self, path, e):
        if fnmatch(path, e):
            return True
        if path.startswith(e):
            return True

        return False

    def _normalize(self, path):
        path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        if os.path.isdir(path):
            path += os.sep
        return path


class ExcludePreferences(PreferencesPanel):
    location = ('Excludes')
    title = 'Excludes'

    def __init__(self, settings, *args, **kwargs):
        super(ExcludePreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._create_sizer()

    def _create_sizer(self):
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        self._add_text_box(sizer)
        self._add_button_and_status(sizer)
        self.SetSizer(sizer)

    def _add_text_box(self, sizer):
        self._text_box = wx.TextCtrl(self,
            style=wx.TE_MULTILINE,
            size=wx.Size(570, 100),
            value=self._settings.excludes.get_excludes())
        sizer.Add(self._text_box, proportion=wx.EXPAND)

    def _add_button_and_status(self, sizer):
        status_and_button_sizer = wx.GridSizer(rows=1, cols=2, hgap=10)
        status_and_button_sizer.Add(wx.Button(self, id=wx.ID_SAVE))
        self.Bind(wx.EVT_BUTTON, self.OnSave)
        self._status_label = wx.StaticText(self)
        status_and_button_sizer.Add(self._status_label)
        sizer.Add(status_and_button_sizer)

    def OnSave(self, event):
        text = self._text_box.GetValue()
        self._settings.excludes.write_excludes(set(text.split('\n')))
        self._status_label.SetLabel('Saved at %s' % datetime.now().strftime('%H:%M:%S'))



