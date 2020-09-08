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
from ..publish import RideSettingsChanged, PUBLISHER


@lru_cache(maxsize=2)
def read_fonts(fixed=False):
    """Returns list with fixed width fonts"""
    f = wx.FontEnumerator()
    f.EnumerateFacenames()
    names = f.GetFacenames(fixedWidthOnly=fixed)
    names = [n for n in names if not n.startswith('@')]
    names.sort()
    return names


class GeneralPreferences(PreferencesPanel):

    def __init__(self, settings, *args, **kwargs):
        super(GeneralPreferences, self).__init__(*args, **kwargs)
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
        f = IntegerChoiceEditor(
            self._settings, 'font size', 'Font Size',
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=30)
        sizer.AddMany([f.label(self), f.chooser(self)])
        fixed_font = False
        if 'zoom factor' in self._settings:
            z = SpinChoiceEditor(
                self._settings, 'zoom factor', 'Zoom Factor', (-10, 20))
            sizer.AddMany([z.label(self), z.chooser(self)])
        if 'fixed font' in self._settings:
            sizer.AddMany(boolean_editor(
                self, self._settings, 'fixed font', 'Use fixed width font'))
            fixed_font = self._settings['fixed font']
        if 'font face' in self._settings:
            s = StringChoiceEditor(self._settings, 'font face', 'Font Face', read_fonts(fixed_font))
            sizer.AddMany([s.label(self), s.chooser(self)])
        return sizer

    def create_colors_sizer(self):
        raise NotImplementedError('Implement me')


class DefaultPreferences(GeneralPreferences):
    location = ("General",)
    title = "General Settings"
    name = "General"

    def __init__(self, settings, *args, **kwargs):
        super(DefaultPreferences, self).__init__(settings[self.name], *args, **kwargs)
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        # print(f"DEBUG: settings_path {settings.get_path()}")

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        settings = (
                    ('foreground', 'Foreground'),
                    ('background', 'Background'),
                    )

        for settings_key, label_text in settings:
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            button = PreferencesColorPicker(
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

    def OnSettingsChanged(self, data):
        """Redraw the colors if the color settings are modified"""
        section, setting = data.keys
        if section == 'General':
            # print(f"DEBUG: OnSettings got here")
            panel = self.GetParent().GetParent()
            # print(f"DEBUG: OnSettings panel {panel.GetParent()}")
            """
            foreground = self._settings.get('foreground', 'black')
            background = self._settings.get('background', 'white')
            panel.settings['foreground'] = foreground
            panel.settings['background'] = background
            """
            panel.Refresh(True)
            panel.ShowPanel()
            self.Refresh(True)
