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

from robotide.controller.commands import (RenameKeywordOccurrences, RemoveMacro,
    AddKeyword, AddTestCase, RenameTest, CopyMacroAs, AddVariable,
    UpdateVariableName, RenameFile, RenameResourceFile, DeleteFile, SortKeywords, DeleteFolder)
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.macrocontrollers import (TestCaseController,
                                                  UserKeywordController)
from robotide.controller.filecontrollers import (TestDataDirectoryController,
    ResourceFileController, TestCaseFileController, DirectoryController)
from robotide.editor.editordialogs import (TestCaseNameDialog,
    UserKeywordNameDialog, ScalarVariableDialog, ListVariableDialog,
    CopyUserKeywordDialog)
from robotide.ui.progress import LoadProgressObserver
from robotide.usages.UsageRunner import Usages, ResourceFileUsages
from .filedialogs import (AddSuiteDialog, ChangeFormatDialog, NewResourceDialog, AddResourceDialog)
from robotide.widgets import PopupMenuItems
from .progress import RenameProgressObserver
from .resourcedialogs import ResourceRenameDialog, ResourceDeleteDialog

def action_handler_class(controller):
    return {TestDataDirectoryController:TestDataDirectoryHandler,
         ResourceFileController:ResourceFileHandler,
         TestCaseFileController:TestCaseFileHandler,
         TestCaseController:TestCaseHandler,
         UserKeywordController:UserKeywordHandler,
         VariableController:VariableHandler,
         DirectoryController: DirectoryHandler
     }[controller.__class__]

class _ActionHandler(wx.Window):
    is_user_keyword = False
    is_test_suite = False
    is_variable = False

    _label_add_suite = 'New Suite\tCtrl-Shift-F'
    _label_new_test_case = 'New Test Case\tCtrl-Shift-T'
    _label_new_user_keyword = 'New User Keyword\tCtrl-Shift-K'
    _label_sort_keywords = 'Sort Keywords'
    _label_new_scalar = 'New Scalar\tCtrl-Shift-V'
    _label_new_list_variable = 'New List Variable\tCtrl-Shift-L'
    _label_change_format = 'Change Format'
    _label_copy_macro = 'Copy\tCtrl-Shift-C'
    _label_rename = 'Rename\tF2'
    _label_add_resource = 'Add Resource'
    _label_new_resource = 'New Resource'
    _label_find_usages = 'Find Usages'
    _label_select_all = 'Select All Tests'
    _label_deselect_all = 'Deselect All Tests'
    _label_select_failed_tests = 'Select Only Failed Tests'
    _label_delete = 'Delete\tCtrl-Shift-D'
    _label_delete_no_kbsc = 'Delete'

    def __init__(self, controller, tree, node, settings):
        wx.Window.__init__(self, tree)
        self.controller = controller
        self._tree = tree
        self._node = node
        self._settings = settings
        self._rendered = False
        self.Show(False)
        self._popup_creator = tree._popup_creator

    @property
    def item(self):
        return self.controller.data

    @property
    def node(self):
        return self._node

    def show_popup(self):
        self._popup_creator.show(self, PopupMenuItems(self, self._actions),
                                 self.controller)
    def begin_label_edit(self):
        return False

    def end_label_edit(self, event):
        pass

    def OnDelete(self, event):
        pass

    def OnNewSuite(self, event):
        pass

    def OnNewResource(self, event):
        pass

    def OnNewUserKeyword(self, event):
        pass

    def OnNewTestCase(self, event):
        pass

    def OnNewScalar(self, event):
        pass

    def OnNewListVariable(self, event):
        pass

    def OnCopy(self, event):
        pass

    def OnFindUsages(self, event):
        pass

    def OnSelectAllTests(self, event):
        self._tree.SelectAllTests(self._node)

    def OnDeselectAllTests(self, event):
        self._tree.DeselectAllTests(self._node)

    def OnSelectOnlyFailedTests(self, event):
        self._tree.SelectFailedTests(self._node)

    def OnSafeDelete(self, event):
        pass


class _CanBeRenamed(object):

    def OnRename(self, event):
        self._tree.label_editor.OnLabelEdit()

    def begin_label_edit(self):
        def label_edit():
            #FIXME: yep.yep.yep.yep.yep
            node = self._tree._controller.find_node_by_controller(self.controller)
            if node:
                self._tree.EditLabel(node)
        # Must handle pending events before label edit
        # This is a fix for situations where there is a pending action
        # that will change this label (Text Editor all changing actions)
        wx.CallAfter(label_edit)
        return True

    def end_label_edit(self, event):
        if not event.IsEditCancelled() and \
                self._is_valid_rename(event.GetLabel()):
            self.rename(event.GetLabel())

    def _is_valid_rename(self, label):
        validation = self.controller.validate_name(label)
        if validation.error_message:
            self._show_validation_error(validation.error_message)
            return False
        return True

    def _show_validation_error(self, err_msg):
        wx.MessageBox(err_msg, 'Validation Error', style=wx.ICON_ERROR)


class DirectoryHandler(_ActionHandler):
    is_draggable = False
    is_test_suite = False
    can_be_rendered = False
    _actions = [_ActionHandler._label_new_resource]

    def OnNewResource(self, event):
        NewResourceDialog(self.controller).execute()


class TestDataHandler(_ActionHandler):
    accepts_drag = lambda self, dragged: (isinstance(dragged, UserKeywordHandler) or
                                          isinstance(dragged, VariableHandler))

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

    def rename(self, new_name):
        return False

    def OnSortKeywords(self, event):
        """Sorts the keywords inside the treenode"""
        self.controller.execute(SortKeywords())

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

    def OnChangeFormat(self, event):
        ChangeFormatDialog(self.controller).execute()

    def OnNewUserKeyword(self, event):
        dlg = UserKeywordNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(AddKeyword(dlg.get_name(), dlg.get_args()))
        dlg.Destroy()

    def OnNewScalar(self, event):
        self._new_var(ScalarVariableDialog)

    def OnNewListVariable(self, event):
        class FakePlugin(object):
            global_settings = self._settings
        self._new_var(ListVariableDialog, plugin=FakePlugin())

    def _new_var(self, dialog_class, plugin=None):
        dlg = dialog_class(self._var_controller, plugin=plugin)
        if dlg.ShowModal() == wx.ID_OK:
            name, value = dlg.get_value()
            comment = dlg.get_comment()
            self.controller.execute(AddVariable(name, value, comment))

    @property
    def _var_controller(self):
        return self.controller.datafile_controller.variables


class TestDataDirectoryHandler(TestDataHandler):

    def __init__(self, *args):
        TestDataHandler.__init__(self, *args)

        self._actions = [_ActionHandler._label_add_suite,
                _ActionHandler._label_new_resource,
                '---',
                _ActionHandler._label_new_user_keyword,
                _ActionHandler._label_new_scalar,
                _ActionHandler._label_new_list_variable,
                '---',
                _ActionHandler._label_change_format] + \
                        ([_ActionHandler._label_delete_no_kbsc] if self.controller.parent else []) + \
                ['---',
                _ActionHandler._label_select_all,
                _ActionHandler._label_deselect_all,
                _ActionHandler._label_select_failed_tests]

    def OnNewSuite(self, event):
        AddSuiteDialog(self.controller, self._settings).execute()

    def OnNewResource(self, event):
        NewResourceDialog(self.controller).execute()

    def OnDelete(self, event):
        if wx.MessageBox('Are you sure you want to delete this folder and all of its '
                         'contents.', caption='Confirm',
            style=wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.controller.execute(DeleteFolder())


class ResourceFileHandler(_CanBeRenamed, TestDataHandler):
    is_test_suite = False
    _actions = [_ActionHandler._label_new_user_keyword,
                _ActionHandler._label_new_scalar,
                _ActionHandler._label_new_list_variable, '---',
                _ActionHandler._label_rename,
                _ActionHandler._label_change_format,
                _ActionHandler._label_sort_keywords,
                _ActionHandler._label_find_usages,
                _ActionHandler._label_delete]

    def OnFindUsages(self, event):
        ResourceFileUsages(self.controller, self._tree.highlight).show()

    def OnDelete(self, event):
        ResourceDeleteDialog(self.controller).execute()

    def OnSafeDelete(self, event):
        return self.OnDelete(event)

    def begin_label_edit(self):
        self._old_label = self._node.GetText()
        self._set_node_label(self.controller.basename)
        return _CanBeRenamed.begin_label_edit(self)

    def end_label_edit(self, event):
        if not event.IsEditCancelled():
            self.controller.execute(RenameResourceFile(event.GetLabel(), self._check_should_rename_static_imports))
        else:
            self._set_node_label(self._old_label)

    def _check_should_rename_static_imports(self):
        return ResourceRenameDialog(self.controller).execute()

    def _set_node_label(self, label):
        self._tree.SetItemText(self._node, label)


class TestCaseFileHandler(_CanBeRenamed, TestDataHandler):
    accepts_drag = lambda *args: True
    _actions = [_ActionHandler._label_new_test_case,
                _ActionHandler._label_new_user_keyword,
                _ActionHandler._label_new_scalar,
                _ActionHandler._label_new_list_variable, '---',
                _ActionHandler._label_rename,
                _ActionHandler._label_change_format,
                _ActionHandler._label_sort_keywords,
                _ActionHandler._label_delete,
                '---',
                _ActionHandler._label_select_all,
                _ActionHandler._label_deselect_all,
                _ActionHandler._label_select_failed_tests]

    def OnNewTestCase(self, event):
        dlg = TestCaseNameDialog(self.controller)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(AddTestCase(dlg.get_name()))
        dlg.Destroy()

    def OnDelete(self, event):
        if wx.MessageBox('Delete test case file', caption='Confirm',
                         style=wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            self.controller.execute(DeleteFile())

    def OnSafeDelete(self, event):
        return self.OnDelete(event)

    def begin_label_edit(self):
        self._old_label = self._node.GetText()
        self._set_node_label(self.controller.basename)
        return _CanBeRenamed.begin_label_edit(self)

    def end_label_edit(self, event):
        if not event.IsEditCancelled():
            self.controller.execute(RenameFile(event.GetLabel()))
        else:
            self._set_node_label(self._old_label)

    def _set_node_label(self, label):
        self._tree.SetItemText(self._node, label)


class _TestOrUserKeywordHandler(_CanBeRenamed, _ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    _actions = [_ActionHandler._label_copy_macro, 'Move Up\tCtrl-Up', 'Move Down\tCtrl-Down',
                _ActionHandler._label_rename, '---', 'Delete']

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self.controller.execute(self._create_rename_command(new_name))

    def OnCopy(self, event):
        dlg = self._copy_name_dialog_class(self.controller, self.item)
        if dlg.ShowModal() == wx.ID_OK:
            self.controller.execute(CopyMacroAs(dlg.get_name()))
        dlg.Destroy()

    def OnMoveUp(self, event):
        if self.controller.move_up():
            self._tree.move_up(self._node)

    def OnMoveDown(self, event):
        if self.controller.move_down():
            self._tree.move_down(self._node)

    def OnDelete(self, event):
        self.controller.execute(RemoveMacro(self.controller))


class TestCaseHandler(_TestOrUserKeywordHandler):
    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = TestCaseNameDialog

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_test(parent_node, copied)

    def _create_rename_command(self, new_name):
        return RenameTest(new_name)


class UserKeywordHandler(_TestOrUserKeywordHandler):
    is_user_keyword = True
    _datalist = property(lambda self: self.item.datalist)
    _copy_name_dialog_class = CopyUserKeywordDialog
    _actions = _TestOrUserKeywordHandler._actions + [_ActionHandler._label_find_usages]

    def _add_copy_to_tree(self, parent_node, copied):
        self._tree.add_keyword(parent_node, copied)

    def _create_rename_command(self, new_name):
        return RenameKeywordOccurrences(self.controller.name, new_name,
                                        RenameProgressObserver(self.GetParent().GetParent()),
                                        self.controller.info)

    def OnFindUsages(self, event):
        Usages(self.controller, self._tree.highlight).show()


class VariableHandler(_CanBeRenamed, _ActionHandler):
    accepts_drag = lambda *args: False
    is_draggable = True
    is_variable = True
    OnMoveUp = OnMoveDown = lambda *args: None
    _actions = [_ActionHandler._label_rename, 'Delete']

    def OnDelete(self, event):
        self.remove()

    def remove(self):
        self.controller.delete()

    def rename(self, new_name):
        self.controller.execute(UpdateVariableName(new_name))


class ResourceRootHandler(_ActionHandler):
    can_be_rendered = is_draggable = is_user_keyword = is_test_suite = False
    rename = lambda self, new_name: False
    accepts_drag = lambda self, dragged: False
    _actions = [_ActionHandler._label_add_resource]

    @property
    def item(self):
        return None

    def OnAddResource(self, event):
        path = AddResourceDialog(self, self.controller).execute()
        if path:
            self.controller.load_resource(path, LoadProgressObserver(self))
