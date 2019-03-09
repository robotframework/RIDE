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

import wx
from wx.lib.masked import NumCtrl
from os.path import abspath, dirname, join

from robotide.preferences import widgets
from robotide.widgets import Label


class EditorPreferences(widgets.PreferencesPanel):

    def __init__(self, settings, *args, **kwargs):
        super(EditorPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        # N.B. There really ought to be a "reset colors to defaults"
        # button, in case the user gets things hopelessly mixed up

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.

        font_editor = self._create_font_editor()
        colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        main_sizer.Add(font_editor)
        main_sizer.Add(colors_sizer)
        self.SetSizer(main_sizer)

    def _create_font_editor(self):
        f = widgets.IntegerChoiceEditor(
            self._settings, 'font size', 'Font Size',
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=30)
        sizer.AddMany([f.label(self), f.chooser(self)])
        if 'fixed font' in self._settings:
            sizer.AddMany(widgets.boolean_editor(
                self, self._settings, 'fixed font', 'Use fixed width font'))
        return sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')


class TextEditorPreferences(EditorPreferences):
    location = ("Text Editor",)
    title = "Text Editor Settings"

    def __init__(self, settings, *args, **kwargs):
        self._color_pickers = []  # must be before super class constructor call
        super(TextEditorPreferences, self).__init__(
            settings['Text Edit'], *args, **kwargs)

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
            button = widgets.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, settings_key)
            container.Add(button, (row, column),
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column),
                          flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
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
        start_index = settings.index('[Text Edit]') + 1
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


class GridEditorPreferences(EditorPreferences):
    location = ("Grid Editor",)
    title = "Grid Editor Settings"

    def __init__(self, settings, *args, **kwargs):
        super(GridEditorPreferences, self).__init__(
            settings['Grid'], *args, **kwargs)
        self.Sizer.Add(self._create_grid_config_editor())

    def _create_grid_config_editor(self):
        settings = self._settings
        sizer = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        sizer.Add(self._label_for('Default column size'))
        sizer.Add(self._number_editor(settings, 'col size'))
        sizer.AddMany(widgets.boolean_editor(
            self, settings, 'auto size cols', 'Auto size columns'))
        sizer.Add(self._label_for('Max column size\n(applies when auto size is on)'))
        sizer.Add(self._number_editor(settings, 'max col size'))
        return sizer

    def _label_for(self, name):
        label = ('%s: ' % name).capitalize()
        return Label(self, label=label)

    def _number_editor(self, settings, name):
        initial_value = settings[name]
        editor = NumCtrl(self, value=initial_value, integerWidth=3, allowNone=True)
        editor.Bind(wx.EVT_TEXT, lambda evt: self._set_value(editor, name))
        return editor

    def _set_value(self, editor, name):
        # Guard against dead object
        if editor:
            value = editor.GetValue()
            if value is not None:
                self._settings.set(name, int(value))

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
            btn = widgets.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, key)
            colors_sizer.Add(btn, (row, 0),
                             flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 1),
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
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
            btn = widgets.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, key)
            colors_sizer.Add(btn, (row, 2),
                             flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 3),
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
            row += 1
