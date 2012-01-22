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

from robotide.publish import (RideTestCaseRemoved, RideVariableAdded,
        RideVariableRemoved, RideVariableMovedUp, RideVariableMovedDown,
        RideImportSettingAdded, RideUserKeywordRemoved, RideUserKeywordAdded,
        RideTestCaseAdded)
from robotide.publish.messages import RideItemMovedUp, RideItemMovedDown
from robotide.robotapi import is_list_var, is_scalar_var
from robotide import utils

from .basecontroller import ControllerWithParent
from .macrocontrollers import TestCaseController, UserKeywordController
from .settingcontrollers import (MetadataController, ImportController,
        VariableController)


class _WithListOperations(object):

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
        self._items.pop(index)
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


class VariableTableController(_TableController, _WithListOperations):

    def __iter__(self):
        return iter(VariableController(self, v) for v in self._table)

    def __getitem__(self, index):
        return VariableController(self, self._items[index])

    @property
    def _items(self):
        return self._table.variables

    def move_up(self, index):
        ctrl = self[index]
        _WithListOperations.move_up(self, index)
        self.mark_dirty()
        RideVariableMovedUp(item=ctrl).publish()

    def move_down(self, index):
        ctrl = self[index]
        _WithListOperations.move_down(self, index)
        self.mark_dirty()
        RideVariableMovedDown(item=ctrl).publish()

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

    def _validate_name(self, validator, name, item=None):
        return VariableNameValidation(self, validator, name, item)

    def delete(self, index):
        self.remove_var(self[index])

    def remove_var(self, var_controller):
        self._items.remove(var_controller.data)
        self.mark_dirty()
        self.notify_variable_removed(var_controller)

    def notify_variable_added(self, ctrl):
        self.datafile_controller.update_namespace()
        RideVariableAdded(datafile=self.datafile,
                          name=ctrl.name, item=ctrl).publish()

    def notify_variable_removed(self, ctrl):
        self.datafile_controller.update_namespace()
        RideVariableRemoved(datafile=self.datafile,
                            name=ctrl.name, item=ctrl).publish()


class _ScalarVarValidator(object):
    __call__ = lambda self, name: is_scalar_var(name)
    name = 'Scalar'
    prefix = '$'


class _ListVarValidator(object):
    __call__ = lambda self, name: is_list_var(name)
    name = 'List'
    prefix = '@'


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


class _MacroTable(_TableController):

    @property
    def _items(self):
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
        return len(self._items)

    def __getitem__(self, index):
        return self._create_controller(self._items[index])

    def move_up(self, item):
        items = self._items
        idx = items.index(item)
        if idx == 0:
            return False
        upper = idx - 1
        items[upper], items[idx] = items[idx], items[upper]
        self.mark_dirty()
        RideItemMovedUp(item=self._create_controller(item)).publish()
        return True

    def move_down(self, item):
        items = self._items
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
        self._items.remove(ctrl.data)
        if ctrl.data in self._item_to_controller:
            del self._item_to_controller[ctrl.data]
        self.datafile_controller.update_namespace()
        self.mark_dirty()
        self._notify_removal(ctrl)

    def add(self, ctrl):
        item = ctrl.data
        item.parent = self._table
        self._items.append(item)
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
        pass


class TestCaseTableController(_MacroTable):
    item_type = 'Test case'
    _controller_class = TestCaseController

    @property
    def _items(self):
        return self._table.tests

    def _notify_creation(self, name, ctrl):
        RideTestCaseAdded(datafile=self.datafile, name=name, item=ctrl).publish()

    def _notify_removal(self, item):
        RideTestCaseRemoved(datafile=self.datafile, name=item.name, item=item).publish()

    def new(self, name):
        return self._create_new(name)


class KeywordTableController(_MacroTable):
    item_type = 'User keyword'
    _controller_class = UserKeywordController

    @property
    def _items(self):
        return self._table.keywords

    def _notify_creation(self, name, ctrl):
        RideUserKeywordAdded(datafile=self.datafile, name=name, item=ctrl).publish()

    def _notify_removal(self, item):
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
    
    def _index_difference(self, original_list, sorted_list):
        """Determines the difference in sorting order for undo/redo"""
        index_difference = []
        for kw in original_list:
            counter = 0
            for kw2 in sorted_list:
                if kw.name == kw2.name:
                    index_difference.append(counter)
                    break
                counter += 1
        return index_difference

    def restore_keyword_order(self, list):
        """Restores the old order of the keyword list"""
        keywords_temp = []
        for i in list:
            keywords_temp.append(self._table.keywords[i])
        self._table.keywords = keywords_temp


class ImportSettingsController(_TableController, _WithListOperations):

    def __init__(self, parent_controller, table, resource_file_controller_factory=None):
        _TableController.__init__(self, parent_controller, table)
        self._resource_file_controller_factory = resource_file_controller_factory

    def __iter__(self):
        return iter(ImportController(self, imp) for imp in self._items)

    def __getitem__(self, index):
        return ImportController(self, self._items[index])

    @property
    def _items(self):
        return self._table.imports

    @property
    def resource_file_controller_factory(self):
        return self._resource_file_controller_factory

    def remove_import_data(self, imp):
        self.delete(self._items.index(imp))

    def delete(self, index):
        item = self[index]
        _WithListOperations.delete(self, index)
        item.publish_removed()
        self.notify_imports_modified()

    def add_library(self, name, argstr, alias, comment=None):
        import_ = self._table.add_library(name, utils.split_value(argstr),
                                          comment)
        import_.alias = alias
        self._parent.mark_dirty()
        self._publish_setting_added(name, 'library')
        self.notify_imports_modified()
        return self[-1]

    def add_resource(self, path, comment=None):
        import_ = self._table.add_resource(path, comment)
        self._parent.mark_dirty()
        self._publish_setting_added(path, 'resource')
        resource = self.resource_import_modified(path)
        self.notify_imports_modified()
        return self[-1]

    def add_variables(self, path, argstr, comment=None):
        self._table.add_variables(path, utils.split_value(argstr), comment)
        self._parent.mark_dirty()
        self._publish_setting_added(path, 'variables')
        return self[-1]

    def _publish_setting_added(self, name, type):
        RideImportSettingAdded(datafile=self.datafile_controller, name=name,
                               type=type).publish()

    def notify_imports_modified(self):
        self.datafile_controller.update_namespace()

    def resource_import_modified(self, path):
        return self._parent.resource_import_modified(path)


class MetadataListController(_TableController, _WithListOperations):

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
