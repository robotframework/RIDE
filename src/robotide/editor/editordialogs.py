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
import wx

from wx import Colour
from .. import utils
from ..namespace.suggesters import ResourceSuggester, LibrariesSuggester, HistorySuggester
from ..validators import (ScalarVariableNameValidator, ListVariableNameValidator, TimeoutValidator, ArgumentsValidator,
                          TestCaseNameValidator, UserKeywordNameValidator, DictionaryVariableNameValidator)
from ..widgets import HelpLabel, RIDEDialog, ButtonWithHandler
from .dialoghelps import get_help
from .fieldeditors import (ValueEditor, ListValueEditor, MultiLineEditor, ContentAssistEditor, VariableNameEditor,
                           ArgumentEditor, FileNameEditor)
from .formatters import ListToStringFormatter
from robotide.lib.compat.parsing import language

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

FORCE_TAGS = 'Force Tags'
DEFAULT_TAGS = 'Default Tags'
TEST_TAGS = 'Test Tags'
SUITE_SETUP = 'Suite Setup'
SUITE_TEAR = 'Suite Teardown'
TEST_SETUP = 'Test Setup'
TEST_TEAR = 'Test Teardown'
RET_VAL = 'Return Value'
TEST_TEMPL = 'Test Template'

def editor_dialog(obj, lang='en'):
    set_lang = lang if lang and len(lang) > 0 else 'en'
    english_label = language.get_english_label(set_lang, obj.label).replace('Task', 'Test')
    # print(f"DEBUG: editordialogs.py editor_dialog object name={obj.label} english_label={english_label}"
    #       f"lang={lang} ")
    return globals()[english_label.replace(' ', '') + 'Dialog']


class _Dialog(RIDEDialog):
    _title_nt = ''  # DEBUG: property(lambda self: utils.name_from_class(self, drop='Dialog'))
    _title = ''

    def __init__(self, controller, item=None, plugin=None, title=None):
        # DEBUG: Get rid of item, everything should be in controller
        if not title:
            title = self._title
        RIDEDialog.__init__(self, title)
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
        self.Layout()
        self._editors[0].set_focus()

    def _add_comment_editor(self, item):
        comment = ListToStringFormatter(item.comment).value if item else ''
        self._comment_editor = ValueEditor(self, comment, _('Comment'))
        self._sizer.Add(self._comment_editor)

    def _create_line(self):
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        if wx.VERSION < (4, 1, 0):
            self._sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP, 5)
        else:
            self._sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 5)
        self._sizer.Fit(self)

    def _create_help(self):
        self._sizer.Add(HelpLabel(self, label=get_help(self._title_nt)), flag=wx.ALL, border=2)
        self._sizer.Fit(self)

    def _create_buttons(self, **kwargs):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        for item in self.GetChildren():
            if isinstance(item, (wx.Button, wx.BitmapButton, ButtonWithHandler)):
                item.SetBackgroundColour(Colour(self.color_secondary_background))
                # item.SetOwnBackgroundColour(Colour(self.color_secondary_background))
                item.SetForegroundColour(Colour(self.color_secondary_foreground))
                # item.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        self._sizer.Add(buttons, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self._sizer.Fit(self)

    def get_value(self):
        return [e.get_value() for e in self._editors]

    def get_comment(self):
        return self._comment_editor.get_value()

    def setFocusToOK(self):
        self.FindWindowById(wx.ID_OK).SetFocus()

    def _execute(self):
        """ Just ignore it """
        pass

    def _get_editors(self, item):
        """ Just ignore it """
        pass


class ScalarVariableDialog(_Dialog):
    _title_nt = 'Scalar Variable'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Scalar Variable')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, var):
        name = var.name if var and var.name else '${}'
        value = utils.join_value(var.value) if var else ''
        # print(f"DEBUG: editor.editordialogs.py  ScalarVariableDialog _get_editors value={value}")
        validator = ScalarVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, _('Name'), validator), ValueEditor(self, value, _('Value'), split=True)]

    def _execute(self):
        """ Just ignore it """
        pass


class ListVariableDialog(_Dialog):
    _title_nt = 'List Variable'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('List Variable')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, var):
        name = var.name if var and var.name else '@{}'
        value = var.value if var and var.value else ''
        validator = ListVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, _('Name'), validator),
                ListValueEditor(self, value, _('Value'), settings=self.plugin.global_settings)]

    def _execute(self):
        """ Just ignore it """
        pass


class DictionaryVariableDialog(_Dialog):
    _title_nt = 'Dictionary Variable'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Dictionary Variable')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, var):
        name = var.name if var and var.name else '&{}'
        value = var.value if var and var.value else ''
        validator = DictionaryVariableNameValidator(self._controller, name)
        return [VariableNameEditor(self, name, _('Name'), validator),
                ListValueEditor(self, value, _('Value'), settings=self.plugin.global_settings)]

    def _execute(self):
        """ Just ignore it """
        pass


class LibraryDialog(_Dialog):

    _history_suggester = HistorySuggester()

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Library'):
        __ = title
        if title:
            self._title = title
        else:
            self._title = _('Library')
        self._title_nt = title_nt
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, item):
        name = item and item.name or ''
        args = item and utils.join_value(item.args) or ''
        alias = item.alias if item else ''
        self._suggester = LibrariesSuggester(self._controller, self._history_suggester)
        return [FileNameEditor(self, name, _('Name'), self._controller, suggestion_source=self._suggester),
                ValueEditor(self, args, _('Args')), ValueEditor(self, alias, _('Alias'))]

    def get_value(self):
        values = _Dialog.get_value(self)
        self._history_suggester.store(values[0])
        return values

    def _execute(self):
        """ Just ignore it """
        pass


class VariablesDialog(LibraryDialog):
    _title_nt = 'Variables'

    _history_suggester = HistorySuggester()

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Variables'):
        __ = title
        self._title = _('Variables')
        LibraryDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _get_editors(self, item):
        path = item and item.name or ''
        args = item and utils.join_value(item.args) or ''
        return [FileNameEditor(self, path, _('Path'), self._controller, suggestion_source=self._history_suggester),
                ValueEditor(self, args, _('Args'))]

    def _execute(self):
        """ Just ignore it """
        pass


class ResourceDialog(_Dialog):
    _title_nt = 'Resource'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Resource')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, item):
        name = item and item.name or ''
        return [FileNameEditor(self, name, _('Path'), self._controller,
                               suggestion_source=ResourceSuggester(self._controller))]

    def _execute(self):
        """ Just ignore it """
        pass


class DocumentationDialog(_Dialog):
    _title_nt = 'Documentation'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Documentation')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, doc):
        return [MultiLineEditor(self, doc)]

    def _add_comment_editor(self, item):
        """ Just ignore it """
        pass

    def get_value(self):
        return _Dialog.get_value(self)

    def get_comment(self):
        return ''

    def _execute(self):
        """ Just ignore it """
        pass


class _SettingDialog(_Dialog):
    _validator = None

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=None):
        __ = title
        if title:
            self._title = title
        else:
            self._title = ''
        self._title_nt = title_nt
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, item):
        editor = ValueEditor(self, item.value)
        if self._validator:
            editor.set_validator(self._validator())
        return [editor]

    def _execute(self):
        """ Just ignore it """
        pass


class ForceTagsDialog(_SettingDialog):
    _title_nt = FORCE_TAGS

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=FORCE_TAGS):
        __ = title
        self._title = _(FORCE_TAGS)
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class DefaultTagsDialog(_SettingDialog):
    _title_nt = DEFAULT_TAGS

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=DEFAULT_TAGS):
        __ = title
        self._title = _(DEFAULT_TAGS)
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TestTagsDialog(_SettingDialog):
    _title_nt = TEST_TAGS

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=TEST_TAGS):
        __ = title
        self._title = _(TEST_TAGS)
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TagsDialog(_SettingDialog):
    _title_nt = 'Tags'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Tags'):
        __ = title
        self._title = _('Tags')
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class _FixtureDialog(_SettingDialog):

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=None):
        __ = title
        if title:
            self._title = title
        else:
            self._title = ''
        self._title_nt = title_nt
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _get_editors(self, item):
        return [ContentAssistEditor(self, item.value)]

    def _execute(self):
        """ Just ignore it """
        pass


class SuiteSetupDialog(_FixtureDialog):
    tooltip = _("Suite Setup is run before any tests")
    _title_nt = SUITE_SETUP

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=SUITE_SETUP):
        __ = title
        self._title = _(SUITE_SETUP)
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class SuiteTeardownDialog(_FixtureDialog):
    _title_nt = SUITE_TEAR

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=SUITE_TEAR):
        __ = title
        self._title = _(SUITE_TEAR)
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TestSetupDialog(_FixtureDialog):
    __test__ = False
    _title_nt = TEST_SETUP

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=TEST_SETUP):
        __ = title
        self._title = _(TEST_SETUP)
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TestTeardownDialog(_FixtureDialog):
    __test__ = False
    _title_nt = TEST_TEAR

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=TEST_TEAR):
        __ = title
        self._title = _(TEST_TEAR)
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class SetupDialog(_FixtureDialog):
    _title_nt = 'Setup'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Setup'):
        __ = title
        self._title = _('Setup')
        # print(f"DEBUG: editordialogs.py SetupDialog ENTER item={item}")
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TeardownDialog(_FixtureDialog):
    _title_nt = 'Teardown'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Teardown'):
        __ = title
        self._title = _('Teardown')
        # print(f"DEBUG: editordialogs.py TeardownDialog ENTER item={item}")
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TemplateDialog(_FixtureDialog):
    _title_nt = 'Template'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Template'):
        __ = title
        self._title = _('Template')
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TestTemplateDialog(_FixtureDialog):
    __test__ = False
    _title_nt = TEST_TEMPL

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=TEST_TEMPL):
        __ = title
        self._title = _(TEST_TEMPL)
        _FixtureDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class ArgumentsDialog(_SettingDialog):
    _title_nt = 'Arguments'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Arguments'):
        __ = title
        self._title = _('Arguments')
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _get_editors(self, item):
        return [ArgumentEditor(self, item.value, _('Arguments'), ArgumentsValidator())]

    def _execute(self):
        """ Just ignore it """
        pass


class ReturnValueDialog(_SettingDialog):
    _title_nt = RET_VAL

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt=RET_VAL):
        __ = title
        self._title = _(RET_VAL)
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TestTimeoutDialog(_SettingDialog):
    __test__ = False
    _validator = TimeoutValidator

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Test Timeout'):
        __ = title
        if title:
            self._title = title
        else:
            self._title = _('Test Timeout')
        self._title_nt = title_nt
        _SettingDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class TimeoutDialog(TestTimeoutDialog):
    _title_nt = 'Timeout'

    def __init__(self, controller, item=None, plugin=None, title=None, title_nt='Timeout'):
        __ = title
        self._title = _('Timeout')
        TestTimeoutDialog.__init__(self, controller, item=item, plugin=plugin, title=self._title, title_nt=title_nt)

    def _execute(self):
        """ Just ignore it """
        pass


class MetadataDialog(_Dialog):
    _title_nt = 'Metadata'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Metadata')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _get_editors(self, item):
        name, value = item and (item.name, item.value) or ('', '')
        return [ValueEditor(self, name, _('Name')),
                ValueEditor(self, value, _('Value'))]

    def _execute(self):
        """ Just ignore it """
        pass


class TestCaseNameDialog(_Dialog):
    __test__ = False
    _title_nt = 'New Test Case'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('New Test Case')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _add_comment_editor(self, item):
        """ Just ignore it """
        pass

    def _get_editors(self, test):
        value = test.name if test else ''
        return [ValueEditor(self, value, _('Name'),
                            TestCaseNameValidator(self._controller))]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def _execute(self):
        """ Just ignore it """
        pass


class CopyUserKeywordDialog(_Dialog):
    _title_nt = 'Copy User Keyword'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('Copy User Keyword')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _add_comment_editor(self, item):
        """ Just ignore it """
        pass

    def _get_editors(self, uk):
        value = uk.name if uk else ''
        return [ValueEditor(self, value, _('Name'),
                            UserKeywordNameValidator(self._controller))]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def _execute(self):
        """ Just ignore it """
        pass


class UserKeywordNameDialog(_Dialog):
    def _execute(self):
        """ Just ignore it """
        pass

    _title_nt = 'New User Keyword'

    def __init__(self, controller, item=None, plugin=None, title=None):
        __ = title
        self._title = _('New User Keyword')
        _Dialog.__init__(self, controller, item=item, plugin=plugin, title=self._title)

    def _add_comment_editor(self, item):
        """ Just ignore it """
        pass

    def _get_editors(self, uk):
        value = uk.name if uk else ''
        args_value = ' | '.join(uk.args.value) if uk else ''
        return [ValueEditor(self, value, _('Name'),
                            UserKeywordNameValidator(self._controller)),
                ArgumentEditor(self, args_value, _('Arguments'), ArgumentsValidator())]

    def get_name(self):
        return _Dialog.get_value(self)[0]

    def get_args(self):
        return _Dialog.get_value(self)[1]
