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

import os
import wx
from wx.lib.filebrowsebutton import DirBrowseButton

from robotide.controller.filecontrollers import ResourceFileController
from robotide.controller.ctrlcommands import CreateNewResource,\
    AddTestDataDirectory, AddTestCaseFile, CreateNewDirectoryProject,\
    CreateNewFileProject, SetFileFormat, SetFileFormatRecuresively
from robotide.utils import overrides
from robotide.widgets import Label, Dialog
from robotide.validators import NonEmptyValidator, NewSuitePathValidator,\
    SuiteFileNameValidator
# This hack needed to set same label width as with other labels
DirBrowseButton.createLabel = lambda self:\
    Label(self, size=(110, -1), label=self.labelText)


class _CreationDialog(Dialog):

    formats = ["ROBOT", "TXT", "TSV", "HTML"]

    def __init__(self, default_dir, title):
        sizer = self._init_dialog(title)
        label_sizer = wx.BoxSizer(wx.VERTICAL)
        self._title = title
        self._name_editor = self._create_name_editor(label_sizer)
        self._parent_chooser = self._create_parent_chooser(
            label_sizer, default_dir)
        self._path_display = self._create_path_display(
            label_sizer, default_dir)
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
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        return wx.BoxSizer(wx.VERTICAL)

    def _finalize_dialog(self, sizer):
        self._create_horizontal_line(sizer)
        self._create_buttons(sizer)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def _create_name_editor(self, sizer):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, "Name")
        name_editor = wx.TextCtrl(self)
        name_editor.SetValidator(NonEmptyValidator("Name"))
        self.Bind(wx.EVT_TEXT, self.OnPathChanged, name_editor)
        disp_sizer.Add(name_editor, 1, wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 3)
        sizer.Add(disp_sizer, 1, wx.EXPAND)
        return name_editor

    def _add_label(self, sizer, text):
        label = Label(self, label=text, size=(110, -1))
        sizer.Add(label, flag=wx.CENTER | wx.ALL, border=3)

    def _create_type_chooser(self, sizer):
        return self._create_radiobuttons(sizer, "Type", ["File", "Directory"])

    def _create_format_chooser(self, sizer, callback=True):
        formats = list(self.formats)
        if (hasattr(self, '_controller') and
            isinstance(self._controller, ResourceFileController)) or\
                (hasattr(self, '_title') and self._title == "New Resource File"):
                formats += ["RESOURCE"]
        return self._create_radiobuttons(sizer, "Format", formats, callback)

    def _create_radiobuttons(self, sizer, label, choices, callback=True):
        radios = wx.RadioBox(self, label=label, choices=choices, majorDimension=4)
        if callback:
            self.Bind(wx.EVT_RADIOBOX, self.OnPathChanged, radios)
        sizer.Add(radios, flag=wx.ALIGN_LEFT | wx.RA_SPECIFY_ROWS | wx.ALL, border=5)
        return radios

    def _create_parent_chooser(self, sizer, default_dir):
        browser = DirBrowseButton(self, labelText="Parent Directory",
                                  dialogTitle="Choose Parent Directory",
                                  startDirectory=default_dir,
                                  size=(600, -1), newDirectory=True,
                                  changeCallback=self.OnPathChanged)
        browser.SetValue(default_dir)
        sizer.Add(browser, 1, wx.EXPAND)
        return browser

    def _create_parent_display(self, sizer, path):
        return self._create_display(sizer, "Parent Directory", path)

    def _create_path_display(self, sizer, path):
        return self._create_display(sizer, "Created Path", path,
                                    NewSuitePathValidator())

    def _create_display(self, sizer, title, value, validator=None):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, title)
        disp = wx.TextCtrl(self, value=value)
        disp.SetSizeHints(self.GetTextExtent(value)[0]+100, -1)
        disp.SetEditable(False)
        disp.SetBackgroundColour("grey")
        if validator:
            disp.SetValidator(validator)
        disp_sizer.Add(disp, 1, wx.ALL | wx.EXPAND, 3)
        sizer.Add(disp_sizer, 1, wx.EXPAND)
        return disp

    def _get_path(self):
        name = self._name_editor.GetValue()
        path = os.path.join(self._parent_chooser.GetValue(),
                            name.replace(' ', '_'))
        if self._is_dir_type():
            path = os.path.join(path, '__init__')
        return path + '.' + self._get_extension()

    def _is_dir_type(self):
        if not self._type_chooser:
            return False
        return self._type_chooser.GetStringSelection() == "Directory"

    def _get_extension(self):
        if not self._format_chooser:
            return 'html'
        return self._format_chooser.GetStringSelection().lower()

    def OnPathChanged(self, event):
        if not hasattr(self, "_path_display"):
            return
        self._path_display.SetValue(self._get_path())
        event.Skip()


class _WithImmutableParent(object):

    def _create_parent_chooser(self, sizer, default_dir):
        return self._create_parent_display(sizer, self._path)


class NewProjectDialog(_CreationDialog):

    def __init__(self, project):
        self._controller = project
        _CreationDialog.__init__(self, project.default_dir, "New Project")

    def _execute(self):
        cmd = CreateNewDirectoryProject if self._is_dir_type()\
            else CreateNewFileProject
        cmd(self._get_path()).execute(self._controller)


class NewResourceDialog(_WithImmutableParent, _CreationDialog):

    def __init__(self, controller, settings):
        self._path = controller.directory
        _CreationDialog.__init__(self, controller.default_dir,
                                 "New Resource File")
        self._format_chooser.SetStringSelection(
            settings.get("default file format", "robot"))
        self._controller = controller

    def _execute(self):
        self._controller.execute(CreateNewResource(self._get_path()))

    def _create_type_chooser(self, sizer):
        return None


class AddSuiteDialog(_WithImmutableParent, _CreationDialog):

    NAME = "Add Suite"

    def __init__(self, controller, settings):
        self._controller = controller
        self._path = controller.directory
        _CreationDialog.__init__(self, self._path, self.NAME)
        self._format_chooser.SetStringSelection(
            settings.get("default file format", "robot"))

    @overrides(_CreationDialog)
    def _create_name_editor(self, sizer):
        name_editor = _CreationDialog._create_name_editor(self, sizer)
        name_editor.SetValidator(
            SuiteFileNameValidator("Name", self._is_dir_type))
        return name_editor

    def _execute(self):
        cmd = AddTestDataDirectory if self._is_dir_type() else AddTestCaseFile
        self._controller.execute(cmd(self._get_path()))


class AddDirectoryDialog(AddSuiteDialog):

    NAME = "Add Directory"

    def _create_type_chooser(self, sizer):
        return None

    def _is_dir_type(self):
        return True


class _FileFormatDialog(_CreationDialog):

    def __init__(self, controller):
        sizer = self._init_dialog("Set Data Format")
        self._controller = controller
        self._create_help(sizer)
        self._chooser = self._create_format_chooser(sizer, callback=False)
        self._chooser.SetStringSelection(controller.get_format() or "TXT")
        self._recursive = self._create_recursion_selector(sizer)
        self._finalize_dialog(sizer)

    def _create_help(self, sizer):
        pass

    def _create_recursion_selector(self, sizer):
        return None

    def _get_format(self):
        return self._chooser.GetStringSelection()


class ChangeFormatDialog(_FileFormatDialog):

    def _create_recursion_selector(self, sizer):
        if not self._controller.is_directory_suite():
            return None
        selector = wx.CheckBox(self, label="Change recursively")
        selector.SetValue(True)
        sizer.Add(selector, flag=wx.ALL, border=5)
        return selector

    def _execute(self):
        cmd = SetFileFormat if not self._get_recursive() \
            else SetFileFormatRecuresively
        self._controller.execute(cmd(self._get_format()))

    def _get_recursive(self):
        return self._recursive and self._recursive.IsChecked()


class InitFileFormatDialog(_FileFormatDialog):

    def _create_help(self, sizer):
        help = "Provide format for initialization file in directory\n\"%s\"." \
               % self._controller.directory
        sizer.Add(Label(self, label=help), flag=wx.ALL, border=5)

    def _execute(self):
        self._controller.execute(SetFileFormat(self._get_format()))


class RobotFilePathDialog(wx.FileDialog):

    def __init__(self, window, controller, settings):
        self._controller = controller
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            style = wx.FD_OPEN
        else:
            style = wx.OPEN
        wx.FileDialog.__init__(
            self, window, style=style, wildcard=self._get_wildcard(settings),
            defaultDir=self._controller.default_dir, message="Open")

    def _get_wildcard(self, settings):
        fileTypes = [
            ("robot", "Robot data (*.robot)|*.robot"),
            ("txt", "Robot data (*.txt)|*.txt"),
            ("all", "All files|*.*")
        ]
        default_format = settings.get("default file format", "robot")
        if default_format not in ["robot", "txt"]:
            default_format = "all"
        first = [ft for ft in fileTypes if ft[0] == default_format]
        rest = [ft for ft in fileTypes if ft[0] != default_format]
        return '|'.join(ft[1] for ft in first + rest)

    def execute(self):
        if self.ShowModal() == wx.ID_OK:
            path = self.GetPath()
            self._controller.update_default_dir(path)
        else:
            path = None
        self.Destroy()
        return path
