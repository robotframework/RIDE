#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

from robotide.preferences import PreferencesPanel, PreferencesColorPicker
from robotide.context import SETTINGS


class ColorPreferences(PreferencesPanel):
    location = ("Grid Colors",)
    title = "Grid Colors"
    def __init__(self, *args, **kwargs):
        super(ColorPreferences, self).__init__(*args, **kwargs)

        # N.B. There really ought to be a "reset colors to defaults"
        # button, in case the user gets things hopelessly mixed up

        # what would make this UI much more usable is if there were a
        # preview window in the dialog that showed all the colors. I
        # don't have the time to do that right now, so this will have
        # to suffice.
        main_sizer = wx.GridBagSizer()
        row = 0
        for key, label in (
            ("text user keyword", "User Keyword Foreground"),
            ("text library keyword", "Library Keyword Foreground"),
            ("text commented", "Comments Foreground"),
            ("text variable", "Variable Foreground"),
            ("text string","Default Foreground"),
            ("text empty", "Empty Foreground"),
            ):
            lbl = wx.StaticText(self, wx.ID_ANY, label)
            btn = PreferencesColorPicker(self, wx.ID_ANY, SETTINGS["Colors"], key)
            main_sizer.Add(btn, (row, 0), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=4)
            main_sizer.Add(lbl, (row, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=4)
            row += 1

        row = 0
        for key, label in (
            ("background assign", "Variable Background"),
            ("background keyword", "Keyword Background"),
            ("background mandatory", "Mandatory Field Background"),
            ("background optional", "Optional Field Background"),
            ("background must be empty", "Mandatory Empty Field Background"),
            ("background unknown", "Unknown Background"),
            ("background error", "Error Background"),
            ("background highlight", "Highlight Background")
            ):

            lbl = wx.StaticText(self, wx.ID_ANY, label)
            btn = PreferencesColorPicker(self, wx.ID_ANY, SETTINGS["Colors"], key)
            main_sizer.Add(btn, (row, 2), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=4)
            main_sizer.Add(lbl, (row, 3), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=4)
            row += 1

        self.SetSizer(main_sizer)


class ColorPicker(wx.Panel):
    """A panel with a color picker and a label"""
    def __init__(self, parent, label, key):
        super(ColorPicker, self).__init__(parent, wx.ID_ANY)

        self.key = key
        color = SETTINGS["Colors"][key]
        label = wx.StaticText(self, wx.ID_ANY, label)
        button = wx.ColourPickerCtrl(self, wx.ID_ANY)
        button.SetColour(color)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(label, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, 10)
        self.SetSizer(sizer)
