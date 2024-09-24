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

import builtins
import wx

from ..context import IS_WINDOWS
from ..ui.preferences_dialogs import PreferencesPanel, IntegerChoiceEditor, StringChoiceEditor, boolean_editor
from wx import Colour

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class SavingPreferences(PreferencesPanel):
    location = (_('Saving'),)

    def __init__(self, settings, *args, **kwargs):
        self.location = (_('Saving'),)
        self.title = _('Saving')
        self.name = 'Saving'
        super(SavingPreferences, self).__init__(name_tr=_('Saving'), *args, **kwargs)
        self._settings = settings
        self.SetSizer(wx.FlexGridSizer(cols=2))
        self.background_color = Colour("light gray")
        self.foreground_color = Colour("black")
        for editor in self._create_editors(settings):
            self._add_editor(editor)
        label, selector = boolean_editor(self, settings, 'tasks', _("Is Task?"),
                                         _("Default for Tasks or Tests sections."))
        l_reformat, editor = boolean_editor(self, settings, 'reformat', _('Reformat?'),
                                            _('Should it recalculate identation on Save?'))
        if IS_WINDOWS:
            label.SetForegroundColour(self.foreground_color)
            label.SetBackgroundColour(self.background_color)
            # label.SetOwnBackgroundColour(self.background_color)
            # label.SetOwnForegroundColour(self.foreground_color)
            l_reformat.SetForegroundColour(self.foreground_color)
            l_reformat.SetBackgroundColour(self.background_color)
            # l_reformat.SetOwnBackgroundColour(self.background_color)
            # l_reformat.SetOwnForegroundColour(self.foreground_color)
        self.Sizer.AddMany([label, selector])
        self.Sizer.AddMany([l_reformat, editor])
        self.Sizer.Layout()
        self.Update()

    def _create_editors(self, settings):
        return [
            StringChoiceEditor(settings, 'default file format', _('Default file format:'),
                               ('txt', 'tsv', 'html', 'robot', 'resource')
                               ),
            StringChoiceEditor(settings, 'txt format separator', _('TXT format separator:'),
                               ('pipe', 'space')
                               ),
            StringChoiceEditor(settings, 'line separator', _('Line separator:'),
                               ('native', 'CRLF', 'LF'),
                               _('Possible values are native (of current OS) CRLF (Windows) and LF (Unixy)')
                               ),
            IntegerChoiceEditor(settings, 'txt number of spaces', _('Separating spaces'),
                                [str(i) for i in range(2, 11)],
                                _('Number of spaces between cells when saving in txt format')
                                )
        ]

    def _add_editor(self, editor):
        l_editor = editor.label(self)
        if IS_WINDOWS:
            l_editor.SetForegroundColour(self.foreground_color)
            l_editor.SetBackgroundColour(self.background_color)
            # l_editor.SetOwnBackgroundColour(self.background_color)
            # l_editor.SetOwnForegroundColour(self.foreground_color)
        self.Sizer.AddMany([l_editor, (editor.chooser(self),)])
        self.Sizer.AddMany([(editor.help(self), 0, wx.BOTTOM, 10), wx.Window(self)])
