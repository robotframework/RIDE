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

import builtins
import textwrap

import wx

from ..context import IS_LINUX
from ..widgets import HelpLabel, Label, TextField

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class PreferencesPanel(wx.Panel):
    """Base class for all preference panels used by PreferencesDialog"""

    def __init__(self, parent=None, name_tr=None, *args, **kwargs):
        self.tree_item = None
        self.name_tr = name_tr
        from ..preferences.settings import RideSettings
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self._gsettings = RideSettings()
        self.settings = self._gsettings['General']
        self.background_color = self.settings['background']
        self.foreground_color = self.settings['foreground']
        self.secondary_background_color = self.settings['secondary background']
        self.secondary_foreground_color = self.settings['secondary foreground']
        self.SetBackgroundColour(self.background_color)
        self.SetForegroundColour(self.foreground_color)

    def GetTitle(self):
        return getattr(self, "title", self.location[-1])

    def Separator(self, parent, title):
        """Creates a simple horizontal separator with title"""
        container = wx.Panel(parent, wx.ID_ANY)
        label = wx.StaticText(container, wx.ID_ANY, label=title)
        label.SetBackgroundColour(self.background_color)
        label.SetForegroundColour(self.foreground_color)
        sep = wx.StaticLine(container, wx.ID_ANY)
        sep.SetBackgroundColour(self.secondary_background_color)
        sep.SetForegroundColour(self.secondary_foreground_color)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND|wx.TOP, 8)
        sizer.Add(sep, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)
        container.SetSizerAndFit(sizer)
        return container


class PreferencesComboBox(wx.ComboBox):
    """A combobox tied to a specific setting. Saves value to disk after edit."""
    def __init__(self, parent, elid, settings, key, choices):
        self.settings = settings
        self.key = key
        from ..preferences.settings import RideSettings
        super(PreferencesComboBox, self).__init__(parent, elid, self._get_value(),
                                                  size=self._get_size(choices),
                                                  choices=choices, style=wx.CB_READONLY)
        self._gsettings = RideSettings()
        self.gsettings = self._gsettings['General']
        background_color = self.gsettings['secondary background']
        foreground_color = self.gsettings['secondary foreground']
        self.SetBackgroundColour(background_color)
        self.SetForegroundColour(foreground_color)
        self.Bind(wx.EVT_COMBOBOX, self.on_select)

    def _get_value(self):
        return self.settings[self.key]

    @staticmethod
    def _get_size(choices=None):
        """ In Linux with GTK3 wxPython 4, there was not enough spacing.
            The value 72 is there for 2 digits numeric lists, for
            IntegerPreferenceComboBox.
            This issue only occurs in Linux, for Mac and Windows using default size.
        """
        if IS_LINUX and isinstance(choices, list):
            return wx.Size(max(max(len(str(s)) for s in choices) * 9, 144), 30)
        return wx.DefaultSize

    def on_select(self, event):
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


class PreferencesSpinControl(wx.SpinCtrl):
    """A spin control tied to a specific setting. Saves value to disk after edit."""

    def __init__(self, parent, elid, settings, key, choices):
        self.settings = settings
        self.key = key
        from ..preferences.settings import RideSettings
        super(PreferencesSpinControl, self).__init__(parent, elid,
            size=self._get_size(choices[-1]))

        self._gsettings = RideSettings()
        self.psettings = self._gsettings['General']
        background_color = self.psettings['background']
        foreground_color = self.psettings['foreground']
        self.SetBackgroundColour(background_color)
        self.SetForegroundColour(foreground_color)
        self.SetRange(*choices)
        self.SetValue(self._get_value())
        self.Bind(wx.EVT_SPINCTRL, self.on_change)
        self.Bind(wx.EVT_TEXT, self.on_change)

    def _get_value(self):
        return self.settings[self.key]

    @staticmethod
    def _get_size(max_value):
        """ In Linux with GTK3 wxPython 4, there was not enough spacing.
            The value 72 is there for 2 digits numeric lists, for
            IntegerPreferenceComboBox.
            This issue only occurs in Linux, for Mac and Windows using default size.
        """
        if IS_LINUX and max_value:
            return wx.Size(max(len(str(max_value)) * 9, 144), 20)
        return wx.DefaultSize

    def on_change(self, event):
        self._set_value(event.GetEventObject().GetValue())
        self.settings.save()

    def _set_value(self, value):
        self.settings[self.key] = value


class PreferencesColorPicker(wx.ColourPickerCtrl):
    """A colored button that opens a color picker dialog"""
    def __init__(self, parent, elid, settings, key):
        self.settings = settings
        self.key = key
        # print(f"DEBUG: Preferences ColourPicker value type {type(settings[key])}")
        value = wx.Colour(settings[key])
        from ..preferences.settings import RideSettings
        super(PreferencesColorPicker, self).__init__(parent, elid, colour=value)
        self._gsettings = RideSettings()
        self.psettings = self._gsettings['General']
        background_color = self.psettings['background']
        foreground_color = self.psettings['foreground']
        self.SetBackgroundColour(background_color)
        self.SetForegroundColour(foreground_color)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_pick_color)

    def on_pick_color(self, event):
        """Set the color for the given key to the color of the widget"""
        color = event.GetColour()
        rgb = color.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        self.settings[self.key] = rgb
        self.settings.save()

    def SetColour(self, colour):
        super(PreferencesColorPicker, self).SetColour(colour)
        self.settings[self.key] = colour
        self.settings.save()


class _ChoiceEditor(object):
    _editor_class = None

    def __init__(self, settings, setting_name, label, choices, elhelp=''):
        self._settings = settings
        self._setting_name = setting_name
        self._label = label
        self._choices = choices
        self._help = elhelp
        from ..preferences.settings import RideSettings
        self._gsettings = RideSettings()
        self.csettings = self._gsettings['General']
        self.background_color = self.csettings['background']
        self.foreground_color = self.csettings['foreground']

    def chooser(self, parent):
        element = self._editor_class(parent, wx.NewId(), self._settings,
                                     key=self._setting_name, choices=self._choices)
        element.SetBackgroundColour(self.background_color)
        element.SetForegroundColour(self.foreground_color)
        return element

    def label(self, parent):
        llabel = wx.StaticText(parent, wx.NewId(), self._label)
        llabel.SetBackgroundColour(self.background_color)
        llabel.SetForegroundColour(self.foreground_color)
        return llabel

    def help(self, parent):
        return HelpLabel(parent, '\n'.join(textwrap.wrap(self._help, 60)))


class StringChoiceEditor(_ChoiceEditor):
    _editor_class = PreferencesComboBox

    def SetSelection(self, combo, idx):
        self._editor_class.SetSelection(combo, idx)


class IntegerChoiceEditor(_ChoiceEditor):
    _editor_class = IntegerPreferenceComboBox


class SpinChoiceEditor(_ChoiceEditor):
    _editor_class = PreferencesSpinControl


def boolean_editor(parent, settings, name, label, elhelp=''):
    editor = _create_checkbox_editor(parent, settings, name, elhelp)
    from ..preferences.settings import RideSettings
    _gsettings = RideSettings()
    bsettings = _gsettings['General']
    background_color = bsettings['background']
    foreground_color = bsettings['foreground']
    editor.SetBackgroundColour(background_color)
    editor.SetForegroundColour(foreground_color)
    blabel = Label(parent, label=label)
    blabel.SetBackgroundColour(background_color)
    blabel.SetForegroundColour(foreground_color)
    return blabel, editor


def _create_checkbox_editor(parent, settings, name, elhelp):
    initial_value = settings.get(name, "")
    editor = wx.CheckBox(parent)
    editor.SetValue(initial_value)
    editor.Bind(wx.EVT_CHECKBOX, lambda evt: settings.set(name, editor.GetValue()))
    editor.SetToolTip(elhelp)
    return editor


def comma_separated_value_editor(parent, settings, name, label, thelp=''):
    initial_value = ', '.join(settings.get(name, ""))
    editor = TextField(parent, initial_value)
    from ..preferences.settings import RideSettings
    _gsettings = RideSettings()
    esettings = _gsettings['General']
    background_color = esettings['background']
    foreground_color = esettings['foreground']
    editor.SetBackgroundColour(background_color)
    editor.SetForegroundColour(foreground_color)
    editor.SetToolTip(thelp)

    def set_value(evt):
        new_value = [token.strip() for token in editor.GetValue().split(',')
                     if token.strip()]
        settings.set(name, new_value)
        evt.Skip()
    editor.Bind(wx.EVT_KILL_FOCUS, lambda evt: set_value(evt))
    elabel = Label(parent, label=label)
    elabel.SetBackgroundColour(background_color)
    elabel.SetForegroundColour(foreground_color)
    return elabel, editor
