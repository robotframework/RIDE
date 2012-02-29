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
        self._create_editor(SETTINGS, 'auto imports', 'Comma separated list of libraries to be automatically imported.')
        self._create_editor(SETTINGS, 'pythonpath', 'Comma separated list of directories to be added to PYTHONPATH when libraries are searched.')

    def _create_editor(self, settings, setting_name, help_text):
        sizer = HorizontalSizer()
        sizer.add_with_padding(self._label_for(setting_name))
        sizer.add(self._editor_for(setting_name), proportion=1)
        self.Sizer.Add(sizer, flag=wx.EXPAND)
        self.Sizer.add_with_padding(HelpLabel(self, help_text))

    def _label_for(self, setting_name):
        label = ('%s: ' % setting_name).capitalize()
        return Label(self, label=label)

    def _editor_for(self, setting_name):
        initial_value = ', '.join(SETTINGS[setting_name])
        editor = TextField(self, initial_value)
        def set_value(event):
            value = [name.strip() for name in editor.GetValue().split(',')]
            SETTINGS.set(setting_name, value)
        editor.Bind(wx.EVT_TEXT, set_value)
        return editor
