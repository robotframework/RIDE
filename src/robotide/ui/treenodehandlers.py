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

    _label_add_suite = 'New Suite\tCtrl-Shift-F'
    _label_add_directory = 'New Directory'
    _label_new_test_case = 'New Test Case\tCtrl-Shift-T'
    _label_new_user_keyword = 'New User Keyword\tCtrl-Shift-K'
    _label_sort_variables = 'Sort Variables'
    _label_sort_tests = 'Sort Tests'
    _label_sort_keywords = 'Sort Keywords'
    _label_new_scalar = 'New Scalar\tCtrl-Shift-V'
    _label_new_list_variable = 'New List Variable\tCtrl-Shift-L'
    _label_new_dict_variable = 'New Dictionary Variable'
    _label_change_format = 'Change Format'
    _label_copy_macro = 'Copy\tCtrl-Shift-C'
    _label_rename = 'Rename\tF2'
    _label_add_resource = 'Add Resource'
    _label_new_resource = 'New Resource'
    _label_find_usages = 'Find Usages'
    _label_select_all = 'Select All Tests'
    _label_deselect_all = 'Deselect All Tests'
    _label_select_failed_tests = 'Select Only Failed Tests'
    _label_select_passed_tests = 'Select Only Passed Tests'
    _label_delete = 'Delete\tCtrl-Shift-D'
    _label_delete_no_kbsc = 'Delete'
    _label_exclude = 'Exclude'
    _label_include = 'Include'
    _label_expand_all = 'Expand all'
    _label_collapse_all = 'Collapse all'
    _label_remove_readonly = 'Remove Read Only'
    _label_open_folder = 'Open Containing Folder'
    _label_move_up = 'Move Up\tCtrl-Up'
    _label_move_down = 'Move Down\tCtrl-Down'
    _actions = []

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
        self._popup_creator.show(self._tree, PopupMenuItems(self, self._actions), self.controller)

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
        _ = event
        self._tree.SelectAllTests(self._node)

    def on_deselect_all_tests(self, event):
        _ = event
        self._tree.SelectAllTests(self._node, False)

    def on_select_only_failed_tests(self, event):
        _ = event
        self._tree.SelectFailedTests(self._node)

    def on_select_only_passed_tests(self, event):
        _ = event
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
        _ = event
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
        wx.MessageBox(err_msg, 'Validation Error', style=wx.ICON_ERROR)


class DirectoryHandler(_ActionHandler):
    is_draggable = False
    is_test_suite = False
    can_be_rendered = False
    _actions = [_ActionHandler._label_new_resource]

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
        _ = event
        """Sorts the tests inside the treenode"""
        self.controller.execute(SortTests())

    def on_sort_keywords(self, event):
        _ = event
        """Sorts the keywords inside the treenode"""
        self.controller.execute(ctrlcommands.SortKeywords())

    def on_sort_variables(self, event):
        _ = event
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
        _ = event
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
            _ActionHandler._label_add_suite,
            _ActionHandler._label_add_directory,
            _ActionHandler._label_new_resource,
            '---',
            _ActionHandler._label_new_user_keyword,
            _ActionHandler._label_new_scalar,
            _ActionHandler._label_new_list_variable,
            _ActionHandler._label_new_dict_variable,
            '---',
            _ActionHandler._label_change_format
        ]
        if self.controller.parent:
            self._actions.extend([_ActionHandler._label_delete_no_kbsc])

        self._actions.extend([
            '---',
            _ActionHandler._label_select_all,
            _ActionHandler._label_deselect_all,
            _ActionHandler._label_select_failed_tests,
            _ActionHandler._label_select_passed_tests
        ])
        if self.controller.parent:
            self._actions.extend(['---',
                                  _ActionHandler._label_exclude])
        self._actions.extend(['---',
                              _ActionHandler._label_expand_all,
                              _ActionHandler._label_collapse_all])

    def on_expand_all(self, event):
        _ = event
        self._tree.ExpandAllSubNodes(self._node)

    def on_collapse_all(self, event):
        _ = event
        self._tree.CollapseAllSubNodes(self._node)

    def on_new_suite(self, event):
        AddSuiteDialog(self.controller, self._settings).execute()

    def on_new_directory(self, event):
        AddDirectoryDialog(self.controller, self._settings).execute()

    def on_new_resource(self, event):
        NewResourceDialog(self.controller, self._settings).execute()

    def on_delete(self, event):
        FolderDeleteDialog(self.controller).execute()

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox('Directory contains unsaved data!\n'
                          'You must save data before excluding.')


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
    _actions = [_ActionHandler._label_new_user_keyword,
                _ActionHandler._label_new_scalar,
                _ActionHandler._label_new_list_variable,
                _ActionHandler._label_new_dict_variable,
                '---',
                _ActionHandler._label_rename,
                _ActionHandler._label_change_format,
                _ActionHandler._label_sort_keywords,
                _ActionHandler._label_find_usages,
                _ActionHandler._label_delete,
                '---',
                _ActionHandler._label_sort_variables,
                _ActionHandler._label_sort_keywords,
                # DEBUG experiment to allow TestSuites be excluded:
                '---',
                _ActionHandler._label_exclude,
                '---',
                _ActionHandler._label_remove_readonly,
                _ActionHandler._label_open_folder
                ]

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox('File contains unsaved data!\n'
                          'You must save data before excluding.')

    def on_remove_read_only(self, event):
        _ = event

        def return_true():
            return True
        self.controller.is_modifiable = return_true
        self.controller.execute(ctrlcommands.RemoveReadOnly())
        
    def on_open_containing_folder(self, event):
        _ = event
        self.controller.execute(ctrlcommands.OpenContainingFolder())

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
    def accepts_drag(self, dragged):
        _ = dragged
        return True
    _actions = [_ActionHandler._label_new_test_case,
                _ActionHandler._label_new_user_keyword,
                _ActionHandler._label_new_scalar,
                _ActionHandler._label_new_list_variable,
                _ActionHandler._label_new_dict_variable,
                '---',
                _ActionHandler._label_rename,
                _ActionHandler._label_change_format,
                _ActionHandler._label_sort_keywords,
                _ActionHandler._label_delete,
                '---',
                _ActionHandler._label_sort_variables,
                _ActionHandler._label_sort_tests,
                _ActionHandler._label_sort_keywords,
                '---',
                _ActionHandler._label_select_all,
                _ActionHandler._label_deselect_all,
                _ActionHandler._label_select_failed_tests,
                _ActionHandler._label_select_passed_tests,
                # DEBUG experiment to allow TestSuites be excluded:
                '---',
                _ActionHandler._label_exclude,
                '---',
                _ActionHandler._label_remove_readonly,
                _ActionHandler._label_open_folder
                ]

    def on_exclude(self, event):
        try:
            self.controller.execute(ctrlcommands.Exclude())
            # Next is to restart the file monitoring
            RideSettingsChanged(keys=('Excludes', 'excluded'), old=None, new=None).publish()
        except filecontrollers.DirtyRobotDataException:
            wx.MessageBox('File contains unsaved data!\n'
                          'You must save data before excluding.')

    def on_remove_read_only(self, event):
        _ = event

        def return_true():
            return True
        self.controller.is_modifiable = return_true
        self.controller.execute(ctrlcommands.RemoveReadOnly())
        
    def on_open_containing_folder(self, event):
        _ = event
        self.controller.execute(ctrlcommands.OpenContainingFolder())

    def on_new_test_case(self, event):
        dlg = TestCaseNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(ctrlcommands.AddTestCase(dlg.get_name()))
        dlg.Destroy()

    def on_delete(self, event):
        if wx.MessageBox('Delete test case file', caption='Confirm',
                         style=wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.controller.execute(ctrlcommands.DeleteFile())

    def on_safe_delete(self, event):
        return self.on_delete(event)

    def _rename_command(self, label):
        return ctrlcommands.RenameFile(label)

    def _rename_ok_handler(self):
        self._tree.SelectAllTests(self._node, False)


class _TestOrUserKeywordHandler(_CanBeRenamed, _ActionHandler):
    @staticmethod
    def accepts_drag(dragged):
        _ = dragged
        return False
    is_draggable = True
    _actions = [
        _ActionHandler._label_copy_macro,
        _ActionHandler._label_move_up,
        _ActionHandler._label_move_down,
        _ActionHandler._label_rename,
        '---',
        _ActionHandler._label_delete_no_kbsc
    ]

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
        _ = event
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def on_move_down(self, event):
        _ = event
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
    _actions = _TestOrUserKeywordHandler._actions + [
        _ActionHandler._label_find_usages]

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_keyword(parent_node, copied)

    def _create_rename_command(self, new_name):
        return ctrlcommands.RenameKeywordOccurrences(
            self.controller.name, new_name,
            RenameProgressObserver(self._tree.GetParent()),
            self.controller.info)

    def on_find_usages(self, event):
        Usages(self.controller, self._tree.highlight).show()


class VariableHandler(_CanBeRenamed, _ActionHandler):
    @staticmethod
    def accepts_drag(dragged):
        _ = dragged
        return False
    is_draggable = True
    is_variable = True
    _actions = [
        _ActionHandler._label_move_up,
        _ActionHandler._label_move_down,
        _ActionHandler._label_rename,
        '---',
        _ActionHandler._label_delete_no_kbsc
    ]

    def double_clicked(self):
        RideOpenVariableDialog(controller=self.controller).publish()

    def on_delete(self, event):
        self.remove()

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self.controller.execute(ctrlcommands.UpdateVariableName(new_name))

    def on_move_up(self, event):
        _ = event
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def on_move_down(self, event):
        _ = event
        if self.controller.move_down():
            self._tree.move_down(self._node)

    @property
    def index(self):
        return self.controller.index


class ResourceRootHandler(_ActionHandler):
    can_be_rendered = is_draggable = is_user_keyword = is_test_suite = False

    @staticmethod
    def rename(new_name):
        _ = new_name
        return False

    @staticmethod
    def accepts_drag(dragged):
        _ = dragged
        return False

    _actions = [_ActionHandler._label_add_resource]

    @property
    def item(self):
        return None

    def on_add_resource(self, event):
        _ = event
        path = RobotFilePathDialog(
            self._tree.GetParent(), self.controller, self._settings).execute()
        if path:
            self.controller.load_resource(path, LoadProgressObserver(self._tree.GetParent()))


class ExcludedDirectoryHandler(TestDataDirectoryHandler):
    is_draggable = False
    is_test_suite = True

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)
        self._actions = [_ActionHandler._label_include]

    def on_include(self, event):
        self.controller.execute(ctrlcommands.Include())
        # Next is to restart the file monitoring
        RideSettingsChanged(keys=('Excludes', 'included'), old=None, new=None).publish()
