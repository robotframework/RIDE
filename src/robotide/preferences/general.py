#  Copyright 2020-     Robot Framework Foundation
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

from functools import lru_cache
from os.path import abspath, dirname, join

import wx

from ..ui.preferences_dialogs import (boolean_editor, PreferencesPanel, IntegerChoiceEditor, SpinChoiceEditor,
                                      StringChoiceEditor, PreferencesColorPicker)
from .managesettingsdialog import SaveLoadSettings
from wx import Colour
from ..context import IS_WINDOWS

ID_APPLY_TO_PANEL = wx.NewIdRef()
ID_RESET = wx.NewIdRef()
ID_SAVELOADSETTINGS = wx.NewIdRef()
ID_LOAD = 5551
ID_SAVE = 5552
ID_CANCEL = -1


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
    element.SetOwnBackgroundColour(bk_color)
    element.SetForegroundColour(fg_color)
    element.SetOwnForegroundColour(fg_color)


class GeneralPreferences(PreferencesPanel):

    def __init__(self, settings, *args, **kwargs):
        super(GeneralPreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._color_pickers = []
        self.name = None
        self._apply_to_panels = self._settings.get('apply to panels', False)

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.

        font_editor = self._create_font_editor()
        colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        reset = wx.Button(self, ID_RESET, 'Reset colors to default')
        saveloadsettings = wx.Button(self, ID_SAVELOADSETTINGS, 'Save or Load settings')
        self.cb_apply_to_panels = wx.CheckBox(self, ID_APPLY_TO_PANEL,
                                              label="Apply to Project and File Explorer panels")
        self.cb_apply_to_panels.Enable()
        self.cb_apply_to_panels.SetValue(self._apply_to_panels)
        if IS_WINDOWS:
            background_color = Colour("light gray")
            foreground_color = Colour("black")
            set_colors(self.cb_apply_to_panels, background_color, foreground_color)
        main_sizer.Add(font_editor)
        main_sizer.Add(colors_sizer)
        main_sizer.Add(self.cb_apply_to_panels)
        buttons_sizer.Add(reset)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(saveloadsettings)
        main_sizer.Add(buttons_sizer)
        self.SetSizerAndFit(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.OnReset)
        self.Bind(wx.EVT_BUTTON, self.OnSaveLoadSettings)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox, self.cb_apply_to_panels)

    def OnCheckBox(self, event):
        self._apply_to_panels = event.IsChecked()
        self._settings.set('apply to panels', self._apply_to_panels)
        # print(f"DEBUG: Preferences Checkbox set {str(self._apply_to_panels)}")

    def OnReset(self, event):
        if event.GetId() != ID_RESET:
            event.Skip()
            return
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])
        # self.Refresh()

    def OnSaveLoadSettings(self, event):
        if event.GetId() != ID_SAVELOADSETTINGS:
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)  # DEBUG self.__class__.__name__
        save_settings_dialog.CenterOnParent()
        save_settings_dialog.ShowModal()
        # Does not look nice but closes Preferences window, so it comes recolored on next call
        # Only working on first use :(
        # TODO: Only close window when Loading, not when Saving (but return is always 5101)
        wx.FindWindowByName("RIDE - Preferences").Close(force=True)

    def _reload_settings(self):
        import os
        from ..context import SETTINGS_DIRECTORY
        self._default_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
        settings = [s.strip() for s in open(self._default_path, 'r').readlines()]
        name = '[General]'
        start_index = settings.index(name) + 1
        defaults = {}
        for line in settings[start_index:]:
            if line.startswith('['):
                break
            if not line:
                continue
            key, value = [s.strip().strip('\'') for s in line.split("=")]
            # print(f"DEBUG: Preferences General default value type {type(value)} {value}")
            if len(value) > 0 and value[0] == '(' and value[-1] == ')':
                from ast import literal_eval as make_tuple
                value = make_tuple(value)
            defaults[key] = value
        self._settings = defaults

        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])
        self.Refresh(True)

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
            # print(f"DEBUG: Preferences General default value type {type(value)} {value}")
            if len(value) > 0 and value[0] == '(' and value[-1] == ')':
                from ast import literal_eval as make_tuple
                value = make_tuple(value)
            defaults[key] = value
        return defaults

    @staticmethod
    def _get_path():
        return join(dirname(abspath(__file__)), 'settings.cfg')

    def _create_font_editor(self):
        f = IntegerChoiceEditor(
            self._settings, 'font size', 'Font Size',
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=30)
        l_size = f.label(self)
        background_color = Colour("light gray")
        foreground_color = Colour("black")
        if IS_WINDOWS:
            set_colors(l_size, background_color, foreground_color)
        sizer.AddMany([l_size, f.chooser(self)])
        fixed_font = False
        if 'zoom factor' in self._settings:
            z = SpinChoiceEditor(
                self._settings, 'zoom factor', 'Zoom Factor', (-10, 20))
            l_zoom = z.label(self)
            if IS_WINDOWS:
                set_colors(l_zoom, background_color, foreground_color)
            sizer.AddMany([l_zoom, z.chooser(self)])
        if 'fixed font' in self._settings:
            l_ff, editor = boolean_editor(self, self._settings, 'fixed font', 'Use fixed width font')
            if IS_WINDOWS:
                set_colors(l_ff, background_color, foreground_color)
            sizer.AddMany([l_ff, editor])
            fixed_font = self._settings['fixed font']
        if 'font face' in self._settings:
            s = StringChoiceEditor(self._settings, 'font face', 'Font Face', read_fonts(fixed_font))
            l_font = s.label(self)
            if IS_WINDOWS:
                set_colors(l_font, background_color, foreground_color)
            sizer.AddMany([l_font, s.chooser(self)])
        sizer.Layout()
        return sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')


class DefaultPreferences(GeneralPreferences):
    location = ("General",)
    title = "General Settings"
    name = "General"

    def __init__(self, settings, *args, **kwargs):
        super(DefaultPreferences, self).__init__(settings[self.name], *args, **kwargs)
        # PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        # print(f"DEBUG: settings_path {settings.get_path()}")

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        settings = (
            ('foreground', 'Foreground'),
            ('background', 'Background'),
            ('secondary foreground', 'Secondary Foreground'),
            ('secondary background', 'Secondary Background'),
            ('foreground text', 'Text Foreground'),
            ('background help', 'Help Background')
        )
        background_color = Colour("light gray")
        foreground_color = Colour("black")
        for settings_key, label_text in settings:
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            if IS_WINDOWS:
                set_colors(label, background_color, foreground_color)
            button = PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, settings_key)
            container.Add(button, (row, column), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def OnReset(self, event):
        defaults = self._read_defaults()
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])
        # self.Refresh()
        wx.FindWindowByName("RIDE - Preferences").Close(force=True)
