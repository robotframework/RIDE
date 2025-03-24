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

from ..controller import ctrlcommands, filecontrollers, macrocontrollers, settingcontrollers
from ..controller.ctrlcommands import SortTests, SortVariables
from ..editor.editordialogs import (TestCaseNameDialog, UserKeywordNameDialog, ScalarVariableDialog, ListVariableDialog,
                                    CopyUserKeywordDialog, DictionaryVariableDialog)
from ..publish import RideOpenVariableDialog, RideTestSelectedForRunningChanged, RideSettingsChanged, PUBLISHER
from ..ui.progress import LoadProgressObserver
from ..usages.UsageRunner import Usages, ResourceFileUsages
from ..widgets import PopupMenuItems
from .filedialogs import (AddSuiteDialog, AddDirectoryDialog, ChangeFormatDialog, NewResourceDialog,
                          RobotFilePathDialog)
from .progress import RenameProgressObserver
from .resourcedialogs import ResourceRenameDialog, ResourceDeleteDialog
from ..ui.resourcedialogs import FolderDeleteDialog

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

FILE_MANAGER = 'file manager'
LABEL_ADD_SUITE = 'New Suite\tCtrl-Shift-F'
LABEL_ADD_DIRECTORY = 'New Directory'
LABEL_NEW_TEST_CASE = 'New Test Case\tCtrl-Shift-T'
LABEL_NEW_USER_KEYWORD = 'New User Keyword\tCtrl-Shift-K'
LABEL_SORT_VARIABLES = 'Sort Variables'
LABEL_SORT_TESTS = 'Sort Tests'
LABEL_SORT_KEYWORDS = 'Sort Keywords'
LABEL_NEW_SCALAR = 'New Scalar\tCtrl-Shift-V'
LABEL_NEW_LIST_VARIABLE = 'New List Variable\tCtrl-Shift-L'
LABEL_NEW_DICT_VARIABLE = 'New Dictionary Variable'
LABEL_CHANGE_FORMAT = 'Change Format'
LABEL_COPY_MACRO = 'Copy\tCtrl-Shift-C'
LABEL_RENAME = 'Rename\tF2'
LABEL_ADD_RESOURCE = 'Add Resource'
LABEL_NEW_RESOURCE = 'New Resource'
LABEL_FIND_USAGES = 'Find Usages'
LABEL_SELECT_ALL = 'Select All Tests'
LABEL_DESELECT_ALL = 'Deselect All Tests'
LABEL_SELECT_FAILED_TESTS = 'Select Only Failed Tests'
LABEL_SELECT_PASSED_TESTS = 'Select Only Passed Tests'
LABEL_DELETE = 'Delete\tCtrl-Shift-D'
LABEL_DELETE_NO_KBSC = 'Delete'
LABEL_EXCLUDE = 'Exclude'
LABEL_INCLUDE = 'Include'
LABEL_EXPAND_ALL = 'Expand all'
LABEL_COLLAPSE_ALL = 'Collapse all'
LABEL_REMOVE_READONLY = 'Remove Read Only'
LABEL_OPEN_FOLDER = 'Open Containing Folder'
LABEL_MOVE_UP = 'Move Up\tCtrl-Up'
LABEL_MOVE_DOWN = 'Move Down\tCtrl-Down'


def action_handler_class(controller):
    return {
        filecontrollers.TestDataDirectoryController: TestDataDirectoryHandler,
        filecontrollers.ResourceFileController: ResourceFileHandler,
        filecontrollers.TestCaseFileController: TestCaseFileHandler,
        macrocontrollers.TestCaseController: TestCaseHandler,
        macrocontrollers.UserKeywordController: UserKeywordHandler,
        settingcontrollers.VariableController: VariableHandler,
        filecontrollers.ExcludedDirectoryController: ExcludedDirectoryHandler,
        filecontrollers.ExcludedFileController: ExcludedDirectoryHandler  # Reuse the same class
    }[controller.__class__]


class _ActionHandler:
    is_user_keyword = False
    is_test_suite = False
    is_variable = False

    _actions = []
    _actions_nt = []

    def __init__(self, controller, tree, node, settings):
        self.controller = controller
        self._tree = tree
        self._node = node
        self._settings = settings
        self._rendered = False
        self._popup_creator = tree._popup_creator

    @property
    def item(self):
        return self.controller.data

    @property
    def node(self):
        return self._node

    def show_popup(self):
        """ DEBUG Next code selects item when right click, which is annoying when we want to expand or select tests
                  but want to keep the Editor in the same file or position
        node = self._tree.controller.find_node_by_controller(self.controller)
        if node:
            wx.CallLater(500, self._tree.SelectItem, node)
        """
        self._popup_creator.show(self._tree, PopupMenuItems(self, self._actions, self._actions_nt), self.controller)

    @staticmethod
    def begin_label_edit():
        return False

    def double_clicked(self):
        """ Just ignore it """
        pass

    def end_label_edit(self, event):
        """ Just ignore it """
        pass

    def on_delete(self, event):
        """ Just ignore it """
        pass

    def on_new_suite(self, event):
        """ Just ignore it """
        pass

    def on_new_directory(self, event):
        """ Just ignore it """
        pass

    def on_new_resource(self, event):
        """ Just ignore it """
        pass

    def on_new_user_keyword(self, event):
        """ Just ignore it """
        pass

    def on_new_test_case(self, event):
        """ Just ignore it """
        pass

    def on_new_scalar(self, event):
        """ Just ignore it """
        pass

    def on_new_list_variable(self, event):
        """ Just ignore it """
        pass

    def on_new_dictionary_variable(self, event):
        """ Just ignore it """
        pass

    def on_copy(self, event):
        """ Just ignore it """
        pass

    def on_find_usages(self, event):
        """ Just ignore it """
        pass

    def on_select_all_tests(self, event):
        __ = event
        self._tree.SelectAllTests(self._node)

    def on_deselect_all_tests(self, event):
        __ = event
        self._tree.SelectAllTests(self._node, False)

    def on_select_only_failed_tests(self, event):
        __ = event
        self._tree.SelectFailedTests(self._node)

    def on_select_only_passed_tests(self, event):
        __ = event
        self._tree.SelectPassedTests(self._node)

    def on_safe_delete(self, event):
        """ Just ignore it """
        pass

    def on_exclude(self, event):
        """ Just ignore it """
        pass

    def on_include(self, event):
        """ Just ignore it """
        pass


class _CanBeRenamed(object):

    def on_rename(self, event):
        __ = event
        self._tree.label_editor.on_label_edit()

    def begin_label_edit(self):
        def label_edit():
            # DEBUG: fixme yep.yep.yep.yep.yep
            node = self._tree.controller.find_node_by_controller(self.controller)
            if node:
                self._tree.EditLabel(node)
        # Must handle pending events before label edit
        # This is a fix for situations where there is a pending action
        # that will change this label (Text Editor all changing actions)
        wx.CallAfter(label_edit)
        return True

    def end_label_edit(self, event):
        if not event.IsEditCancelled():
            if self._is_valid_rename(event.GetLabel()):
                self.rename(event.GetLabel())
            else:
                event.Veto()

    def _is_valid_rename(self, label):
        validation = self.controller.validate_name(label)
        if validation.error_message:
            self._show_validation_error(validation.error_message)
            return False
        return True

    @staticmethod
    def _show_validation_error(err_msg):
        wx.MessageBox(err_msg, _('Validation Error'), style=wx.ICON_ERROR)


class DirectoryHandler(_ActionHandler):
    is_draggable = False
    is_test_suite = False
    can_be_rendered = False

    def __init__(self, *args):
        _ActionHandler.__init__(self, *args)
        self._actions = [_('New Resource')]
        self._actions_nt = [LABEL_NEW_RESOURCE]

    def on_new_resource(self, event):
        NewResourceDialog(self.controller, self._settings).execute()


class TestDataHandler(_ActionHandler):
    def accepts_drag(self, dragged):
        return isinstance(dragged, UserKeywordHandler) or isinstance(dragged, VariableHandler)
    is_draggable = False
    is_test_suite = True

    @property
    def tests(self):
        return self.controller.tests

    @property
    def keywords(self):
        return self.controller.keywords

    @property
    def variables(self):
        return self.controller.variables

    def has_been_modified_on_disk(self):
        return self.item.has_been_modified_on_disk()

    def do_drop(self, item):
        self.controller.add_test_or_keyword(item)

    @staticmethod
    def rename(new_name):
        _ = new_name
        return False

    def on_sort_tests(self, event):
        __ = event
        """Sorts the tests inside the treenode"""
        self.controller.execute(SortTests())

    def on_sort_keywords(self, event):
        __ = event
        """Sorts the keywords inside the treenode"""
        self.controller.execute(ctrlcommands.SortKeywords())

    def on_sort_variables(self, event):
        __ = event
        """Sorts the variables inside the treenode"""
        self.controller.execute(SortVariables())

    @property
    def can_be_rendered(self):
        if not self._has_children():
            return False
        return not self._rendered

    def _has_children(self):
        return (self.item.keyword_table or self.item.testcase_table or
                self.item.variable_table)

    def set_rendered(self):
        self._rendered = True

    def on_change_format(self, event):
        __ = event
        ChangeFormatDialog(self.controller).execute()

    def on_new_user_keyword(self, event):
        dlg = UserKeywordNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(ctrlcommands.AddKeyword(dlg.get_name(), dlg.get_args()))
        dlg.Destroy()

    def on_new_scalar(self, event):
        self._new_var(ScalarVariableDialog)

    def on_new_list_variable(self, event):
        class FakePlugin(object):
            global_settings = self._settings
        self._new_var(ListVariableDialog, plugin=FakePlugin())

    def on_new_dictionary_variable(self, event):
        class FakePlugin(object):
            global_settings = self._settings
        self._new_var(DictionaryVariableDialog, plugin=FakePlugin())

    def _new_var(self, dialog_class, plugin=None):
        dlg = dialog_class(self._var_controller, plugin=plugin)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self.controller.execute(ctrlcommands.AddVariable(name, value, comment))

    @property
    def _var_controller(self):
        return self.controller.datafile_controller.variables


class TestDataDirectoryHandler(TestDataHandler):

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)
        self._actions = [
                        _('New Suite\tCtrl-Shift-F'),
                        _('New Directory'),
                        _('New Resource'),
                        '---',
                        _('New User Keyword\tCtrl-Shift-K'),
                        _('New Scalar\tCtrl-Shift-V'),
                        _('New List Variable\tCtrl-Shift-L'),
                        _('New Dictionary Variable'),
                        '---',
                        _('Change Format'),
                        _('Open Containing Folder')
                        ]
        self._actions_nt = [
                            LABEL_ADD_SUITE,
                            LABEL_ADD_DIRECTORY,
                            LABEL_NEW_RESOURCE,
                            '---',
                            LABEL_NEW_USER_KEYWORD,
                            LABEL_NEW_SCALAR,
                            LABEL_NEW_LIST_VARIABLE,
                            LABEL_NEW_DICT_VARIABLE,
                            '---',
                            LABEL_CHANGE_FORMAT,
                            LABEL_OPEN_FOLDER
                           ]
        if self.controller.parent:
            self._actions.extend([_('Delete')])
            self._actions_nt.extend([LABEL_DELETE_NO_KBSC])

        self._actions.extend([
                              '---',
                              _('Select All Tests'),
                              _('Deselect All Tests'),
                              _('Select Only Failed Tests'),
                              _('Select Only Passed Tests')
                              ])
        self._actions_nt.extend([
                                 '---',
                                 LABEL_SELECT_ALL,
                                 LABEL_DESELECT_ALL,
                                 LABEL_SELECT_FAILED_TESTS,
                                 LABEL_SELECT_PASSED_TESTS
                                ])
        if self.controller.parent:
            self._actions.extend(['---', _('Exclude')])
            self._actions_nt.extend(['---', LABEL_EXCLUDE])
        self._actions.extend(['---', _('Expand all'), _('Collapse all')])
        self._actions_nt.extend(['---', LABEL_EXPAND_ALL, LABEL_COLLAPSE_ALL])

    def on_expand_all(self, event):
        __ = event
        self._tree.ExpandAllSubNodes(self._node)

    def on_collapse_all(self, event):
        __ = event
        self._tree.CollapseAllSubNodes(self._node)

    def on_new_suite(self, event):
        AddSuiteDialog(self.controller, self._settings).execute()

    def on_new_directory(self, event):
        AddDirectoryDialog(self.controller, self._settings).execute()

    def on_new_resource(self, event):
        NewResourceDialog(self.controller, self._settings).execute()

    def on_delete(self, event):
        FolderDeleteDialog(self.controller).execute()

    def on_open_containing_folder(self, event):
        __ = event
        try:
            file_manager = self._settings['General'][FILE_MANAGER]
        except KeyError:
            file_manager = None
        directory = self.controller.source
        # print(f"DEBUG: treenodecontrollers.py TestDataDirectoryHandler on_open_containing_folder"
        #       f" directory={directory}")
        self.controller.execute(ctrlcommands.OpenContainingFolder(tool=file_manager, path=directory))

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox(_('Directory contains unsaved data!\n'
                          'You must save data before excluding.'))


class _FileHandlerThanCanBeRenamed(_CanBeRenamed):

    def begin_label_edit(self):
        self._old_label = self._node.GetText()
        self._set_node_label(self.controller.basename)
        return _CanBeRenamed.begin_label_edit(self)

    def end_label_edit(self, event):
        if not event.IsEditCancelled():
            result = self.controller.execute(
                self._rename_command(event.GetLabel()))
            if result:
                self._rename_ok_handler()
                self._old_label = self.controller.basename
            else:
                event.Veto()
        else:
            self._set_node_label(self._old_label)

    def _rename_ok_handler(self):
        """ Just ignore it """
        pass

    def _rename_command(self, label):
        raise NotImplementedError(self.__class__)

    def _set_node_label(self, label):
        self._tree.SetItemText(self._node, label)


class ResourceFileHandler(_FileHandlerThanCanBeRenamed, TestDataHandler):
    is_test_suite = False

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)
        self._actions = [
                         _('New User Keyword\tCtrl-Shift-K'),
                         _('New Scalar\tCtrl-Shift-V'),
                         _('New List Variable\tCtrl-Shift-L'),
                         _('New Dictionary Variable'),
                         '---',
                         _('Rename\tF2'),
                         _('Change Format'),
                         _('Sort Keywords'),
                         _('Find Usages'),
                         _('Delete\tCtrl-Shift-D'),
                         '---',
                         _('Sort Variables'),
                         _('Sort Keywords'),
                         '---',
                         _('Exclude'),
                         '---',
                         _('Remove Read Only'),
                         _('Open Containing Folder')
                        ]
        self._actions_nt = [
                            LABEL_NEW_USER_KEYWORD,
                            LABEL_NEW_SCALAR,
                            LABEL_NEW_LIST_VARIABLE,
                            LABEL_NEW_DICT_VARIABLE,
                            '---',
                            LABEL_RENAME,
                            LABEL_CHANGE_FORMAT,
                            LABEL_SORT_KEYWORDS,
                            LABEL_FIND_USAGES,
                            LABEL_DELETE,
                            '---',
                            LABEL_SORT_VARIABLES,
                            LABEL_SORT_KEYWORDS,
                            '---',
                            LABEL_EXCLUDE,
                            '---',
                            LABEL_REMOVE_READONLY,
                            LABEL_OPEN_FOLDER
                           ]

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox(_('File contains unsaved data!\n'
                          'You must save data before excluding.'))

    def on_remove_read_only(self, event):
        __ = event

        def return_true():
            return True
        self.controller.is_modifiable = return_true
        self.controller.execute(ctrlcommands.RemoveReadOnly())

    def on_open_containing_folder(self, event):
        __ = event
        try:
            file_manager = self._settings['General'][FILE_MANAGER]
        except KeyError:
            file_manager = None
        self.controller.execute(ctrlcommands.OpenContainingFolder(file_manager))

    def on_find_usages(self, event):
        ResourceFileUsages(self.controller, self._tree.highlight).show()

    def on_delete(self, event):
        ResourceDeleteDialog(self.controller).execute()

    def on_safe_delete(self, event):
        return self.on_delete(event)

    def _rename_command(self, label):
        return ctrlcommands.RenameResourceFile(
            label, self._check_should_rename_static_imports)

    def _check_should_rename_static_imports(self):
        return ResourceRenameDialog(self.controller).execute()


class TestCaseFileHandler(_FileHandlerThanCanBeRenamed, TestDataHandler):

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)
        self._actions = [_('New Test Case\tCtrl-Shift-T'),
                         _('New User Keyword\tCtrl-Shift-K'),
                         _('New Scalar\tCtrl-Shift-V'),
                         _('New List Variable\tCtrl-Shift-L'),
                         _('New Dictionary Variable'),
                         '---',
                         _('Rename\tF2'),
                         _('Change Format'),
                         _('Sort Keywords'),
                         _('Delete\tCtrl-Shift-D'),
                         '---',
                         _('Sort Variables'),
                         _('Sort Tests'),
                         _('Sort Keywords'),
                         '---',
                         _('Select All Tests'),
                         _('Deselect All Tests'),
                         _('Select Only Failed Tests'),
                         _('Select Only Passed Tests'),
                         '---',
                         _('Exclude'),
                         '---',
                         _('Remove Read Only'),
                         _('Open Containing Folder')
                         ]
        self._actions_nt = [
                            LABEL_NEW_TEST_CASE,
                            LABEL_NEW_USER_KEYWORD,
                            LABEL_NEW_SCALAR,
                            LABEL_NEW_LIST_VARIABLE,
                            LABEL_NEW_DICT_VARIABLE,
                            '---',
                            LABEL_RENAME,
                            LABEL_CHANGE_FORMAT,
                            LABEL_SORT_KEYWORDS,
                            LABEL_DELETE,
                            '---',
                            LABEL_SORT_VARIABLES,
                            LABEL_SORT_TESTS,
                            LABEL_SORT_KEYWORDS,
                            '---',
                            LABEL_SELECT_ALL,
                            LABEL_DESELECT_ALL,
                            LABEL_SELECT_FAILED_TESTS,
                            LABEL_SELECT_PASSED_TESTS,
                            '---',
                            LABEL_EXCLUDE,
                            '---',
                            LABEL_REMOVE_READONLY,
                            LABEL_OPEN_FOLDER
                           ]

    def accepts_drag(self, dragged):
        _ = dragged
        return True

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox(_('File contains unsaved data!\n'
                          'You must save data before excluding.'))

    def on_remove_read_only(self, event):
        __ = event

        def return_true():
            return True
        self.controller.is_modifiable = return_true
        self.controller.execute(ctrlcommands.RemoveReadOnly())
        
    def on_open_containing_folder(self, event):
        __ = event
        try:
            file_manager = self._settings['General'][FILE_MANAGER]
        except KeyError:
            file_manager = None
        self.controller.execute(ctrlcommands.OpenContainingFolder(file_manager))

    def on_new_test_case(self, event):
        dlg = TestCaseNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(ctrlcommands.AddTestCase(dlg.get_name()))
        dlg.Destroy()

    def on_delete(self, event):
        if wx.MessageBox(_('Delete test case file'), caption=_('Confirm'),
                         style=wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.controller.execute(ctrlcommands.DeleteFile())

    def on_safe_delete(self, event):
        return self.on_delete(event)

    def _rename_command(self, label):
        return ctrlcommands.RenameFile(label)

    def _rename_ok_handler(self):
        self._tree.SelectAllTests(self._node, False)


class _TestOrUserKeywordHandler(_CanBeRenamed, _ActionHandler):
    is_draggable = True

    def __init__(self, *args):
        _ActionHandler.__init__(self, *args)
        self._actions = [
                        _('Copy\tCtrl-Shift-C'),
                        _('Move Up\tCtrl-Up'),
                        _('Move Down\tCtrl-Down'),
                        _('Rename\tF2'),
                        '---',
                        _('Delete')
                        ]
        self._actions_nt = [
                            LABEL_COPY_MACRO,
                            LABEL_MOVE_UP,
                            LABEL_MOVE_DOWN,
                            LABEL_RENAME,
                            '---',
                            LABEL_DELETE_NO_KBSC
                            ]


    @staticmethod
    def accepts_drag(dragged):
        __ = dragged
        return False

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self.controller.execute(self._create_rename_command(new_name))

    def on_copy(self, event):
        dlg = self._copy_name_dialog_class(self.controller, self.item)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(ctrlcommands.CopyMacroAs(dlg.get_name()))
        dlg.Destroy()

    def on_move_up(self, event):
        __ = event
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def on_move_down(self, event):
        __ = event
        if self.controller.move_down():
            self._tree.move_down(self._node)

    def on_delete(self, event):
        self.controller.execute(ctrlcommands.RemoveMacro(self.controller))


class TestCaseHandler(_TestOrUserKeywordHandler):
    def __init__(self, controller, tree, node, settings):
        _TestOrUserKeywordHandler.__init__(self, controller, tree, node, settings)
        PUBLISHER.subscribe(self.test_selection_changed, RideTestSelectedForRunningChanged)

    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = TestCaseNameDialog

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_test(parent_node, copied)

    @staticmethod
    def _create_rename_command(new_name):
        return ctrlcommands.RenameTest(new_name)

    def test_selection_changed(self, message):
        if self.controller in message.tests:
            if not self.node.GetValue():
                self._tree.CheckItem(self.node, checked=True)
        else:
            if self.node.GetValue():
                self._tree.CheckItem(self.node, checked=False)


class UserKeywordHandler(_TestOrUserKeywordHandler):
    is_user_keyword = True
    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = CopyUserKeywordDialog

    def __init__(self, *args):
        _TestOrUserKeywordHandler.__init__(self, *args)
        self._actions = self._actions + [_('Find Usages')]
        self._actions_nt = self._actions_nt + [LABEL_FIND_USAGES]

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_keyword(parent_node, copied)

    def _create_rename_command(self, new_name):
        # print(f"DEBUG: treenodehandlers.py UserKeywodHandler _create_rename_command controller.name={self.controller.name}"
        #       f", new_name={new_name} info={self.controller.info}")
        return ctrlcommands.RenameKeywordOccurrences(self.controller.name, new_name,
                                                     RenameProgressObserver(self._tree.GetParent()),
                                                     self.controller.info, language=self.controller.language)

    def on_find_usages(self, event):
        Usages(self.controller, self._tree.highlight).show()


class VariableHandler(_CanBeRenamed, _ActionHandler):
    is_draggable = True
    is_variable = True

    def __init__(self, *args):
        _ActionHandler.__init__(self, *args)
        self._actions = [
            _('Move Up\tCtrl-Up'),
            _('Move Down\tCtrl-Down'),
            _('Rename\tF2'),
            '---',
            _('Delete')
            ]
        self._actions_nt = [
            LABEL_MOVE_UP,
            LABEL_MOVE_DOWN,
            LABEL_RENAME,
            '---',
            LABEL_DELETE_NO_KBSC
            ]

    @staticmethod
    def accepts_drag(dragged):
        __ = dragged
        return False

    def double_clicked(self):
        RideOpenVariableDialog(controller=self.controller).publish()

    def on_delete(self, event):
        self.remove()

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self.controller.execute(ctrlcommands.UpdateVariableName(new_name))

    def on_move_up(self, event):
        __ = event
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def on_move_down(self, event):
        __ = event
        if self.controller.move_down():
            self._tree.move_down(self._node)

    @property
    def index(self):
        return self.controller.index


class ResourceRootHandler(_ActionHandler):
    can_be_rendered = is_draggable = is_user_keyword = is_test_suite = False

    def __init__(self, *args):
        _ActionHandler.__init__(self, *args)
        self._actions = [_('Add Resource')]
        self._actions_nt = [LABEL_ADD_RESOURCE]

    @staticmethod
    def rename(new_name):
        _ = new_name
        return False

    @staticmethod
    def accepts_drag(dragged):
        __ = dragged
        return False

    @property
    def item(self):
        return None

    def on_add_resource(self, event):
        __ = event
        path = RobotFilePathDialog(
            self._tree.GetParent(), self.controller, self._settings).execute()
        if path:
            self.controller.load_resource(path, LoadProgressObserver(self._tree.GetParent()))


class ExcludedDirectoryHandler(TestDataDirectoryHandler):
    is_draggable = False
    is_test_suite = True

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)
        self._actions = [_('Include')]
        self._actions_nt = [LABEL_INCLUDE]

    def on_include(self, event):
        self.controller.execute(ctrlcommands.Include())
        # Next is to restart the file monitoring
        RideSettingsChanged(keys=('Excludes', 'included'), old=None, new=None).publish()
