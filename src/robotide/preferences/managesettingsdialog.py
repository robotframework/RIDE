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

import os
import wx

from wx import Colour
from ..widgets import RIDEDialog, VirtualList, VerticalSizer, ImageList, ImageProvider, ButtonWithHandler
from ..widgets.list import ListModel
from .configobj import ConfigObj, ConfigObjError, UnreprError
from ..publish import RideSettingsChanged
from .settings import ConfigurationError, _Section

from ..context import SETTINGS_DIRECTORY

ID_LOAD= wx.NewId()
ID_SAVE = wx.NewId()
ID_CANCEL = -1


class SaveLoadSettings(RIDEDialog):

    def __init__(self, parent, section):
        self._parent = parent
        self._section = section
        self._selection_listeners = []
        title = "Save or Load Settings"
        RIDEDialog.__init__(self, parent=parent, title=title, size=(650, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        main_sizer = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        buttons_sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        load = wx.Button(self, ID_LOAD, 'Load settings from file...')
        save = wx.Button(self, ID_SAVE, 'Save settings to file...')
        self.SetSizer(VerticalSizer())
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        from ..preferences import RideSettings
        self._settings = RideSettings()
        self._default_path = os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')
        directory = wx.StaticText(self, label=f"Current directory: {SETTINGS_DIRECTORY}")
        """self.usage_list = VirtualList(self, self.usages.headers,
                                      self.usages)
        self.usage_list.SetBackgroundColour(Colour(self.color_secondary_background))
        self.usage_list.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.usage_list.add_selection_listener(self._usage_selected)
        """
        buttons_sizer.Add(load)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(save)
        main_sizer.Add(directory)
        main_sizer.AddSpacer(10)
        main_sizer.Add(buttons_sizer)
        self.SetSizerAndFit(main_sizer)
        self.Bind(wx.EVT_BUTTON, self.OnLoad)
        self.Bind(wx.EVT_BUTTON, self.OnSave)

    def OnLoad(self, event):
        if event.GetId() != ID_LOAD:
            event.Skip()
            return ID_CANCEL
        load_dlg = wx.FileDialog(self, message="File with Settings to Load",
                                 defaultDir=SETTINGS_DIRECTORY, wildcard="*.cfg")
        if load_dlg.ShowModal() == wx.ID_CANCEL:
            return ID_CANCEL
        file = load_dlg.GetPath()
        if os.path.isfile(file):  # Test validity settings
            print(f"DEBUG: Selected file is {file}.")
            self.load_and_merge(file)
            RideSettingsChanged(keys=("General", ''), old='', new='').publish()
            # self._parent.Refresh()
            # wx.CallLater(1000, self._parent.Close)
            self._parent.Close()
            # wx.CallAfter(self._parent.Close)
            self.Close()
            return ID_LOAD

    def OnClose(self):
        return ID_CANCEL

    def OnSave(self, event):
        if event.GetId() != ID_SAVE:
            event.Skip()
            return ID_CANCEL

    def load_and_merge(self, user_path):
        from ..preferences import RideSettings
        # current_settings = ConfigObj(self._default_path, unrepr=True)
        # print("DEBUG: load_and_merge %s\ndefault_path %s" % (current_settings.__repr__(), self._default_path))
        try:
            # new_settings = ConfigObj(user_path, unrepr=True)
            nnew_settings = RideSettings(user_path)
            print("DEBUG: load_and_merge _nnew_settings %s" % (nnew_settings.__repr__()))
            # current_settings.merge(new_settings)
            for key, value in nnew_settings.iteritems():
                print("DEBUG: nnew_settings iteritems key= %s value=%s" % (key, value))
                if self._settings.has_setting(key):
                    if isinstance(self._settings.get_without_default(key), _Section):
                        if isinstance(value, dict):
                            print("DEBUG: load_and_merge SubSection value %s" % value)
                            for k, v in value.items():
                                if isinstance(self._settings.get_without_default(key).get_without_default(k), _Section):
                                    print("DEBUG: load_and_merge SubSection k %s v %s" % (k, v))
                                    self._settings[key][k].set_defaults(None, **v)
                            #print("DEBUG: load_and_merge SubSection key %s" % isinstance(value[0], str) )
                            # print("DEBUG: load_and_merge SubSection %s", self._settings[key[value[0]]] )
                            # self._settings[key[value[0]]].set_defaults(None, value)
                        else:
                            self._settings[key].set_defaults(None, **value)
                    else:
                        self._settings.set(key, value)
            # print("DEBUG: load_and_merge after merge _current_settings %s" % (current_settings.__repr__()))
            # print("DEBUG: Merge after: %s, old%s\n" % (self._default_settings.__repr__(), self._old_settings.__repr__()))
            # self._write_merged_settings(current_settings, self._default_path)
            self._settings.save()
            print("DEBUG: wrote settings %s" % (self._settings.__repr__()))
            # wx.CallLater(1000, RideSettingsChanged(keys=("General", ''), old='', new='').publish)
        except UnreprError as err:  # DEBUG errored file
            # print("DEBUG: Settings migrator ERROR -------- %s path %s" %
            #      (self._old_settings.__repr__(), user_path))
            raise ConfigurationError("Invalid config file '%s': %s" %
                                     (user_path, err))
        # print("DEBUG: Settings migrator old_settings: %s\nuser_path %s" %
        # (self._old_settings.__repr__(), self._user_path))
        # print("DEBUG: Settings migrator default_settings: %s\nsettings_path "
        # "%s" % (self._default_settings.__repr__(), default_path))
        # RideSettingsChanged(keys=("General", ''), old='', new='').publish

    @staticmethod
    def _write_merged_settings(settings, path):
        try:
            with open(path, 'wb') as outfile:  # DEBUG used to be 'wb'
                settings.write(outfile)  # DEBUG .encoding('UTF-8')
        except IOError:
            raise RuntimeError(
                'Could not open settings file "%s" for writing' % path)