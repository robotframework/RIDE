#  Copyright 2008-2015 Nokia Solutions and Networks
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

from robotide.widgets import (
    Label, TextField, VerticalSizer, HorizontalSizer, HelpLabel)

from .widgets import PreferencesPanel


class ImportPreferences(PreferencesPanel):
    location = ('Importing')
    title = 'Automatic imports and PYTHONPATH'

    def __init__(self, parent, settings):
        super(PreferencesPanel, self).__init__(parent)
        self.SetSizer(VerticalSizer())
        self._settings = [
            Setting(settings, 'auto imports',
                    'Comma separated list of libraries to be automatically imported.'),
            Setting(settings, 'pythonpath',
                    'Comma separated list of directories to be added to PYTHONPATH when libraries are searched.'),
            Setting(settings, 'library xml directories',
                    'Directories to search for library xml files')
        ]
        for s in self._settings:
            self._create_editor(s)

    def _create_editor(self, setting):
        sizer = HorizontalSizer()
        sizer.add_with_padding(self._label_for(setting))
        sizer.add(self._editor_for(setting), proportion=1)
        self.Sizer.Add(sizer, flag=wx.EXPAND)
        self.Sizer.add_with_padding(HelpLabel(self, setting.help))

    def _label_for(self, setting):
        label = ('%s: ' % setting.name).capitalize()
        return Label(self, label=label)

    def _editor_for(self, setting):
        initial_value = ', '.join(setting.original_value)
        editor = TextField(self, initial_value)
        editor.Bind(wx.EVT_KILL_FOCUS, lambda evt: setting.set(editor.GetValue()))
        return editor


class Setting(object):

    def __init__(self, settings, name, help):
        self._settings = settings
        self.name = name
        self.help = help
        self.original_value = settings[name]

    def set(self, new_value):
        self._settings[self.name] = \
            [token.strip() for token in new_value.split(',') if token.strip()]
