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


from robotide.robotapi import is_list_var, is_scalar_var
from robotide.publish import RideUserKeywordAdded, RideTestCaseAdded, RideUserKeywordRemoved
from robotide import utils

from robotide.controller.basecontroller import ControllerWithParent
from robotide.controller.settingcontroller import (MetadataController,
                                                   ImportController,
                                                   VariableController)
from robotide.controller.userscriptcontroller import (TestCaseController,
                                                      UserKeywordController)
from robotide.publish.messages import RideTestCaseRemoved


class _WithListOperations(object):

    def swap(self, ind1, ind2):
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

    def add_variable(self, name, value, comment=None):
        self._table.add(name, value, comment)
        self.mark_dirty()
        return self[-1]

    def validate_scalar_variable_name(self, name):
        return self._validate_name(_ScalarVarValidator(), name)

    def validate_list_variable_name(self, name):
        return self._validate_name(_ListVarValidator(), name)

    def _validate_name(self, validator, name):
        # TODO: Should communication be changed to use exceptions?
        if not validator(name):
            return '%s variable name must be in format %s{name}' % \
                    (validator.name, validator.prefix)
        if self._name_taken(name):
            return 'Variable with this name already exists.'
        return None

    def _name_taken(self, name):
        return any(utils.eq(name, var.name) for var in self._table)


class _ScalarVarValidator(object):
    __call__ = lambda self, name: is_scalar_var(name)
    name = 'Scalar'
    prefix = '$'

class _ListVarValidator(object):
    __call__ = lambda self, name: is_list_var(name)
    name = 'List'
    prefix = '@'


class _UserScriptTable(object):

    @property
    def _items(self):
        raise NotImplementedError(self.__class__)

    def __iter__(self):
        return iter(self._controller_class(self, item) for item in self._table)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._controller_class(self, self._items[index])

    def move_up(self, item):
        items = self._items
        idx = items.index(item)
        if idx == 0:
            return False
        upper = idx - 1
        items[upper], items[idx] = items[idx], items[upper]
        return True

    def move_down(self, item):
        items = self._items
        idx = items.index(item)
        if idx + 1 == len(items):
            return False
        lower = idx + 1
        items[idx], items[lower] = items[lower], items[idx]
        return True

    def validate_name(self, name):
        if not name:
            return '%s name cannot be empty.' % self._item_name
        for t in self._table:
            if t.name == name:
                return '%s with this name already exists.' % self._item_name
        return None

    def delete(self, ctrl):
        self._items.remove(ctrl.data)
        self.mark_dirty()
        self._notify_removal(ctrl)

    def add(self, ctrl):
        item = ctrl.data
        item.parent = self.datafile
        self._items.append(item)
        self.mark_dirty()
        self._notify_creation(ctrl.name, ctrl)

    def _create_new(self, name, config=None):
        ctrl = self._controller_class(self, self._table.add(name))
        self._configure_controller(ctrl, config)
        self.mark_dirty()
        self._notify_creation(name, ctrl)
        return ctrl

    def _configure_controller(self, ctrl, config):
        pass


class TestCaseTableController(_TableController, _UserScriptTable):
    _item_name = 'Test case'
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


class KeywordTableController(_TableController, _UserScriptTable):
    _item_name = 'User keyword'
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


class ImportSettingsController(_TableController, _WithListOperations):

    def __iter__(self):
        return iter(ImportController(self, imp) for imp in self._items)

    def __getitem__(self, index):
        return ImportController(self, self._items[index])

    @property
    def _items(self):
        return self._table.imports

    def add_library(self, name, argstr, alias, comment=None):
        import_ = self._table.add_library(name, utils.split_value(argstr),
                                          comment)
        import_.alias = alias
        self._parent.mark_dirty()
        return self[-1]

    def add_resource(self, path, comment=None):
        self._table.add_resource(path, comment)
        self._parent.mark_dirty()
        return self[-1]

    def add_variables(self, path, argstr, comment=None):
        self._table.add_variables(path, utils.split_value(argstr), comment)
        self._parent.mark_dirty()
        return self[-1]

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
