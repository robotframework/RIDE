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

from .. import utils
from ..publish import (RideTestCaseRemoved, RideVariableAdded, RideVariableRemoved, RideVariableMovedUp,
                       RideVariableMovedDown, RideUserKeywordRemoved, RideUserKeywordAdded, RideTestCaseAdded)
from ..publish.messages import RideItemMovedUp, RideItemMovedDown
from ..robotapi import is_list_var, is_scalar_var, is_dict_var
from ..utils import variablematcher
from .basecontroller import ControllerWithParent
from . import macrocontrollers  # TestCaseController, UserKeywordController
from .settingcontrollers import MetadataController, import_controller, VariableController


class WithListOperations(object):

    def move_up(self, index):
        if index > 0:
            self._swap(index - 1, index)

    def move_down(self, index):
        if index < len(self._items) - 1:
            self._swap(index, index + 1)

    def _swap(self, ind1, ind2):
        self._items[ind1], self._items[ind2] = self._items[ind2], self._items[ind1]
        self.mark_dirty()

    def delete(self, index):
        if isinstance(self._items, list):
            self._items.pop(index)
        else:
            self._items.data.pop(index)
        self.mark_dirty()

    @property
    def _items(self):
        raise NotImplementedError(self.__class__)

    def mark_dirty(self):
        raise NotImplementedError(self.__class__)


class _TableController(ControllerWithParent):

    def __init__(self, parent_controller, table):
        self._parent = parent_controller
        self._table = table

    @staticmethod
    def _index_difference(original_list, sorted_list):
        """Determines the difference in sorting order for undo/redo"""
        index_difference = []
        for item in original_list:
            counter = 0
            for item2 in sorted_list:
                if item.name == item2.name:
                    index_difference.append(counter)
                    break
                counter += 1
        return index_difference


class VariableTableController(_TableController, WithListOperations):

    def __init__(self, parent_controller, table):
        _TableController.__init__(self, parent_controller, table)
        self._variable_cache = {}

    def _get(self, variable):
        if variable not in self._variable_cache:
            self._variable_cache[variable] = VariableController(self, variable)
        return self._variable_cache[variable]

    def __iter__(self):
        return iter(self._get(v) for v in self._table)

    def __getitem__(self, index):
        return self._get(self._items[index])

    def index(self, ctrl):
        return [v for v in self].index(ctrl)

    @property
    def _items(self):
        return self._table.variables

    def move_up(self, index):
        if index == 0:
            return False
        ctrl = self[index]
        WithListOperations.move_up(self, index)
        other = self[index]
        self.mark_dirty()
        RideVariableMovedUp(item=ctrl, other=other).publish()

    def move_down(self, index):
        if index + 1 == len(self._items):
            return False
        ctrl = self[index]
        WithListOperations.move_down(self, index)
        other = self[index]
        self.mark_dirty()
        RideVariableMovedDown(item=ctrl, other=other).publish()

    def add_variable(self, name, value, comment=None):
        self._table.add(name, value, comment)
        self.mark_dirty()
        var_controller = self[-1]
        self.notify_variable_added(var_controller)
        return var_controller

    def validate_scalar_variable_name(self, name, item=None):
        return self._validate_name(_ScalarVarValidator(), name, item)

    def validate_list_variable_name(self, name, item=None):
        return self._validate_name(_ListVarValidator(), name, item)

    def validate_dict_variable_name(self, name, item=None):
        return self._validate_name(_DictVarValidator(), name, item)

    def _validate_name(self, validator, name, item=None):
        return VariableNameValidation(self, validator, name, item)

    def delete(self, index):
        self.remove_var(self[index])

    def remove_var(self, var_controller):
        self._items.remove(var_controller.data)
        del self._variable_cache[var_controller.data]
        self.mark_dirty()
        self.notify_variable_removed(var_controller)

    def notify_variable_added(self, ctrl):
        self.datafile_controller.update_namespace()
        RideVariableAdded(datafile=self.datafile,
                          name=ctrl.name, item=ctrl,
                          index=ctrl.index).publish()

    def notify_variable_removed(self, ctrl):
        self.datafile_controller.update_namespace()
        RideVariableRemoved(datafile=self.datafile, name=ctrl.name, item=ctrl).publish()

    def contains_variable(self, name):
        vars_as_list = []
        for var in self._items:
            vars_as_list += var.as_list()
        return any(variablematcher.value_contains_variable(string, name)
                   for string in vars_as_list)

    def sort(self):
        """Sorts the variables of the controller by name"""
        variables_sorted = sorted(self._table.variables, key=lambda variable: variable.name)
        index_difference = self._index_difference(self._table.variables, variables_sorted)
        self._table.variables = variables_sorted
        return index_difference

    def restore_variable_order(self, rlist):
        """Restores the old order of the variable list"""
        variables_temp = []
        for i in rlist:
            variables_temp.append(self._table.variables[i])
        self._table.variables = variables_temp


class _ScalarVarValidator(object):
    __call__ = lambda self, name: is_scalar_var(name)
    name = 'Scalar'
    prefix = '$'


class _ListVarValidator(object):
    __call__ = lambda self, name: is_list_var(name)
    name = 'List'
    prefix = '@'


class _DictVarValidator(object):
    __call__ = lambda self, name: is_dict_var(name)
    name = 'Dictionary'
    prefix = '&'


class _NameValidation(object):

    def __init__(self, table, name, named_ctrl=None):
        self._table = table
        self.error_message = ''
        self._named_ctrl = named_ctrl
        self._validate(name.strip())

    def _name_taken(self, name):
        return any(utils.eq(name, item.name, ignore=['_'])
                   for item in self._table if item != self._named_ctrl)


class VariableNameValidation(_NameValidation):

    def __init__(self, table, validator, name, named_ctrl=None):
        self._validator = validator
        _NameValidation.__init__(self, table, name, named_ctrl)

    def _validate(self, name):
        if not self._validator(name):
            self.error_message = '%s variable name must be in format %s{name}' % \
                    (self._validator.name, self._validator.prefix)
        if self._name_taken(name):
            self.error_message = 'Variable with this name already exists.'


class MacroNameValidation(_NameValidation):

    def _validate(self, name):
        if not name:
            self.error_message = '%s name cannot be empty.' % \
                    self._table.item_type
        if self._name_taken(name):
            self.error_message = '%s with this name already exists.' % \
                    self._table.item_type
        if "\n" in name:
            self.error_message = '%s name contains newlines' % \
                    self._table.item_type


class _MacroTable(_TableController):

    @property
    def items(self):
        raise NotImplementedError(self.__class__)

    def __iter__(self):
        return iter(self._create_controller(item) for item in self._table)

    def _create_controller(self, item):
        if item not in self._item_to_controller:
            self._item_to_controller[item] = self._controller_class(self, item)
        return self._item_to_controller[item]

    @property
    def _item_to_controller(self):
        if not hasattr(self, '_item_to_controller_attribute'):
            self._item_to_controller_attribute = {}
        return self._item_to_controller_attribute

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self._create_controller(self.items[index])

    def move_up(self, item):
        items = self.items
        idx = items.index(item)
        if idx == 0:
            return False
        upper = idx - 1
        items[upper], items[idx] = items[idx], items[upper]
        self.mark_dirty()
        RideItemMovedUp(item=self._create_controller(item)).publish()
        return True

    def move_down(self, item):
        items = self.items
        idx = items.index(item)
        if idx + 1 == len(items):
            return False
        lower = idx + 1
        items[idx], items[lower] = items[lower], items[idx]
        self.mark_dirty()
        RideItemMovedDown(item=self._create_controller(item)).publish()
        return True

    def validate_name(self, name, named_ctrl=None):
        return MacroNameValidation(self, name, named_ctrl)

    def delete(self, ctrl):
        self.items.remove(ctrl.data)
        if ctrl.data in self._item_to_controller:
            del self._item_to_controller[ctrl.data]
        self.datafile_controller.update_namespace()
        self.mark_dirty()
        self._notify_removal(ctrl)

    def add(self, ctrl):
        item = ctrl.data
        item.parent = self._table
        self.items.append(item)
        new_controller = self._create_controller(item)
        self.datafile_controller.update_namespace()
        self.mark_dirty()
        self._notify_creation(new_controller.name, new_controller)

    def _create_new(self, name, config=None):
        name = name.strip()
        ctrl = self._create_controller(self._table.add(name))
        self._configure_controller(ctrl, config)
        self.datafile_controller.update_namespace()
        self.mark_dirty()
        self._notify_creation(name, ctrl)
        return ctrl

    def _configure_controller(self, ctrl, config):
        """ Don't know this exists ;) """
        pass


class TestCaseTableController(_MacroTable):
    __test__ = False
    item_type = 'Test case'
    _controller_class = macrocontrollers.TestCaseController

    @property
    def items(self):
        return self._table.tests

    def _notify_creation(self, name, ctrl):
        RideTestCaseAdded(datafile=self.datafile, name=name, item=ctrl).publish()

    def _notify_removal(self, item):
        RideTestCaseRemoved(datafile=self.datafile, name=item.name, item=item).publish()

    def new(self, name):
        return self._create_new(name)

    def sort(self):
        """Sorts the tests of the controller by name"""
        tests_sorted = sorted(self._table.tests, key=lambda testcase: testcase.name)
        index_difference = self._index_difference(self._table.tests, tests_sorted)
        self._table.tests = tests_sorted
        return index_difference

    def restore_test_order(self, rlist):
        """Restores the old order of the test list"""
        tests_temp = []
        for i in rlist:
            tests_temp.append(self._table.tests[i])
        self._table.tests = tests_temp


class KeywordTableController(_MacroTable):
    item_type = 'User keyword'
    _controller_class = macrocontrollers.UserKeywordController

    @property
    def items(self):
        return self._table.keywords

    def _notify_creation(self, name, ctrl):
        # print("DEBUG notify_creation %s" % name)
        RideUserKeywordAdded(datafile=self.datafile, name=name, item=ctrl).publish()

    def _notify_removal(self, item):
        # print("DEBUG notify_removal %s" % item.name)
        RideUserKeywordRemoved(datafile=self.datafile, name=item.name, item=item).publish()

    def new(self, name, argstr=''):
        return self._create_new(name, argstr)

    def _configure_controller(self, ctrl, config):
        if config:
            ctrl.arguments.set_value(config)

    def sort(self):
        """Sorts the keywords of the controller by name"""
        keywords_sorted = sorted(self._table.keywords, key=lambda userkeyword: userkeyword.name)
        index_difference = self._index_difference(self._table.keywords, keywords_sorted)
        self._table.keywords = keywords_sorted
        return index_difference

    def restore_keyword_order(self, rlist):
        """Restores the old order of the keyword list"""
        keywords_temp = []
        for i in rlist:
            keywords_temp.append(self._table.keywords[i])
        self._table.keywords = keywords_temp


class ImportSettingsController(_TableController, WithListOperations):

    def __init__(self, parent_controller, table, resource_file_controller_factory=None):
        _TableController.__init__(self, parent_controller, table)
        self._resource_file_controller_factory = resource_file_controller_factory
        self.__import_controllers = None

    def __iter__(self):
        return iter(self._import_controllers)

    def __getitem__(self, index):
        return self._import_controllers[index]

    @property
    def _import_controllers(self):
        if self.__import_controllers is None:
            self.__import_controllers = [self._import_controller(imp) for imp in self._items]
        return self.__import_controllers

    def _import_controller(self, import_):
        return import_controller(self, import_)

    @property
    def _items(self):
        return self._table.imports

    @property
    def resource_file_controller_factory(self):
        return self._resource_file_controller_factory

    def _swap(self, ind1, ind2):
        imps = self._import_controllers
        imps[ind1], imps[ind2] = imps[ind2], imps[ind1]
        WithListOperations._swap(self, ind1, ind2)

    def remove_import_data(self, imp):
        self.delete(self._items.data.index(imp))

    def delete(self, index):
        item = self[index]
        WithListOperations.delete(self, index)
        self._import_controllers.pop(index)
        item.publish_removed()
        self.notify_imports_modified()

    def add_library(self, name, argstr, alias, comment=None):
        self._import_controllers # Call property since it has to exist before adding new
        import_ = self._table.add_library(name, utils.split_value(argstr),
                                          comment)
        import_.alias = alias
        self._parent.mark_dirty()
        self._add_controller(import_)
        self.notify_imports_modified()
        return self[-1]

    def _add_controller(self, import_):
        ctrl = self._import_controller(import_)
        ctrl.publish_added()
        self._import_controllers.append(ctrl)

    def add_resource(self, path, comment=None):
        self._import_controllers # Have to exist before adding new
        import_ = self._table.add_resource(path, comment)
        self._parent.mark_dirty()
        self.resource_import_modified(path)
        self._add_controller(import_)
        self.notify_imports_modified()
        return self[-1]

    def add_variables(self, path, argstr, comment=None):
        self._import_controllers # Have to exist before adding new
        import_ = self._table.add_variables(path, utils.split_value(argstr), comment)
        self._parent.mark_dirty()
        self._add_controller(import_)
        return self[-1]

    def notify_imports_modified(self):
        self.datafile_controller.update_namespace()

    def resource_import_modified(self, path):
        return self._parent.resource_import_modified(path)


class MetadataListController(_TableController, WithListOperations):

    def __iter__(self):
        return iter(MetadataController(self, m) for m in self._items)

    def __getitem__(self, index):
        return MetadataController(self, self._items[index])

    @property
    def _items(self):
        return self._table.metadata

    def add_metadata(self, name, value, comment=None):
        self._table.add_metadata(name, value, comment)
        self._parent.mark_dirty()
        return self[-1]
