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

import builtins
import os
import wx

from wx import Colour
from ..widgets import RIDEDialog, VerticalSizer
# from .configobj import ConfigObj, UnreprError
from . import ConfigObj, UnreprError
from .settings import ConfigurationError, _Section, initialize_settings

from ..context import SETTINGS_DIRECTORY

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

ID_LOAD = 5551
ID_SAVE = 5552
ID_CANCEL = -1


class SaveLoadSettings(RIDEDialog):

    def __init__(self, parent, settings):
        self._parent = parent
        self._settings = settings
        self._section = self._settings._name
        self._selection_listeners = []
        title = _("Save or Load Settings")
        RIDEDialog.__init__(self, parent=parent, title=title, size=(650, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        main_sizer = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        load = wx.Button(self, ID_LOAD, _('Load settings from file...'))
        save = wx.Button(self, ID_SAVE, _('Save settings to file...'))
        self.SetSizer(VerticalSizer())
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        load.SetBackgroundColour(Colour(self.color_secondary_background))
        load.SetForegroundColour(Colour(self.color_secondary_foreground))
        save.SetBackgroundColour(Colour(self.color_secondary_background))
        save.SetForegroundColour(Colour(self.color_secondary_foreground))
        self._default_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
        directory = wx.StaticText(self, label=f"{_('Current directory:')} {SETTINGS_DIRECTORY}")
        buttons_sizer.Add(load)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(save)
        main_sizer.Add(directory)
        main_sizer.AddSpacer(10)
        main_sizer.Add(buttons_sizer)
        self.SetSizerAndFit(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.on_load)
        self.Bind(wx.EVT_BUTTON, self.on_save)
        # print(f"DEBUG: SaveLoad init returncode {self.GetReturnCode()}")

    def on_load(self, event):
        if event.GetId() != ID_LOAD:
            event.Skip()
            self.SetReturnCode(ID_CANCEL)
            return ID_CANCEL
        load_dlg = wx.FileDialog(self, message=_("File with Settings to Load"),
                                 defaultDir=SETTINGS_DIRECTORY, wildcard="*.cfg")
        if load_dlg.ShowModal() == wx.ID_CANCEL:
            self.SetReturnCode(ID_CANCEL)
            return ID_CANCEL
        file = load_dlg.GetPath()
        if os.path.isfile(file):  # Test validity settings
            self.Freeze()
            self.load_and_merge(file)
            self.Thaw()
            self._parent.Refresh()
            self._parent.GetParent().Refresh()
            self.SetReturnCode(ID_LOAD)
            self.Close()
            return ID_LOAD

    def on_close(self):
        self.SetReturnCode(ID_CANCEL)
        return ID_CANCEL

    def on_save(self, event):
        if event.GetId() != ID_SAVE:
            event.Skip()
            self.SetReturnCode(ID_CANCEL)
            return ID_CANCEL

        with wx.FileDialog(self, message=_("Save Settings to file"), defaultDir=SETTINGS_DIRECTORY,
                           wildcard="*.cfg", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as save_dlg:
            if save_dlg.ShowModal() == wx.ID_CANCEL:
                self.SetReturnCode(ID_CANCEL)
                return ID_CANCEL
            pathname = save_dlg.GetPath()
            """
            filename = os.path.basename(pathname)
            dirname = os.path.dirname(pathname)
            """
            try:
                initialize_settings(self._default_path, pathname)
            except IOError:
                raise RuntimeError(_('Could not open settings file "%s" for writing') % pathname)
        self.SetReturnCode(ID_SAVE)
        self.Close()
        return ID_SAVE

    def load_and_merge(self, user_path):
        try:
            nnew_settings = ConfigObj(user_path, encoding='UTF-8', unrepr=True)
            mysection = nnew_settings.get(self._section)
            if not mysection:
                mysection = nnew_settings['Plugins'].get(self._section)
                if not mysection:
                    raise ConfigurationError(_("Error trying to get '%s' from file %s") % (f"[Plugins][{self._section}]",
                                                                                        user_path))

            for key, value in mysection.items():
                if self._settings.has_setting(key):
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if isinstance(self._settings.get_without_default(key).get_without_default(k), _Section):
                                self._settings[key][k].set_defaults(None, **v)
                            else:
                                self._settings[key].set(k, v)
                    else:
                        self._settings.set(key, value)
            self._settings.save()
        except UnreprError as err:  # DEBUG errored file
            raise ConfigurationError(_("Invalid config file '%s': %s") % (user_path, err))
