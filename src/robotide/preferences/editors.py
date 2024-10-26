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

from os.path import abspath, dirname, join
import builtins
import wx
from wx.lib.masked import NumCtrl

from .settings import RideSettings
from ..ui import preferences_dialogs as pdiag
from robotide.ui.preferences_dialogs import PreferencesPanel

from ..widgets import Label
from .managesettingsdialog import SaveLoadSettings
from functools import lru_cache

try:  # import installed version first
    from pygments.lexers import robotframework as robotframeworklexer
except ImportError:  # Pygments is not installed
    robotframeworklexer = None

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


ID_SAVELOADSETTINGS = wx.NewIdRef()
ID_LOAD = 5551
ID_SAVE = 5552
ID_CANCEL = -1
TEXT_BACKGROUND = _('Text background')
LIGHT_GRAY = 'light gray'
FIXED_FONT = 'fixed font'


@lru_cache(maxsize=2)
def read_fonts(fixed=False):
    """Returns list with fixed width fonts"""
    f = wx.FontEnumerator()
    f.EnumerateFacenames()
    names = f.GetFacenames(fixedWidthOnly=fixed)
    names = [n for n in names if not n.startswith('@')]
    names.sort()
    return names


def set_colors(element, bk_color, fg_color):
    element.SetBackgroundColour(bk_color)
    # element.SetOwnBackgroundColour(bk_color)
    element.SetForegroundColour(fg_color)
    # element.SetOwnForegroundColour(fg_color)


class EditorPreferences(PreferencesPanel):

    def __init__(self, settings, *args, **kwargs):
        super(EditorPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._color_pickers = []
        self.name = None

        self._gsettings = RideSettings()
        self.settings = self._gsettings['General']

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.

        font_editor = self._create_font_editor()
        colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        reset = wx.Button(self, wx.ID_ANY, _('Reset colors to default'))
        saveloadsettings = wx.Button(self, ID_SAVELOADSETTINGS, _('Save or Load settings'))
        set_colors(reset, self.secondary_background_color, self.secondary_foreground_color)
        set_colors(saveloadsettings, self.secondary_background_color, self.secondary_foreground_color)
        main_sizer.Add(font_editor)
        main_sizer.Add(colors_sizer)
        buttons_sizer.Add(reset)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(saveloadsettings)
        main_sizer.Add(buttons_sizer)
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_reset)
        self.Bind(wx.EVT_BUTTON, self.on_save_load_settings)

    def on_save_load_settings(self, event):
        raise NotImplementedError('Implement me')

    def on_reset(self, event):
        if not self.name:
            self.name = "Grid"
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
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            key, value = [s.strip().strip('\'') for s in line.split("=")]
            defaults[key] = value
        return defaults

    @staticmethod
    def _get_path():
        return join(dirname(abspath(__file__)), 'settings.cfg')

    def _create_font_editor(self):
        f = pdiag.IntegerChoiceEditor(
            self._settings, 'font size', _('Font Size'),
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=30)
        l_size = f.label(self)
        set_colors(l_size, self.background_color, self.foreground_color)
        sizer.AddMany([l_size, f.chooser(self)])
        fixed_font = False
        if 'zoom factor' in self._settings:
            z = pdiag.SpinChoiceEditor(
                self._settings, 'zoom factor', _('Zoom Factor'), (-10, 20))
            l_zoom = z.label(self)
            set_colors(l_zoom, self.background_color, self.foreground_color)
            sizer.AddMany([l_zoom, z.chooser(self)])
        if FIXED_FONT in self._settings:
            l_ff, editor = pdiag.boolean_editor(self, self._settings, FIXED_FONT, _('Use fixed width font'))
            set_colors(l_ff, self.background_color, self.foreground_color)
            sizer.AddMany([l_ff, editor])
            fixed_font = self._settings[FIXED_FONT]
        if 'font face' in self._settings:
            s = pdiag.StringChoiceEditor(self._settings, 'font face', _('Font Face'), read_fonts(fixed_font))
            l_font = s.label(self)
            set_colors(l_font, self.background_color, self.foreground_color)
            sizer.AddMany([l_font, s.chooser(self)])
        return sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')


class TextEditorPreferences(EditorPreferences):
    location = (_("Text Editor"),)

    def __init__(self, settings, *args, **kwargs):
        self.location = (_("Text Editor"),)
        self.title = _("Text Editor Settings")
        self.name = "Text Edit"
        super(TextEditorPreferences, self).__init__(settings[self.name], *args, **kwargs)
        self.Sizer.Add(self._create_text_config_editor())

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        if robotframeworklexer:
            settings = (
                ('argument', _('Argument foreground')),
                ('comment', _('Comment foreground')),
                ('error', _('Error foreground')),
                ('gherkin', _('Gherkin keyword foreground')),
                ('heading', _('Heading foreground')),
                ('import', _('Import foreground')),
                ('variable', _('Variable foreground')),
                ('tc_kw_name', _('Keyword definition foreground')),
                ('keyword', _('Keyword call foreground')),
                ('separator', _('Separator')),
                ('setting', _('Setting foreground')),
                ('syntax', _('Syntax characters')),
                ('background', TEXT_BACKGROUND),
            )
        else:
            settings = (
                ('setting', _('Text foreground')),
                ('background', TEXT_BACKGROUND),
            )
        for settings_key, label_text in settings:
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            set_colors(label, self.background_color, self.foreground_color)
            button = pdiag.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, settings_key)
            container.Add(button, (row, column),
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column),
                          flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def on_save_load_settings(self, event):
        if event.GetId() != ID_SAVELOADSETTINGS:
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)
        save_settings_dialog.CenterOnParent()
        save_settings_dialog.ShowModal()
        for picker in self._color_pickers:
            picker.SetColour(self._settings[picker.key])

    def on_reset(self, event):
        if not self.name:
            self.name = "Text Edit"
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])

    def _create_text_config_editor(self):
        settings = self._settings
        sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        l_auto_suggest, editor = pdiag.boolean_editor(self, settings, 'enable auto suggestions',
                                                _('Enable auto suggestions'))
        set_colors(l_auto_suggest, self.background_color, self.foreground_color)
        sizer.AddMany([l_auto_suggest, editor])
        return sizer


class GridEditorPreferences(EditorPreferences):
    location = (_("Grid Editor"),)

    def __init__(self, settings, *args, **kwargs):
        self.location = (_("Grid Editor"),)
        self.title = _("Grid Editor Settings")
        self.name = "Grid"
        super(GridEditorPreferences, self).__init__(
            settings[self.name], *args, **kwargs)
        self.Sizer.Add(self._create_grid_config_editor())

    def _create_grid_config_editor(self):
        settings = self._settings
        sizer = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        l_col_size = self._label_for(_('Default column size'))
        set_colors(l_col_size, self.background_color, self.foreground_color)
        sizer.Add(l_col_size)
        sizer.Add(self._number_editor(settings, 'col size'))
        l_auto_size, editor = pdiag.boolean_editor(self, settings, 'auto size cols', _('Auto size columns'))
        set_colors(l_auto_size, self.background_color, self.foreground_color)
        sizer.AddMany([l_auto_size, editor])
        l_max_size = self._label_for(_('Max column size\n(applies when auto size is on)'))
        set_colors(l_max_size, self.background_color, self.foreground_color)
        sizer.Add(l_max_size)
        sizer.Add(self._number_editor(settings, 'max col size'))
        l_word_wrap, editor = pdiag.boolean_editor(self, settings, 'word wrap', _('Word wrap and auto size rows'))
        set_colors(l_word_wrap, self.background_color, self.foreground_color)
        sizer.AddMany([l_word_wrap, editor])
        l_auto_suggest, editor = pdiag.boolean_editor(self, settings, 'enable auto suggestions',
                                                _('Enable auto suggestions'))
        set_colors(l_auto_suggest, self.background_color, self.foreground_color)
        sizer.AddMany([l_auto_suggest, editor])
        return sizer

    def _label_for(self, name):
        label = ('%s: ' % name).capitalize()
        return Label(self, label=label)

    def _number_editor(self, settings, name):
        initial_value = settings[name]
        editor = NumCtrl(self, value=initial_value, integerWidth=3, allowNone=True)
        set_colors(editor, self.background_color, self.foreground_color)
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
            ('text user keyword', _('User Keyword Foreground')),
            ('text library keyword', _('Library Keyword Foreground')),
            ('text variable', _('Variable Foreground')),
            ('text unknown variable', _('Unknown Variable Foreground')),
            ('text commented', _('Comments Foreground')),
            ('text string', _('Default Foreground')),
            ('text empty', _('Empty Foreground')),
        ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            set_colors(lbl, self.background_color, self.foreground_color)
            btn = pdiag.PreferencesColorPicker(
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
                ('background assign', _('Variable Background')),
                ('background keyword', _('Keyword Background')),
                ('background mandatory', _('Mandatory Field Background')),
                ('background optional', _('Optional Field Background')),
                ('background must be empty', _('Mandatory Empty Field Background')),
                ('background unknown', _('Unknown Background')),
                ('background error', _('Error Background')),
                ('background highlight', _('Highlight Background'))
        ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            set_colors(lbl, self.background_color, self.foreground_color)
            btn = pdiag.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, key)
            self._color_pickers.append(btn)
            colors_sizer.Add(btn, (row, 0),
                             flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            colors_sizer.Add(lbl, (row, 1),
                             flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
            row += 1

    def on_save_load_settings(self, event):
        if event.GetId() != ID_SAVELOADSETTINGS:
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)
        save_settings_dialog.CenterOnParent()
        save_settings_dialog.ShowModal()
        for picker in self._color_pickers:
            picker.SetColour(self._settings[picker.key])


class TestRunnerPreferences(EditorPreferences):
    location = (_("Test Runner"),)

    def __init__(self, settings, *args, **kwargs):
        self.location = (_("Test Runner"),)
        self.title = _("Test Runner Settings")
        self.name = "Test Runner"
        super(TestRunnerPreferences, self).__init__(
            settings['Plugins'][self.name], *args, **kwargs)
        help_color = wx.StaticText(self, wx.ID_ANY, _("Colors will be active after next RIDE restart."))
        set_colors(help_color, self.background_color, self.foreground_color)
        self.Sizer.Add(help_color)
        self.Sizer.Add(self._create_test_runner_config_editor())

    def _create_test_runner_config_editor(self):
        self._settings.get('confirm run', True)
        self._settings.get('use colors', False)
        settings = self._settings
        sizer = wx.FlexGridSizer(rows=6, cols=2, vgap=10, hgap=10)
        from sys import platform
        if platform.endswith('win32'):
            add_colors = "-C ansi"
        else:
            add_colors = "-C on"
        l_usecolor, usecolor = pdiag.boolean_editor(self, settings, 'use colors',
                                              f"{_('Shows console colors set by')} {add_colors} ")
        l_confirm, editor = pdiag.boolean_editor(self, settings, 'confirm run',
                                           _('Asks for confirmation to run all tests if none selected '))
        set_colors(l_confirm, self.background_color, self.foreground_color)
        set_colors(l_usecolor, self.background_color, self.foreground_color)
        sizer.AddMany([l_usecolor, usecolor])
        sizer.AddMany([l_confirm, editor])
        return sizer

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        row = 0
        column = 0
        for settings_key, label_text in (
                ('foreground', _('Text foreground')),
                ('background', TEXT_BACKGROUND),
                ('error', _('Error foreground')),
                ('fail color', _('Fail foreground')),
                ('pass color', _('Pass foreground')),
                ('skip color', _('Skip foreground')),
        ):
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            set_colors(label, self.background_color, self.foreground_color)
            button = pdiag.PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, settings_key)
            container.Add(button, (row, column),
                          flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column),
                          flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def on_save_load_settings(self, event):
        if event.GetId() != ID_SAVELOADSETTINGS:
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)
        save_settings_dialog.CenterOnParent()
        save_settings_dialog.ShowModal()
        for picker in self._color_pickers:
            picker.SetColour(self._settings[picker.key])

    def on_reset(self, event):
        if not self.name:
            self.name = "Test Runner"
        defaults = self._read_defaults(plugin=True)
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])
