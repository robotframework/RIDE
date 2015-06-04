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
import textwrap

from .widgets import (PreferencesPanel, PreferencesComboBox,
                      IntegerPreferenceComboBox)
from robotide.widgets import HelpLabel


class _ChoiceEditor(object):
    _editor_class = None

    def __init__(self, settings, setting_name, label, choices, help=''):
        self._settings = settings
        self._setting_name = setting_name
        self._label = label
        self._choices = choices
        self._help = help

    def chooser(self, parent):
        return self._editor_class(parent, wx.ID_ANY, self._settings,
                                  key=self._setting_name, choices=self._choices)

    def label(self, parent):
        return wx.StaticText(parent, wx.ID_ANY, self._label)

    def help(self, parent):
        return HelpLabel(parent, '\n'.join(textwrap.wrap(self._help, 60)))


class StringChoiceEditor(_ChoiceEditor):
    _editor_class = PreferencesComboBox


class IntegerChoiceEditor(_ChoiceEditor):
    _editor_class = IntegerPreferenceComboBox


class SavingPreferences(PreferencesPanel):
    location = ('Saving',)
    title = 'Saving Preferences'

    def __init__(self, settings, *args, **kwargs):
        super(SavingPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self.SetSizer(wx.FlexGridSizer(rows=7, cols=2))
        for editor in self._create_editors(settings):
            self._add_editor(editor)

    def _create_editors(self, settings):
        return [
            StringChoiceEditor(settings,
                'default file format',
                'Default file format:',
                ('txt', 'tsv', 'html', 'robot')
            ),
            StringChoiceEditor(settings,
                'txt format separator',
                'TXT format separator:',
                ('pipe', 'space')
            ),
            StringChoiceEditor(settings,
                'line separator',
                'Line separator:',
                ('native', 'CRLF', 'LF'),
                'Possible values are native (of current OS) CRLF (Windows) and LF (Unixy)'
            ),
            IntegerChoiceEditor(settings,
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
