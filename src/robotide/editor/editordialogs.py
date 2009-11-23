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

import wx

from robotide import utils
from robotide.validators import ScalarVariableNameValidator,\
    ListVariableNameValidator, TimeoutValidator, NonEmptyValidator, ArgumentsValidator

from fieldeditors import ValueEditor, MultiLineEditor, ContentAssistEditor
from dialoghelps import get_help


class _Dialog(wx.Dialog):
    _title = property(lambda self: utils.name_from_class(self, drop='Dialog'))

    def __init__(self, parent, item=None, datafile=None):
        wx.Dialog.__init__(self, parent, -1, self._title,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME)
        self.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
        self._item = item
        self.datafile = datafile
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._editors = self._get_editors(item)
        for editor in self._editors:
            self._sizer.Add(editor, 1, wx.EXPAND)
        self._create_help()
        self._create_line()
        self._create_buttons()
        self.SetSizer(self._sizer)
        self._sizer.Fit(self)
        self._editors[0].set_focus()

    def _create_line(self):
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        self._sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

    def _create_help(self):
        text = wx.StaticText(self, label=get_help(self._title))
        text.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTWEIGHT_NORMAL,
                             wx.FONTSTYLE_NORMAL))
        self._sizer.Add(text, flag=wx.ALL, border=2)

    def _create_buttons(self):
        buttons = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self._sizer.Add(buttons, 0, wx.ALIGN_CENTER|wx.ALL, 5)

    def get_value(self):
        values = [ e.get_value() for e in self._editors ]
        if len(values) == 1:
            return values[0]
        return values


class _VariableDialog(_Dialog):

    def _get_editors(self, var):
        name, value = var or (self._empty_name, '')
        return [ValueEditor(self, name, 'Name', validator=self._validator()),
                ValueEditor(self, value, 'Value')]

class ScalarVariableDialog(_VariableDialog):
    _empty_name = '${}'
    _validator = ScalarVariableNameValidator

class ListVariableDialog(_VariableDialog):
    _empty_name = '@{}'
    _validator = ListVariableNameValidator


class LibraryImportDialog(_Dialog):

    def _get_editors(self, item):
        value = item and item.get_str_value() or ''
        return [ValueEditor(self, value, 
                            validator=NonEmptyValidator(self._title))]

class VariablesImportDialog(LibraryImportDialog):
    _title = 'Variable Import'

class ResourceImportDialog(LibraryImportDialog):
    pass


class DocumentationDialog(_Dialog):

    def _get_editors(self, doc):
        return [MultiLineEditor(self, doc)]

    def get_value(self):
        return _Dialog.get_value(self)


class _SettingDialog(_Dialog):
    _validator = None

    def _get_editors(self, item):
        editor = ValueEditor(self, item.get_str_value())
        if self._validator:
            editor.set_validator(self._validator())
        return [editor]


class ForceTagsDialog(_SettingDialog):
    pass

class DefaultTagsDialog(_SettingDialog):
    pass

class TagsDialog(_SettingDialog):
    pass


class _FixtureDialog(_SettingDialog):

    def _get_editors(self, item):
        return [ContentAssistEditor(self, item.get_str_value())]

class SuiteSetupDialog(_FixtureDialog):
    pass

class SuiteTeardownDialog(_FixtureDialog):
    pass

class TestSetupDialog(_FixtureDialog):
    pass

class TestTeardownDialog(_FixtureDialog):
    pass

class SetupDialog(_FixtureDialog):
    pass

class TeardownDialog(_FixtureDialog):
    pass


class ArgumentsDialog(_SettingDialog):
    _validator = ArgumentsValidator

class ReturnValueDialog(_SettingDialog):
    pass

class TestTimeoutDialog(_SettingDialog):
    _validator = TimeoutValidator

class TimeoutDialog(TestTimeoutDialog):
    pass


class MetadataDialog(_Dialog):

    def _get_editors(self, item):
        name, value = item and (item.name, item.value) or ('', '')
        return [ValueEditor(self, name, 'Name'),
                ValueEditor(self, value, 'Value')]
