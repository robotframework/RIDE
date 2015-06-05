#  Copyright 2008-2015 Nokia Solutions and Networks
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


class PreferencesPanel(wx.Panel):
    """Base class for all preference panels used by PreferencesDialog"""
    location = ("Preferences",)
    title = "Preferences"

    def __init__(self, parent=None, *args, **kwargs):
        self.tree_item = None
        wx.Panel.__init__(self, parent, *args, **kwargs)

    def GetTitle(self):
        return getattr(self, "title", self.location[-1])

    def Separator(self, parent, title):
        """Creates a simple horizontal separator with title"""
        container = wx.Panel(parent, wx.ID_ANY)
        label = wx.StaticText(container, wx.ID_ANY, label=title)
        sep = wx.StaticLine(container, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND|wx.TOP, 8)
        sizer.Add(sep, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)
        container.SetSizerAndFit(sizer)
        return container


class PreferencesComboBox(wx.ComboBox):
    """A combobox tied to a specific setting. Saves value to disk after edit."""
    def __init__(self, parent, id, settings, key, choices):
        self.settings = settings
        self.key = key
        super(PreferencesComboBox, self).__init__(parent, id, self._get_value(),
                                                  choices=choices)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)

    def _get_value(self):
        return self.settings[self.key]

    def OnSelect(self, event):
        self._set_value(str(event.GetEventObject().GetValue()))
        self.settings.save()

    def _set_value(self, value):
        self.settings[self.key] = value


class IntegerPreferenceComboBox(PreferencesComboBox):
    """A combobox tied to a setting that has integer values."""

    def _get_value(self):
        return str(self.settings[self.key])

    def _set_value(self, value):
        self.settings[self.key] = int(value)


class PreferencesColorPicker(wx.ColourPickerCtrl):
    """A colored button that opens a color picker dialog"""
    def __init__(self, parent, id, settings, key):
        self.settings = settings
        self.key = key
        value = settings[key]
        super(PreferencesColorPicker, self).__init__(parent, id, col=value)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnPickColor)

    def OnPickColor(self, event):
        """Set the color for the given key to the color of the widget"""
        color = event.GetColour()
        rgb = "#%02X%02X%02X" % color.asTuple()
        self.settings[self.key] = rgb
        self.settings.save()

    def SetColour(self, colour):
        super(PreferencesColorPicker, self).SetColour(colour)
        self.settings[self.key] = colour
        self.settings.save()
