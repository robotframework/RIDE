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
import ConfigParser
import wx
from os.path import abspath, dirname, join

from robotide.preferences import PreferencesPanel, PreferencesColorPicker
from robotide.preferences.saving import IntegerChoiceEditor


class ColorPreferences(PreferencesPanel):

    def __init__(self, font_label, font_setting_key, settings, *args, **kwargs):
        super(ColorPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        # N.B. There really ought to be a "reset colors to defaults"
        # button, in case the user gets things hopelessly mixed up

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.

        font_size_sizer = self._create_font_size_sizer(settings, font_setting_key, font_label)
        colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=2, cols=1, hgap=10)
        main_sizer.Add(font_size_sizer)
        main_sizer.Add(colors_sizer)
        self.SetSizer(main_sizer)

    def _create_font_size_sizer(self, settings, settings_key, title='Font Size'):
        f = IntegerChoiceEditor(settings,
                                settings_key,
                                title,
                                [str(i) for i in range(8, 49)]
        )
        font_size_sizer = wx.FlexGridSizer(rows=1, cols=1)
        font_size_sizer.AddMany([f.label(self), (f.chooser(self),)])
        return font_size_sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')

class TextEditColorPreferences(ColorPreferences):
    location = ("Text Edit Colors and Font Size",)
    title = "Text Edit Colors and Font Size"

    def __init__(self, settings, *args, **kwargs):
        self._color_pickers = [] # must be before super class constructor call
        super(TextEditColorPreferences, self).__init__('Text Edit Font Size',
                                                       'text edit font size', settings, *args, **kwargs)


    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        for settings_key, label_text in (
            ('argument',  'Argument foreground'),
            ('comment', 'Comment foreground'),
            ('error',  'Error foreground'),
            ('gherkin', 'Gherkin keyword foreground'),
            ('heading', 'Heading foreground'),
            ('import', 'Import foreground'),
            ('separator', 'Separator'),
            ('setting',  'Setting foreground'),
            ('syntax', 'Syntax characters'),
            ('tc_kw_name', 'Keyword definition foreground'),
            ('variable',  'Variable foreground'),
        ):
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            button = PreferencesColorPicker(self, wx.ID_ANY, self._settings['Text Edit Colors'], settings_key)
            container.Add(button, (row, column), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=4)
            column += 1
        reset = wx.Button(self, wx.ID_ANY, 'Reset colors to default')
        self.Bind(wx.EVT_BUTTON, self.OnReset)
        container.Add(reset, (row + 1, 0))
        return container

    def OnReset(self, event):
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])

    def _read_defaults(self):
        settings = [s.strip() for s in open(self._get_path(), 'r').readlines()]
        start_index = settings.index('[Text Edit Colors]') + 1
        defaults = {}
        for line in settings[start_index:]:
            if line.startswith('['):
                break
            if not line:
                continue
            key, value = [s.strip().strip('\'') for s in line.split("=")]
            defaults[key] = value
        return defaults

    def _get_path(self):
        return join(dirname(abspath(__file__)), 'settings.cfg')


class GridColorPreferences(ColorPreferences):
    location = ("Grid Colors and Font Size",)
    title = "Grid Colors and Font Size"

    def __init__(self, settings, *args, **kwargs):
        super(GridColorPreferences, self).__init__('Grid Font Size', 'font size', settings, *args, **kwargs)

    def create_colors_sizer(self):
        colors_sizer = wx.GridBagSizer()
        self._create_foreground_pickers(colors_sizer)
        self._create_background_pickers(colors_sizer)
        return colors_sizer

    def _create_foreground_pickers(self, colors_sizer):
        row = 0
        for key, label in (
            ('text user keyword', 'User Keyword Foreground'),
            ('text library keyword', 'Library Keyword Foreground'),
            ('text commented', 'Comments Foreground'),
            ('text variable', 'Variable Foreground'),
            ('text string', 'Default Foreground'),
            ('text empty', 'Empty Foreground'),
        ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            btn = PreferencesColorPicker(self, wx.ID_ANY, self._settings['Grid Colors'], key)
            colors_sizer.Add(btn, (row, 0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
            row += 1

    def _create_background_pickers(self, colors_sizer):
        row = 0
        for key, label in (
            ('background assign', 'Variable Background'),
            ('background keyword', 'Keyword Background'),
            ('background mandatory', 'Mandatory Field Background'),
            ('background optional', 'Optional Field Background'),
            ('background must be empty', 'Mandatory Empty Field Background'),
            ('background unknown', 'Unknown Background'),
            ('background error', 'Error Background'),
            ('background highlight', 'Highlight Background')
        ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            btn = PreferencesColorPicker(self, wx.ID_ANY, self._settings['Grid Colors'], key)
            colors_sizer.Add(btn, (row, 2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
            row += 1