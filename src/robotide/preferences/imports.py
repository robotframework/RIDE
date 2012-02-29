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

import wx

from robotide.context import SETTINGS
from robotide.widgets import Label, TextField, VerticalSizer, HorizontalSizer, HelpLabel

from .widgets import PreferencesPanel


class ImportPreferences(PreferencesPanel):
    location = ('Importing')
    title = 'Automatic imports and PYTHONPATH'
    def __init__(self, parent):
        super(PreferencesPanel, self).__init__(parent)
        self.SetSizer(VerticalSizer())
        self._settings = [
            Setting('auto imports', 'Comma separated list of libraries to be automatically imported.'),
            Setting('pythonpath', 'Comma separated list of directories to be added to PYTHONPATH when libraries are searched.')
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
        initial_value = ', '.join(setting.current_value)
        editor = TextField(self, initial_value)
        editor.Bind(wx.EVT_TEXT, lambda evt: setting.set(editor.GetValue()))
        return editor

    def close(self):
        for s in self._settings:
            s.publish()


class Setting(object):

    def __init__(self, name, help):
        self.name = name
        self.help = help
        self._original_value = SETTINGS[name]
        self.current_value = self._original_value

    def set(self, new_value):
        self.current_value = [token.strip() for token in new_value.split(',')]

    def publish(self):
        SETTINGS.set(self.name, self.current_value)
        SETTINGS.notify(self.name, self._original_value, self.current_value)
