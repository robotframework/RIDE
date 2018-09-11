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

from robotide.preferences import widgets


class SavingPreferences(widgets.PreferencesPanel):
    location = ('Saving',)
    title = 'Saving Preferences'

    def __init__(self, settings, *args, **kwargs):
        super(SavingPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self.SetSizer(wx.FlexGridSizer(cols=2))
        for editor in self._create_editors(settings):
            self._add_editor(editor)

    def _create_editors(self, settings):
        return [
            widgets.StringChoiceEditor(settings,
                'default file format',
                'Default file format:',
                ('txt', 'tsv', 'html', 'robot')
            ),
            widgets.StringChoiceEditor(settings,
                'txt format separator',
                'TXT format separator:',
                ('pipe', 'space')
            ),
            widgets.StringChoiceEditor(settings,
                'line separator',
                'Line separator:',
                ('native', 'CRLF', 'LF'),
                'Possible values are native (of current OS) CRLF (Windows) and LF (Unixy)'
            ),
            widgets.IntegerChoiceEditor(settings,
                'txt number of spaces',
                'Separating spaces',
                [str(i) for i in range(2, 11)],
                'Number of spaces between cells when saving in txt format'
            )
        ]

    def _add_editor(self, editor):
        self.Sizer.AddMany([editor.label(self), (editor.chooser(self),)])
        self.Sizer.AddMany([(editor.help(self), 0, wx.BOTTOM, 10),
                            wx.Window(self)])
