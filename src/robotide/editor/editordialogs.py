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

from robotide.namespace.suggesters import ResourceSuggester, \
    LibrariesSuggester, HistorySuggester
from robotide.validators import ScalarVariableNameValidator, \
    ListVariableNameValidator, TimeoutValidator, ArgumentsValidator, \
    TestCaseNameValidator, UserKeywordNameValidator, \
    DictionaryVariableNameValidator
from robotide import utils
from robotide.widgets import HelpLabel, Dialog

from .fieldeditors import ValueEditor, ListValueEditor, MultiLineEditor,\
    ContentAssistEditor, VariableNameEditor, ArgumentEditor, FileNameEditor
from .formatters import ListToStringFormatter
from .dialoghelps import get_help


def EditorDialog(obj):
    return globals()[obj.label.replace(' ', '') + 'Dialog']


class _Dialog(Dialog):
    _title = property(lambda self: utils.name_from_class(self, drop='Dialog'))

    def __init__(self, controller, item=None, plugin=None):
        # TODO: Get rid of item, everything should be in controller
        Dialog.__init__(self, self._title)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
        self._controller = controller
        self.plugin = plugin
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._editors = self._get_editors(item)
        for editor in self._editors:
            self._sizer.Add(editor, editor.expand_factor, wx.EXPAND)
        self._add_comment_editor(item)
        self._create_help()
        self._create_line()
        self._create_buttons()
        self.SetSizer(self._sizer)
        self._sizer.Fit(self)
        self._editors[0].set_focus()

    def _add_comment_editor(self, item):
        comment = ListToStringFormatter(item.comment).value if item else ''
        self._comment_editor = ValueEditor(self, comment, 'Comment')
        self._sizer.Add(self._comment_editor)

    def _create_line(self):
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        self._sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

    def _create_help(self):
        self._sizer.Add(HelpLabel(self, label=get_help(self._title)),
                        flag=wx.ALL, border=2)

    def _create_buttons(self, **kwargs):
        buttons = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self._sizer.Add(buttons, 0, wx.ALIGN_CENTER|wx.ALL, 5)

    def get_value(self):
        return [ e.get_value() for e in self._editors ]

    def get_comment(self):
        return self._comment_editor.get_value()

    def setFocusToOK(self):
        self.FindWindowById(wx.ID_OK).SetFocus()

    def _execute(self):
        pass


class ScalarVariableDialog(_Dialog):

    def _get_editors(self, var):
        name = var.name if var and var.name else '${}'
        value = var.value[0] if var else ''
        validator = ScalarVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, 'Name', validator),
                ValueEditor(self, value, 'Value')]

    def _execute(self):
        pass


class ListVariableDialog(_Dialog):

    def _get_editors(self, var):
        name = var.name if var and var.name else '@{}'
        value = var.value if var and var.value else ''
        validator = ListVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, 'Name', validator),
                ListValueEditor(self, value, 'Value',
                                settings=self.plugin.global_settings)]

    def _execute(self):
        pass


class DictionaryVariableDialog(_Dialog):

    def _get_editors(self, var):
        name = var.name if var and var.name else '&{}'
        value = var.value if var and var.value else ''
        validator = DictionaryVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, 'Name', validator),
                ListValueEditor(self, value, 'Value',
                                settings=self.plugin.global_settings)]

    def _execute(self):
        pass


class LibraryDialog(_Dialog):

    _history_suggester = HistorySuggester()

    def _get_editors(self, item):
        name = item and item.name or ''
        args = item and utils.join_value(item.args) or ''
        alias = item.alias if item else ''
        self._suggester = LibrariesSuggester(self._controller, self._history_suggester)
        return [FileNameEditor(self, name, 'Name', self._controller, suggestion_source=self._suggester),
                ValueEditor(self, args, 'Args'),
                ValueEditor(self, alias, 'Alias')]

    def get_value(self):
        values = _Dialog.get_value(self)
        self._history_suggester.store(values[0])
        return values

    def _execute(self):
        pass


class VariablesDialog(LibraryDialog):

    _history_suggester = HistorySuggester()

    def _get_editors(self, item):
        path = item and item.name or ''
        args = item and utils.join_value(item.args) or ''
        return [FileNameEditor(self, path, 'Path', self._controller, suggestion_source=self._history_suggester),
               ValueEditor(self, args, 'Args')]

    def _execute(self):
        pass


class ResourceDialog(_Dialog):

    def _get_editors(self, item):
        name = item and item.name or ''
        return [FileNameEditor(self, name, 'Path', self._controller, suggestion_source=ResourceSuggester(self._controller))]

    def _execute(self):
        pass


class DocumentationDialog(_Dialog):

    def _get_editors(self, doc):
        return [MultiLineEditor(self, doc)]

    def _add_comment_editor(self, item):
        pass

    def get_value(self):
        return _Dialog.get_value(self)

    def get_comment(self):
        return ''

    def _execute(self):
        pass


class _SettingDialog(_Dialog):
    _validator = None

    def _get_editors(self, item):
        editor = ValueEditor(self, item.value)
        if self._validator:
            editor.set_validator(self._validator())
        return [editor]

    def _execute(self):
        pass


class ForceTagsDialog(_SettingDialog):
    def _execute(self):
        pass


class DefaultTagsDialog(_SettingDialog):
    def _execute(self):
        pass


class TagsDialog(_SettingDialog):
    def _execute(self):
        pass


class _FixtureDialog(_SettingDialog):

    def _get_editors(self, item):
        return [ContentAssistEditor(self, item.value)]

    def _execute(self):
        pass


class SuiteSetupDialog(_FixtureDialog):
    tooltip = "Suite Setup is run before any tests"

    def _execute(self):
        pass


class SuiteTeardownDialog(_FixtureDialog):
    def _execute(self):
        pass


class TestSetupDialog(_FixtureDialog):
    def _execute(self):
        pass


class TestTeardownDialog(_FixtureDialog):
    def _execute(self):
        pass


class SetupDialog(_FixtureDialog):
    def _execute(self):
        pass


class TeardownDialog(_FixtureDialog):
    def _execute(self):
        pass


class TemplateDialog(_FixtureDialog):
    def _execute(self):
        pass


class TestTemplateDialog(_FixtureDialog):
    def _execute(self):
        pass


class ArgumentsDialog(_SettingDialog):
    def _get_editors(self, item):
        return [ArgumentEditor(self, item.value, 'Arguments', ArgumentsValidator())]

    def _execute(self):
        pass


class ReturnValueDialog(_SettingDialog):
    def _execute(self):
        pass


class TestTimeoutDialog(_SettingDialog):
    _validator = TimeoutValidator

    def _execute(self):
        pass


class TimeoutDialog(TestTimeoutDialog):
    def _execute(self):
        pass


class MetadataDialog(_Dialog):

    def _get_editors(self, item):
        name, value = item and (item.name, item.value) or ('', '')
        return [ValueEditor(self, name, 'Name'),
                ValueEditor(self, value, 'Value')]

    def _execute(self):
        pass


class TestCaseNameDialog(_Dialog):
    _title = 'New Test Case'

    def _add_comment_editor(self, item):
        pass

    def _get_editors(self, test):
        value = test.name if test else ''
        return [ValueEditor(self, value, 'Name',
                            TestCaseNameValidator(self._controller))]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def _execute(self):
        pass


class CopyUserKeywordDialog(_Dialog):
    _title = 'Copy User Keyword'

    def _add_comment_editor(self, item):
        pass

    def _get_editors(self, uk):
        value = uk.name if uk else ''
        return [ValueEditor(self, value, 'Name',
                            UserKeywordNameValidator(self._controller))]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def _execute(self):
        pass


class UserKeywordNameDialog(_Dialog):
    def _execute(self):
        pass

    _title = 'New User Keyword'

    def _add_comment_editor(self, item):
        pass

    def _get_editors(self, uk):
        value = uk.name if uk else ''
        return [ValueEditor(self, value, 'Name',
                            UserKeywordNameValidator(self._controller)),
                ArgumentEditor(self, '', 'Arguments', ArgumentsValidator())]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def get_args(self):
        return _Dialog.get_value(self)[1]
