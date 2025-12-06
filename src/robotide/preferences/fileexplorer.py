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


def get_settings_path():
    import os
    from ..context import SETTINGS_DIRECTORY
    main_settings_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
    new_path = os.environ['RIDESETTINGS']
    if os.path.exists(new_path):
        return new_path
    return main_settings_path


class FileExplorerPreferences(EditorPreferences):
    location = (_("File Explorer"),)

    def __init__(self, settings, *args, **kwargs):
        self._settings = settings
        self.location = (_("File Explorer"),)
        self.title = _("File Explorer Settings")
        self.cb_default_file_explorer = None
        super(FileExplorerPreferences, self).__init__(settings['Plugins']['File Explorer'], *args, **kwargs)
        self._settings._name = self.name = 'File Explorer'
        self._default_path = get_settings_path()
        # print(f"DEBUG: Preferences File Explorer init type settings={type(self._settings)}")
        # self.Sizer.Add(self.txt_file_explorer)
        self.Sizer.Add(self._create_file_explorer_config_editor())

    def set_txt_value(self, evt):
        new_value = self.txt_file_explorer.GetValue()
        self._settings.set('file manager', new_value)
        evt.Skip()

    def _create_file_explorer_config_editor(self):
        self._settings.get('own colors', False)
        self._settings.get('file manager', None)
        self._settings.get('system file explorer', True)
        settings = self._settings
        self.txt_file_explorer = wx.TextCtrl(self, id=ID_TXT_FILE_EXPLORER, size=wx.Size(150, 20), name='file_manager')
        if settings['file manager'] is not None:
            self.txt_file_explorer.SetValue(settings['file manager'])
        if settings['system file explorer']:
            self.txt_file_explorer.SetEditable(False)
            self.txt_file_explorer.Disable()
            # print(f"DEBUG: Preferences _create_file_explorer_config_editor DISABLE settings['system file explorer']="
            #       f"{settings['system file explorer']}")
        else:
            self.txt_file_explorer.Enable()
            self.txt_file_explorer.SetEditable(True)
            # print(f"DEBUG: Preferences _create_file_explorer_config_editor ENABLE settings['system file explorer']="
            #       f"{settings['system file explorer']}")
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
        # print(f"DEBUG: Preferences on_check_box ENTER {event}")
        # event.Skip()
        if event.GetId() == ID_USE_OWN_COLORS:
            self._own_colors = event.IsChecked()
            self._settings.set('own colors', self._own_colors)
            if self._own_colors:
                self.set_own_colors()
            else:
                self.set_global_colors()
        if event.GetId() == ID_DEFAULT_FILE_EXPLORER:
            # print(f"DEBUG: Preferences on_check_box ID_DEFAULT_FILE_EXPLORER {event.IsChecked()}")
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
        self._settings._name = self.name = 'File Explorer'
        # print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings ENTER {event=}"
        #       f" ID_SAVELOADSETTINGS={ID_SAVELOADSETTINGS}"
        #       f"\n self._settings = {self._settings}")
        if event.GetId() != ID_SAVELOADSETTINGS:
            # print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings "
            #       f"CONDITION event.GetId() != ID_SAVELOADSETTINGS "
            #       f"{event.GetId()} {ID_SAVELOADSETTINGS=}")
            event.Skip()
            return
        save_settings_dialog = SaveLoadSettings(self, self._settings)
        save_settings_dialog.CenterOnParent()
        result = save_settings_dialog.ShowModal()
        # print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings Preferences color_pickers {self._color_pickers=}")
        for picker in self._color_pickers:
            picker.SetColour(self._settings[picker.key])
        # print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings check {ID_LOAD}=={result=}"
        #       f"\nDIALOG RESULT {save_settings_dialog.GetReturnCode()}")
        if result == 5101:  # DEBUG Should be ID_LOAD: but is always 5101
            # print(f"DEBUG: Preferences FILE_EXPLORER on_save_load_settings {result=}")
            self._reload_settings()  # Force reload on File explorer pane
            # wnd_handle = wx.FindWindowByName('files_explorer')
            # print(f"DEBUG: Preferences FILE_EXPLORER WINDOW IS {wnd_handle=}")
            # if wnd_handle:
            #     wnd_handle.Update()
            self.Update()

    def _reload_settings(self):
        from pprint import pp
        from .settings import RideSettings
        if self._settings is None:
            self._settings = RideSettings(self._default_path)
        # else:
        #     print(f"DEBUG: FileExplorerPreferences _reload_settings ENTER previous settings="
        #           f"{pp(self._settings)}")
        settings = [s.strip() for s in open(self._default_path, 'r').readlines()]
        name = '[[File Explorer]]'
        # print(f"DEBUG: Preferences {name} _reload_settings set {settings}")
        start_index = settings.index(name) + 1
        defaults = {}
        for line in settings[start_index:]:
            if line.startswith('['):
                break
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            key, value = [s.strip().strip('\'') for s in line.split("=")]
            # print(f"DEBUG: Preferences FILE_EXPLORER default value type {type(value)} {key}={value}")
            if len(value) > 0 and value[0] == '(' and value[-1] == ')':
                from ast import literal_eval as make_tuple
                value = make_tuple(value)
            defaults[key] = value
        for key, value in defaults.items():
            if key in ["own colors", "system file explorer", "opened", "docked"]:
                self._settings.set(key, bool(value))
            elif key == "font size":
                self._settings.set(key, int(value))
            else:
                self._settings.set(key, value)
        # print(f"DEBUG: FileExplorerPreferences _reload_settings EXIT previous settings="
        #       f"{pp(self._settings)}")
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
            if key in ["own colors", "system file explorer", "opened", "docked"]:
                defaults[key] = bool(value)
            elif key == "font size":
                defaults[key] = int(value)
            else:
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
