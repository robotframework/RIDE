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
import textwrap

from robotide.widgets import HelpLabel, Label, TextField
from robotide.context import IS_WINDOWS


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
                                                  size=self._get_size(choices),
                                                  choices=choices)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)

    def _get_value(self):
        return self.settings[self.key]

    def _get_size(self, choices=[]):
        """ In Linux with GTK3 wxPython 4, there was not enough spacing.
            The value 72 is there for 2 digits numeric lists, for
            IntegerPreferenceComboBox.
        """
        fact = 9 if IS_WINDOWS else 18  # On GTK3 labels are bigger
        if choices:
            return wx.Size(max(max(len(str(s)) for s in choices)*fact, 72), 20)
        return wx.DefaultSize

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


class PreferencesSpinControl(wx.SpinCtrl):
    """A spin control tied to a specific setting. Saves value to disk after edit."""
    def __init__(self, parent, id, settings, key, choices):
        self.settings = settings
        self.key = key
        super(PreferencesSpinControl, self).__init__(parent, id,
            initial=self._get_value(), size=self._get_size(choices[-1]))
        self.SetRange(*choices)
        self.Bind(wx.EVT_SPINCTRL, self.OnChange)
        self.Bind(wx.EVT_TEXT, self.OnChange)

    def _get_value(self):
        return self.settings[self.key]

    def _get_size(self, max_value):
        """ In Linux with GTK3 wxPython 4, there was not enough spacing.
            The value 72 is there for 2 digits numeric lists, for
            IntegerPreferenceComboBox.
        """
        fact = 9 if IS_WINDOWS else 18  # On GTK3 labels are bigger
        if max_value:
            return wx.Size(max(len(str(max_value))*fact, 72), 20)
        return wx.DefaultSize

    def OnChange(self, event):
        self._set_value(event.GetEventObject().GetValue())
        self.settings.save()

    def _set_value(self, value):
        self.settings[self.key] = value


class PreferencesColorPicker(wx.ColourPickerCtrl):
    """A colored button that opens a color picker dialog"""
    def __init__(self, parent, id, settings, key):
        self.settings = settings
        self.key = key
        value = settings[key]
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            super(PreferencesColorPicker, self).__init__(parent, id,
                                                         colour=value)
        else:
            super(PreferencesColorPicker, self).__init__(parent, id, col=value)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnPickColor)

    def OnPickColor(self, event):
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

    def __init__(self, settings, setting_name, label, choices, help=''):
        self._settings = settings
        self._setting_name = setting_name
        self._label = label
        self._choices = choices
        self._help = help

    def chooser(self, parent):
        return self._editor_class(parent, wx.ID_ANY, self._settings,
                                  key=self._setting_name, choices=self._choices)

    def label(self, parent):
        return wx.StaticText(parent, wx.ID_ANY, self._label)

    def help(self, parent):
        return HelpLabel(parent, '\n'.join(textwrap.wrap(self._help, 60)))


class StringChoiceEditor(_ChoiceEditor):
    _editor_class = PreferencesComboBox


class IntegerChoiceEditor(_ChoiceEditor):
    _editor_class = IntegerPreferenceComboBox


class SpinChoiceEditor(_ChoiceEditor):
    _editor_class = PreferencesSpinControl


def boolean_editor(parent, settings, name, label, help=''):
    editor = _create_checkbox_editor(parent, settings, name, help)
    label = Label(parent, label=label)
    return label, editor


def _create_checkbox_editor(parent, settings, name, help):
    initial_value = settings.get(name, "")
    editor = wx.CheckBox(parent)
    editor.SetValue(initial_value)
    editor.Bind(wx.EVT_CHECKBOX,
                lambda evt: settings.set(name, editor.GetValue()))
    MySetToolTip(editor, help)
    return editor


def comma_separated_value_editor(parent, settings, name, label, help=''):
    initial_value = ', '.join(settings.get(name, ""))
    editor = TextField(parent, initial_value)
    MySetToolTip(editor, help)

    def set_value():
        new_value = [token.strip() for token in editor.GetValue().split(',')
                     if token.strip()]
        settings.set(name, new_value)
    editor.Bind(wx.EVT_KILL_FOCUS, lambda evt: set_value())

    return Label(parent, label=label), editor


def MySetToolTip(obj, tip):
    if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
        obj.SetToolTip(tip)
    else:
        obj.SetToolTipString(tip)
