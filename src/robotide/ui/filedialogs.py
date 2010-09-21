#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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
from wx.lib.filebrowsebutton import DirBrowseButton
# This hack needed to set same label width as with other labels
DirBrowseButton.createLabel = lambda self: wx.StaticText(self, size=(110, -1),
                                                         label=self.labelText)

from robotide.widgets import Dialog
from robotide.validators import NonEmptyValidator, NewSuitePathValidator


class _CreationDialog(Dialog):

    def __init__(self, default_dir, title):
        sizer = self._init_dialog(title)
        label_sizer = wx.BoxSizer(wx.VERTICAL)
        self._name_editor = self._create_name_editor(label_sizer)
        self._parent_chooser = self._create_parent_chooser(label_sizer, default_dir)
        self._path_display = self._create_path_display(label_sizer, default_dir)
        radio_group_sizer = wx.BoxSizer(wx.VERTICAL)
        self._type_chooser = self._create_type_chooser(radio_group_sizer)
        self._format_chooser = self._create_format_chooser(radio_group_sizer)
        edit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        edit_sizer.Add(label_sizer, 1, wx.EXPAND)
        edit_sizer.Add(radio_group_sizer)
        sizer.Add(edit_sizer, 1, wx.EXPAND)
        self._finalize_dialog(sizer)
        self._name_editor.SetFocus()

    def _init_dialog(self, title):
        Dialog.__init__(self, title)
        return wx.BoxSizer(wx.VERTICAL)

    def _finalize_dialog(self, sizer):
        self._create_line(sizer)
        self._create_buttons(sizer)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def _create_name_editor(self, sizer):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, 'Name')
        name_editor = wx.TextCtrl(self)
        name_editor.SetValidator(NonEmptyValidator('Name'))
        self.Bind(wx.EVT_TEXT, self.OnPathChanged, name_editor)
        disp_sizer.Add(name_editor, 1, wx.ALIGN_CENTRE|wx.ALL|wx.EXPAND, 3)
        sizer.Add(disp_sizer, 1, wx.EXPAND)
        return name_editor

    def _add_label(self, sizer, text):
        label = wx.StaticText(self, label=text, size=(110, -1))
        sizer.Add(label, flag=wx.CENTER|wx.ALL, border=3)

    def _create_type_chooser(self, sizer):
        return self._create_radiobuttons(sizer, 'Type', ['File', 'Directory'])

    def _create_format_chooser(self, sizer, callback=True):
        return self._create_radiobuttons(sizer, 'Format', ['HTML', 'TSV', 'TXT'],
                                         callback)

    def _create_radiobuttons(self, sizer, label, choices, callback=True):
        radios = wx.RadioBox(self, label=label, choices=choices)
        if callback:
            self.Bind(wx.EVT_RADIOBOX, self.OnPathChanged, radios)
        sizer.Add(radios, flag=wx.ALIGN_LEFT|wx.ALL, border=5)
        return radios

    def _create_parent_chooser(self, sizer, default_dir):
        browser = DirBrowseButton(self, labelText='Parent Directory',
                                  dialogTitle='Choose Parent Directory',
                                  startDirectory=default_dir,
                                  size=(600, -1), newDirectory=True,
                                  changeCallback=self.OnPathChanged)
        browser.SetValue(default_dir)
        sizer.Add(browser, 1, wx.EXPAND)
        return browser

    def _create_parent_display(self, sizer, path):
        return self._create_display(sizer, 'Parent Directory', path)

    def _create_path_display(self, sizer, path):
        return self._create_display(sizer, 'Created Path', path,
                                    NewSuitePathValidator())

    def _create_display(self, sizer, title, value, validator=None):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, title)
        disp = wx.TextCtrl(self, value=value)
        disp.SetSizeHints(self.GetTextExtent(value)[0]+100, -1)
        disp.SetEditable(False)
        disp.SetBackgroundColour('grey')
        if validator:
            disp.SetValidator(validator)
        disp_sizer.Add(disp, 1, wx.ALL|wx.EXPAND, 3)
        sizer.Add(disp_sizer, 1, wx.EXPAND)
        return disp

    def _create_line(self, sizer):
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP,
                  border=5)

    def _create_buttons(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        sizer.Add(buttons, flag=wx.ALIGN_CENTER|wx.ALL, border=5)

    def get_name(self):
        return self._name_editor.GetValue()

    def get_directory(self):
        return self._parent_chooser.GetValue()

    def get_path(self):
        path = os.path.join(self._parent_chooser.GetValue(),
                            self._name_editor.GetValue().replace(' ', '_'))
        if self.is_dir_type():
            path = os.path.join(path, '__init__')
        return path + '.' + self._get_extension()

    def is_dir_type(self):
        if not self._type_chooser:
            return False
        return self._type_chooser.GetStringSelection() == 'Directory'

    def _get_extension(self):
        if not self._format_chooser:
            return 'html'
        return self._format_chooser.GetStringSelection().lower()

    def OnPathChanged(self, event):
        if not hasattr(self, '_path_display'):
            return
        self._path_display.SetValue(self.get_path())
        event.Skip()


class NewProjectDialog(_CreationDialog):

    def __init__(self, default_dir):
        _CreationDialog.__init__(self, default_dir, 'New Project')


class NewResourceDialog(_CreationDialog):

    def __init__(self, default_dir):
        _CreationDialog.__init__(self, default_dir, 'New Resource File')

    def _create_type_chooser(self, sizer):
        return None


class AddSuiteDialog(_CreationDialog):

    def __init__(self, path):
        self._path = path
        _CreationDialog.__init__(self, path, 'Add Suite')

    def _create_parent_chooser(self, sizer, default_dir):
        return self._create_parent_display(sizer, self._path)


class ChangeFormatDialog(_CreationDialog):

    def __init__(self, default_format, allow_recursive=False,
                 help_text=None):
        sizer = self._init_dialog('Data Format')
        self._create_help(sizer, help_text)
        self._chooser = self._create_format_chooser(sizer, callback=False)
        self._chooser.SetStringSelection(default_format)
        self._recursive = self._create_recursion_selector(sizer, allow_recursive)
        self._finalize_dialog(sizer)

    def _create_help(self, sizer, help_text):
        if help_text:
            help = wx.StaticText(self, label=help_text)
            sizer.Add(help, flag=wx.ALL, border=5)

    def _create_recursion_selector(self, sizer, recursive):
        if not recursive:
            return None
        selector = wx.CheckBox(self, label='Change recursively')
        selector.SetValue(True)
        sizer.Add(selector, flag=wx.ALL, border=5)
        return selector

    def get_format(self):
        return self._chooser.GetStringSelection()

    def get_recursive(self):
        if not self._recursive:
            return False
        return self._recursive.IsChecked()
