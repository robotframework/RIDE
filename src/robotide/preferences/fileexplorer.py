#  Copyright 2025-     Robot Framework Foundation
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
import builtins
import wx

from .editors import EditorPreferences, read_fonts, set_colors, ID_SAVELOADSETTINGS
from ..ui import preferences_dialogs as pdiag
from ..ui.preferences_dialogs import (boolean_editor, IntegerChoiceEditor, SpinChoiceEditor,
                                      StringChoiceEditor, PreferencesColorPicker)
from .managesettingsdialog import SaveLoadSettings
try:
    from robot.conf import languages
except ImportError:
    languages = None

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

ID_DEFAULT_FILE_EXPLORER = wx.NewIdRef()
ID_TXT_FILE_EXPLORER = wx.NewIdRef()
ID_USE_OWN_COLORS = wx.NewIdRef()
ID_LOAD = 5551
ID_SAVE = 5552
ID_CANCEL = -1
LIGHT_GRAY = "light gray"
FIXED_FONT = 'fixed font'


class FileExplorerPreferences(EditorPreferences):
    location = (_("File Explorer"),)

    def __init__(self, settings, *args, **kwargs):
        # self._settings = settings
        self.location = (_("File Explorer"),)
        self.name = 'File Explorer'
        self.title = _("File Explorer Settings")
        self.cb_default_file_explorer = None
        super(FileExplorerPreferences, self).__init__(settings['Plugins'][self.name], *args, **kwargs)
        # print(f"DEBUG: Preferences File Explorer init type settings={type(self._settings)}")
        # self.Sizer.Add(self.txt_file_explorer)
        self.Sizer.Add(self._create_file_explorer_config_editor())
        """
        self._color_pickers = []
        # self._reload_settings()
        # self.background_color = self.settings['background']
        # self.foreground_color = self.settings['foreground']
        # self.sbackground_color = self.settings['secondary background']
        # self.sforeground_color = self.settings['secondary foreground']
        # font_editor = self._create_font_editor()
        # colors_sizer = self.create_colors_sizer()
        main_sizer = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        # buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        # reset = wx.Button(self, ID_RESET, _('Reset colors to default'))
        # saveloadsettings = wx.Button(self, ID_SAVELOADSETTINGS, _('Save or Load settings'))
        self.cb_own_colors = wx.CheckBox(self, ID_USE_OWN_COLORS, label=_("Use own colors"))
        self.cb_own_colors.Enable()
        self.cb_own_colors.SetValue(self._own_colors)
        set_colors(self.cb_own_colors, self.background_color, self.foreground_color)
        # set_colors(reset, self.sbackground_color, self.sforeground_color)
        # set_colors(saveloadsettings, self.sbackground_color, self.sforeground_color)
        # main_sizer.Add(font_editor)
        # main_sizer.Add(colors_sizer)
        main_sizer.Add(self.cb_own_colors)
        # buttons_sizer.Add(reset)
        # buttons_sizer.AddSpacer(10)
        # buttons_sizer.Add(saveloadsettings)
        # main_sizer.Add(buttons_sizer)
        main_sizer.AddSpacer(10)
        main_sizer.Add(self.txt_file_explorer)
        self.SetSizerAndFit(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_reset)
        self.Bind(wx.EVT_BUTTON, self.on_save_load_settings)
        self.Bind(wx.EVT_CHECKBOX, self.on_check_box, self.cb_own_colors)
        self.Bind(wx.EVT_CHECKBOX, self.on_check_box, self.cb_default_file_explorer)
        """

    def set_txt_value(self, evt):
        new_value = self.txt_file_explorer.GetValue()
        self._settings.set('file manager', new_value)
        evt.Skip()

    def _create_file_explorer_config_editor(self):
        # self._settings.get('confirm run', True)
        # self._settings.get('use colors', False)
        self._settings.get('own colors', False)
        self._settings.get('file manager', None)
        self._settings.get('system file explorer', True)
        settings = self._settings
        self.txt_file_explorer = wx.TextCtrl(self, id=ID_TXT_FILE_EXPLORER, size=wx.Size(150, 20), name='file_manager')
        if settings['file manager'] is not None:
            self.txt_file_explorer.SetValue(settings['file manager'])
        # self.cb_default_file_explorer = wx.CheckBox(self, ID_DEFAULT_FILE_EXPLORER, label=_("Use System File Explorer"))
        # set_colors(self.cb_default_file_explorer, self.background_color, self.foreground_color)
        # self.Sizer.Add(self.cb_default_file_explorer)
        sizer = wx.FlexGridSizer(rows=8, cols=2, vgap=10, hgap=10)
        l_usecolor, own_colors = pdiag.boolean_editor(self, settings, 'own colors',
                                              f"{_('Use these colors definitions')} ")
        l_confirm, self.cb_default_file_explorer = pdiag.boolean_editor(self, settings, 'system file explorer',
                                                   f"{_('Use operating system file explorer')}")
        own_colors.SetId(ID_USE_OWN_COLORS)
        m_sizer = wx.FlexGridSizer(cols=3, gap=wx.Size(10, 10))
        self.cb_default_file_explorer.SetId(ID_DEFAULT_FILE_EXPLORER)
        set_colors(l_confirm, self.background_color, self.foreground_color)
        set_colors(l_usecolor, self.background_color, self.foreground_color)
        set_colors(self.txt_file_explorer, self.background_color, self.foreground_color)
        self.Bind(wx.EVT_CHECKBOX, self.on_check_box, self.cb_default_file_explorer)
        self.txt_file_explorer.Bind(wx.EVT_KILL_FOCUS, lambda evt: self.set_txt_value(evt))
        sizer.AddMany([l_usecolor, own_colors])
        # sizer.Add(wx.StaticText())
        m_sizer.AddMany([l_confirm, self.cb_default_file_explorer, self.txt_file_explorer])
        sizer.Add(m_sizer)
        return sizer

    def create_colors_sizer(self):
        container = wx.GridBagSizer()
        column = 0
        row = 0
        settings = (
            ('foreground', _('Foreground')),
            ('background', _('Background')),
            ('secondary foreground', _('Secondary Foreground')),
            ('secondary background', _('Secondary Background'))
        )
        for settings_key, label_text in settings:
            if column == 4:
                column = 0
                row += 1
            label = wx.StaticText(self, wx.ID_ANY, label_text)
            set_colors(label, self.background_color, self.foreground_color)
            button = PreferencesColorPicker(
                self, wx.ID_ANY, self._settings, settings_key)
            container.Add(button, (row, column), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=4)
            self._color_pickers.append(button)
            column += 1
            container.Add(label, (row, column), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=8)
            column += 1
        return container

    def set_own_colors(self):
        print(f"DEBUG: Preferences Checkbox set OWN COLORS {str(self._own_colors)}")

    def set_global_colors(self):
        print(f"DEBUG: Preferences Checkbox set GLOBAL COLORS {str(self._own_colors)}")

    def on_check_box(self, event):
        print(f"DEBUG: Preferences on_check_box ENTER {event}")
        # event.Skip()
        if event.GetId() == ID_USE_OWN_COLORS:
            self._own_colors = event.IsChecked()
            self._settings.set('own colors', self._own_colors)
            if self._own_colors:
                self.set_own_colors()
            else:
                self.set_global_colors()
        if event.GetId() == ID_DEFAULT_FILE_EXPLORER:
            print(f"DEBUG: Preferences on_check_box ID_DEFAULT_FILE_EXPLORER {event.IsChecked()}")
            if not event.IsChecked():
                self.txt_file_explorer.SetEditable(True)
            else:
                self.txt_file_explorer.SetEditable(False)
            self.Update()

    def on_reset(self, event):
        if not self.name:
            self.name = "File Explorer"
        defaults = self._read_defaults(plugin=True)
        for picker in self._color_pickers:
            picker.SetColour(defaults[picker.key])

    def on_save_load_settings(self, event):
        if event.GetId() != ID_SAVELOADSETTINGS:
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)
        save_settings_dialog.CenterOnParent()
        result = save_settings_dialog.ShowModal()
        for picker in self._color_pickers:
            picker.SetColour(self._settings[picker.key])
        print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings check {ID_LOAD}=={result=}")
        if result == 5101:  # DEBUG Should be ID_LOAD: ut is always 5101
            print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings {result=}")
            self._reload_settings()  # Force reload on File explorer pane
            # wnd_handle = wx.FindWindowByName('files_explorer')
            # print(f"DEBUG: Preferences FILE_EXPLORER WINDOW IS {wnd_handle=}")
            # if wnd_handle:
            #     wnd_handle.Update()
            self.Update()

    def _reload_settings(self):
        import os
        from ..context import SETTINGS_DIRECTORY
        from .settings import RideSettings
        self._settings = RideSettings()
        # self._default_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
        self._default_path = self._settings.user_path
        settings = [s.strip() for s in open(self._default_path, 'r').readlines()]
        name = '[[File Explorer]]'
        print(f"DEBUG: Preferences {name} _reload_settings set {settings}")
        start_index = settings.index(name) + 1
        defaults = {}
        for line in settings[start_index:]:
            if line.startswith('['):
                break
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            key, value = [s.strip().strip('\'') for s in line.split("=")]
            print(f"DEBUG: Preferences FILE_EXPLORER default value type {type(value)} {key}={value}")
            if len(value) > 0 and value[0] == '(' and value[-1] == ')':
                from ast import literal_eval as make_tuple
                value = make_tuple(value)
            defaults[key] = value
        for key, value in defaults.items():
            self._settings.set(key, value)

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
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            # print(f"DEBUG: Preferences General RESET default line {line} \nLine Split: {line.split("=")}")
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
            self._settings, 'font size', _('Font Size'),
            [str(i) for i in range(8, 16)])
        sizer = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=30)
        l_size = f.label(self)
        set_colors(l_size, self.background_color, self.foreground_color)
        sizer.AddMany([l_size, f.chooser(self)])
        fixed_font = False
        if 'zoom factor' in self._settings:
            z = SpinChoiceEditor(
                self._settings, 'zoom factor', _('Zoom Factor'), (-10, 20))
            l_zoom = z.label(self)
            set_colors(l_zoom, self.background_color, self.foreground_color)
            sizer.AddMany([l_zoom, z.chooser(self)])
        if FIXED_FONT in self._settings:
            l_ff, editor = boolean_editor(self, self._settings, FIXED_FONT, _('Use fixed width font'))
            set_colors(l_ff, self.background_color, self.foreground_color)
            sizer.AddMany([l_ff, editor])
            fixed_font = self._settings[FIXED_FONT]
        if 'font face' in self._settings:
            s = StringChoiceEditor(self._settings, 'font face', _('Font Face'), read_fonts(fixed_font))
            l_font = s.label(self)
            set_colors(l_font, self.background_color, self.foreground_color)
            sizer.AddMany([l_font, s.chooser(self)])
        sizer.Layout()
        return sizer
