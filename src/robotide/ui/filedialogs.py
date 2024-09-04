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
import os

import wx
from wx import Colour
from wx.lib.filebrowsebutton import DirBrowseButton
from multiprocessing import shared_memory

from ..controller.ctrlcommands import (CreateNewResource, AddTestDataDirectory, AddTestCaseFile,
                                       CreateNewDirectoryProject, CreateNewFileProject, SetFileFormat,
                                       SetFileFormatRecuresively)
from ..robotapi import ROBOT_VERSION
from ..preferences.general import read_languages, set_colors
from .preferences_dialogs import boolean_editor, StringChoiceEditor
from ..validators import NonEmptyValidator, NewSuitePathValidator, SuiteFileNameValidator
from ..widgets import Label, RIDEDialog
try:
    from robot.conf.languages import Language
except ImportError:
    try:
        from ..lib.compat.parsing.languages import Language
    except ImportError:
        Language = None


_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

# This hack needed to set same label width as with other labels
DirBrowseButton.createLabel = lambda self: Label(self, size=(110, -1), label=self.labelText)

DEFAULT_FFORMAT = "default file format"
DOC_LANGUAGE = 'doc language'


class _CreationDialog(RIDEDialog):

    formats = ["ROBOT", "TXT", "TSV"]  # Removed "HTML"

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
        sizer.Add(edit_sizer)  # , 1, wx.EXPAND)
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._task_chooser = self._create_task_chooser(self, content_sizer)
        self._language_chooser = self._create_lang_chooser(content_sizer)
        sizer.Add(content_sizer, 1, wx.EXPAND)
        self._finalize_dialog(sizer)
        self._name_editor.SetFocus()

    def _init_dialog(self, title):
        RIDEDialog.__init__(self, title)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        return wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)  # wx.BoxSizer(wx.VERTICAL)

    def _finalize_dialog(self, sizer):
        self._create_horizontal_line(sizer)
        self._create_buttons(sizer)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def _create_name_editor(self, sizer):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, _("Name"))
        name_editor = wx.TextCtrl(self)
        name_editor.SetValidator(NonEmptyValidator(_("Name")))
        name_editor.SetBackgroundColour(Colour(self.color_secondary_background))
        name_editor.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.Bind(wx.EVT_TEXT, self.on_path_changed, name_editor)
        if wx.VERSION < (4, 1, 0):
            disp_sizer.Add(name_editor, 1, wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 3)
        else:
            disp_sizer.Add(name_editor, 1, wx.ALL | wx.EXPAND, 3)
        sizer.Add(disp_sizer, 1, wx.EXPAND)
        return name_editor

    def _add_label(self, sizer, text):
        label = Label(self, label=text, size=(110, -1))
        sizer.Add(label, flag=wx.CENTER | wx.ALL, border=3)

    def _create_type_chooser(self, sizer):
        return self._create_radiobuttons(sizer, _("Type"), [_("File"), _("Directory")])

    def _create_task_chooser(self, window, sizer):
        from ..preferences import RideSettings
        _settings = RideSettings()
        label, selector = boolean_editor(window, _settings, 'tasks',
                                         ' '+_("Is Task?")+' ', _("Default for Tasks or Tests sections."))
        selector.SetBackgroundColour(Colour(self.color_background))
        selector.SetForegroundColour(Colour(self.color_foreground))
        # self.Bind(wx.EVT_CHECKBOX, self.on_path_changed, selector)
        task_box = wx.BoxSizer(wx.HORIZONTAL)
        task_box.AddMany([label, selector])
        sizer.Add(task_box, flag=wx.ALIGN_LEFT)
        return selector

    def _create_lang_chooser(self, sizer):
        from ..preferences import RideSettings
        from ..lib.compat.parsing.language import get_language_name
        _settings = RideSettings()
        lang = _settings.get(DOC_LANGUAGE, '')
        languages = read_languages()
        if languages[0] != '':
            languages.insert(0, '')
        # Remove non-existing languages
        for value in languages:
            if ROBOT_VERSION < (6, 1, 0) and value == 'Vietnamese':
                languages.remove(value)
            if ROBOT_VERSION < (7, 0, 1) and value == 'Japanese':
                languages.remove(value)
            if ROBOT_VERSION < (7, 1, ) and value == 'Korean':
                languages.remove(value)
        if isinstance(lang, list) and len(lang) > 0:
            _settings[DOC_LANGUAGE] = lang[0]
            lang = lang[0]
        elif lang and len(lang) > 0:
            _settings[DOC_LANGUAGE] = lang
        else:
            _settings[DOC_LANGUAGE] = ''
        ll = StringChoiceEditor(_settings, DOC_LANGUAGE, _('Language')+' ', languages)
        l_lang = ll.label(self)
        set_colors(l_lang, Colour(self.color_background), Colour(self.color_foreground))
        lang_box = wx.BoxSizer(wx.HORIZONTAL)
        chooser = ll.chooser(self)
        lang_box.AddMany([l_lang, chooser])
        sizer.Add(lang_box)
        sizer.Layout()
        # Force no selection if lang code is en
        if lang in ('en', ):  # We will only consider English as the effective setting
            lang = ''
        lang_name = get_language_name(lang)
        if lang_name in languages:
            index = languages.index(lang_name)
            ll.SetSelection(chooser, index)
        return ll

    def _create_format_chooser(self, sizer, callback=True):
        from ..controller.filecontrollers import ResourceFileController

        formats = list(self.formats)
        if ((hasattr(self, '_controller') and isinstance(self._controller, ResourceFileController)) or
                (hasattr(self, '_title') and self._title == _("New Resource File"))):
            formats += ["RESOURCE"]
        return self._create_radiobuttons(sizer, _("Format"), formats, callback)

    def _create_radiobuttons(self, sizer, label, choices, callback=True):
        radios = wx.RadioBox(self, label=label, choices=choices, majorDimension=4)
        radios.SetBackgroundColour(Colour(self.color_background))
        radios.SetForegroundColour(Colour(self.color_foreground))
        if callback:
            self.Bind(wx.EVT_RADIOBOX, self.on_path_changed, radios)
        sizer.Add(radios, flag=wx.ALIGN_LEFT | wx.RA_SPECIFY_ROWS | wx.ALL, border=5)
        return radios

    def _create_parent_chooser(self, sizer, default_dir):
        browser = DirBrowseButton(self, labelText=_("Parent Directory"),
                                  dialogTitle=_("Choose Parent Directory"),
                                  startDirectory=default_dir,
                                  size=(600, -1), newDirectory=True,
                                  changeCallback=self.on_path_changed)
        browser.SetBackgroundColour(Colour(self.color_background))
        browser.SetForegroundColour(Colour(self.color_foreground))
        # DEBUG: Change colors on buttons and text field
        # browser.SetOwnBackgroundColour(Colour(self.color_secondary_background))
        # browser.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        browser.SetValue(default_dir)
        sizer.Add(browser, 1, wx.EXPAND)
        return browser

    def _create_parent_display(self, sizer, path):
        return self._create_display(sizer, _("Parent Directory"), path)

    def _create_path_display(self, sizer, path):
        return self._create_display(sizer, _("Created Path"), path,
                                    NewSuitePathValidator())

    def _create_display(self, sizer, title, value, validator=None):
        disp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._add_label(disp_sizer, title)
        disp = wx.TextCtrl(self, value=value)
        disp.SetBackgroundColour(Colour(self.color_background))
        disp.SetForegroundColour(Colour(self.color_foreground))
        disp.SetSizeHints(self.GetTextExtent(value)[0]+100, -1)
        disp.SetEditable(False)
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
        return self._type_chooser.GetStringSelection() == _("Directory")

    @staticmethod
    def _is_task_type():
        # if not self._task_chooser:
        #     return False
        from ..preferences import RideSettings
        _settings = RideSettings()
        task = _settings.get('tasks', False)
        # print(f"DEBUG: filedialogs.py _CreationDialog _is_task_type task={task}")
        return task  # self._task_chooser.GetValue()

    def selected_language(self):
        if not self._language_chooser:
            return ['']
        from ..preferences import RideSettings
        _settings = RideSettings()
        lang = _settings.get(DOC_LANGUAGE, '')
        set_lang = shared_memory.ShareableList(name="language")
        if lang and len(lang) > 0:
            if isinstance(lang, list):
                lang = lang[0]
            if lang in ('en',):  # We will only consider English as the effective setting
                return ['en']
            try:
                mlang = Language.from_name(lang.replace('_', '-'))
                set_lang[0] = mlang.code.replace('-', '_')
            except ValueError:  # For the case of missing language, like Ko
                set_lang[0] = 'en'
                return ['en']
        else:
            return ['en']  # [set_lang[0]]
        return [mlang.name]

    def _get_extension(self):
        if not self._format_chooser:
            return 'robot'
        return self._format_chooser.GetStringSelection().lower()

    def on_path_changed(self, event):
        if not hasattr(self, "_path_display"):
            return
        self._path_display.SetValue(self._get_path())
        event.Skip()


class _WithImmutableParent(object):

    def _create_parent_chooser(self, sizer, default_dir):
        _ = default_dir
        return self._create_parent_display(sizer, self._path)


class NewProjectDialog(_CreationDialog):

    def __init__(self, project):
        self._controller = project
        self.dlg = _CreationDialog.__init__(self, project.default_dir, _("New Project"))

    def _execute(self):
        cmd = CreateNewDirectoryProject if self._is_dir_type()\
            else CreateNewFileProject
        self.language = self.selected_language()
        cmd(self._get_path(), self._is_task_type(), self.language).execute(self._controller)
        del self.dlg


class NewResourceDialog(_WithImmutableParent, _CreationDialog):

    def __init__(self, controller, settings):
        self._path = controller.directory
        _CreationDialog.__init__(self, controller.default_dir,
                                 _("New Resource File"))
        self._format_chooser.SetStringSelection(
            settings.get(DEFAULT_FFORMAT, "robot"))
        self._controller = controller

    def _execute(self):
        self._controller.execute(CreateNewResource(self._get_path()))

    def _create_type_chooser(self, sizer):
        return None


class AddSuiteDialog(_WithImmutableParent, _CreationDialog):

    NAME = _("Add Suite")

    def __init__(self, controller, settings):
        self._controller = controller
        self._path = controller.directory
        _CreationDialog.__init__(self, self._path, self.NAME)
        self._format_chooser.SetStringSelection(
            settings.get(DEFAULT_FFORMAT, "robot"))

    def _create_name_editor(self, sizer):
        name_editor = _CreationDialog._create_name_editor(self, sizer)
        name_editor.SetBackgroundColour(Colour(self.color_secondary_background))
        name_editor.SetForegroundColour(Colour(self.color_secondary_foreground))
        name_editor.SetValidator(
            SuiteFileNameValidator(_("Name"), self._is_dir_type))
        return name_editor

    def _execute(self):
        cmd = AddTestDataDirectory if self._is_dir_type() else AddTestCaseFile
        self._controller.execute(cmd(self._get_path()))


class AddDirectoryDialog(AddSuiteDialog):

    NAME = _("Add Directory")

    def _create_type_chooser(self, sizer):
        return None

    def _is_dir_type(self):
        return True


class _FileFormatDialog(_CreationDialog):

    def __init__(self, controller):
        sizer = self._init_dialog(_("Set Data Format"))
        self._controller = controller
        self._create_help(sizer)
        self._chooser = self._create_format_chooser(sizer, callback=False)
        self._chooser.SetStringSelection(controller.get_format() or "TXT")
        self._recursive = self._create_recursion_selector(sizer)
        self._finalize_dialog(sizer)

    def _create_help(self, sizer):
        """ Just ignore it """
        pass

    def _create_recursion_selector(self, sizer):
        return None

    def _get_format(self):
        return self._chooser.GetStringSelection()


class ChangeFormatDialog(_FileFormatDialog):

    def _create_recursion_selector(self, sizer):
        if not self._controller.is_directory_suite():
            return None
        selector = wx.CheckBox(self, label=_("Change recursively"))
        selector.SetBackgroundColour(Colour(self.color_secondary_background))
        selector.SetForegroundColour(Colour(self.color_secondary_foreground))
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
        ihelp = _("Provide format for initialization file in directory\n\"%s\".") \
               % self._controller.directory
        sizer.Add(Label(self, label=ihelp), flag=wx.ALL, border=5)

    def _execute(self):
        self._controller.execute(SetFileFormat(self._get_format()))


class RobotFilePathDialog(wx.FileDialog):

    def __init__(self, window, controller, settings):
        self._controller = controller
        style = wx.FD_OPEN
        wx.FileDialog.__init__(self, window, style=style, wildcard=self._get_wildcard(settings),
                               defaultDir=self._controller.default_dir, message=_("Open"))

    @staticmethod
    def _get_wildcard(settings):
        filetypes = [
            ("robot", _("Robot data (*.robot)|*.robot")),
            ("txt", _("Robot data (*.txt)|*.txt")),
            ("resource", _("Robot resource file (*.resource)|*.resource")),
            ("tsv", _("Robot Tab Separated data (*.tsv)|*.tsv")),
            # ("html", "Robot HTML data (pre 3.2.2) (*.html)|*.html"),
            ("all", _("All files|*.*"))
        ]
        default_format = settings.get(DEFAULT_FFORMAT, "robot")
        robottypes = settings.get('robot types', ['robot', 'resource', 'txt', 'tsv'])  # , 'html'
        if default_format not in robottypes:
            default_format = "all"
        first = [ft for ft in filetypes if ft[0] == default_format]
        rest = [ft for ft in filetypes if ft[0] != default_format]
        return '|'.join(ft[1] for ft in first + rest)

    def execute(self):
        if self.ShowModal() == wx.ID_OK:
            path = self.GetPath()
            self._controller.update_default_dir(path)
        else:
            path = None
        self.Destroy()
        return path
