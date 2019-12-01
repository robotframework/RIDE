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
from robotide.utils import PY3

try:  # import installed version first
    import robotframeworklexer
except ImportError:
    try:  # then import local version
        from . import robotframeworklexer
    except ImportError:  # Pygments is not installed
        robotframeworklexer = None

if PY3:
    from functools import lru_cache
else:
    # On PY2, cache function is not built-in
    def lru_cache(*args, **kwargs):
        def inner(func):
            return func
        return inner


@lru_cache(maxsize=2)
def ReadFonts(fixed=False):
    '''Returns list with fixed width fonts'''
    f = wx.FontEnumerator()
    f.EnumerateFacenames()
    if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
        names = f.GetFacenames(fixedWidthOnly=fixed)
    else:
        names = f.GetFacenames()
    names = [n for n in names if not n.startswith('@')]
    names.sort()
    return names


class EditorPreferences(widgets.PreferencesPanel):

    def __init__(self, settings, *args, **kwargs):
        super(EditorPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._color_pickers = []

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.

        font_editor = self._create_font_editor()
        colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        reset = wx.Button(self, wx.ID_ANY, 'Reset colors to default')
        main_sizer.Add(font_editor)
        main_sizer.Add(colors_sizer)
        main_sizer.Add(reset)
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.OnReset)

    def OnReset(self, event):
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])

    def _read_defaults(self, plugin=False):
        settings = [s.strip() for s in open(self._get_path(), 'r').readlines()]
        name = ('[[%s]]' if plugin else '[%s]') % self.name
        start_index = settings.index(name) + 1
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

    def _create_font_editor(self):
        f = widgets.IntegerChoiceEditor(
            self._settings, 'font size', 'Font Size',
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=30)
        sizer.AddMany([f.label(self), f.chooser(self)])
        fixed_font = False
        if 'zoom factor' in self._settings:
            z = widgets.SpinChoiceEditor(
                self._settings, 'zoom factor', 'Zoom Factor', (-10, 20))
            sizer.AddMany([z.label(self), z.chooser(self)])
        if 'fixed font' in self._settings:
            sizer.AddMany(widgets.boolean_editor(
                self, self._settings, 'fixed font', 'Use fixed width font'))
            fixed_font = self._settings['fixed font']
        if 'font face' in self._settings:
            s = widgets.StringChoiceEditor(self._settings, 'font face', 'Font Face', ReadFonts(fixed_font))
            sizer.AddMany([s.label(self), s.chooser(self)])
        return sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')


class TextEditorPreferences(EditorPreferences):
    location = ("Text Editor",)
    title = "Text Editor Settings"
    name = "Text Edit"

    def __init__(self, settings, *args, **kwargs):
        super(TextEditorPreferences, self).__init__(
            settings[self.name], *args, **kwargs)

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        if robotframeworklexer:
            settings = (
                        ('argument', 'Argument foreground'),
                        ('comment', 'Comment foreground'),
                        ('error', 'Error foreground'),
                        ('gherkin', 'Gherkin keyword foreground'),
                        ('heading', 'Heading foreground'),
                        ('import', 'Import foreground'),
                        ('variable', 'Variable foreground'),
                        ('tc_kw_name', 'Keyword definition foreground'),
                        ('separator', 'Separator'),
                        ('setting', 'Setting foreground'),
                        ('syntax', 'Syntax characters'),
                        ('background', 'Text background'),
                       )
        else:
            settings = (
                        ('setting', 'Text foreground'),
                        ('background', 'Text background'),
                       )

        for settings_key, label_text in settings:
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
                          flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def OnReset(self, event):
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])


class GridEditorPreferences(EditorPreferences):
    location = ("Grid Editor",)
    title = "Grid Editor Settings"
    name = "Grid"

    def __init__(self, settings, *args, **kwargs):
        super(GridEditorPreferences, self).__init__(
            settings[self.name], *args, **kwargs)
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
        sizer.AddMany(widgets.boolean_editor(
            self, settings, 'word wrap', 'Word wrap and auto size rows'))
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
            ('text variable', 'Variable Foreground'),
            ('text unknown variable', 'Unknown Variable Foreground'),
            ('text commented', 'Comments Foreground'),
            ('text string', 'Default Foreground'),
            ('text empty', 'Empty Foreground'),
        ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            btn = widgets.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, key)
            self._color_pickers.append(btn)
            colors_sizer.Add(btn, (row, 2),
                             flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 3),
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
            self._color_pickers.append(btn)
            colors_sizer.Add(btn, (row, 0),
                             flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 1),
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
            row += 1


class TestRunnerPreferences(EditorPreferences):
    location = ("Test Runner",)
    title = "Test Runner Settings"
    name = "Test Runner"

    def __init__(self, settings, *args, **kwargs):
        super(TestRunnerPreferences, self).__init__(
            settings['Plugins'][self.name], *args, **kwargs)
        self.Sizer.Add(self._create_test_runner_config_editor())

    def _create_test_runner_config_editor(self):
        self._settings.get('confirm run', True)
        settings = self._settings
        sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)

        sizer.AddMany(widgets.boolean_editor(
            self, settings, 'confirm run', 'Asks for confirmation to run all'
                                           ' tests if none selected '))
        return sizer

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        row = 0
        column = 0
        for settings_key, label_text in (
            ('foreground', 'Text foreground'),
            ('background', 'Text background'),
            ('error', 'Error foreground'),
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
                          flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def OnReset(self, event):
        defaults = self._read_defaults(plugin=True)
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])
