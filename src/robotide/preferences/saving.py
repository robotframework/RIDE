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
import textwrap

from robotide.preferences import PreferencesPanel, PreferencesComboBox
from robotide.widgets import HelpLabel


class SavingPreferences(PreferencesPanel):
    '''Preferences panel for general preferences'''
    location = ("Saving",)
    title = "Saving Preferences"
    def __init__(self, settings, *args, **kwargs):
        super(SavingPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self.SetSizer(wx.FlexGridSizer(rows=5, cols=2))
        self._add_saving_preference('TXT format separator:',
                                    'txt format separator',
                                    ('pipe', 'space'),
                                    )
        help = 'Possible values are native (of current OS), CRLF (Windows) and LF (Unixy)'
        self._add_saving_preference('Line separator:',
                                    'line separator',
                                    ('native', 'CRLF', 'LF'),
                                    help)


    def _add_saving_preference(self, label, setting_name, choices, help=''):
        combo = PreferencesComboBox(self, wx.ID_ANY,
                                    self._settings,
                                    key=setting_name,
                                    choices=choices
                                    )
        label = wx.StaticText(self, wx.ID_ANY, label)
        self.Sizer.AddMany([label, (combo,)])
        help = '\n'.join(textwrap.wrap(help, 60))
        if help:
            self.Sizer.AddMany([(HelpLabel(self, help), 0, wx.BOTTOM, 10), wx.Window(self)])
