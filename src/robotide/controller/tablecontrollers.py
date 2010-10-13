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


from robot.parsing.tablepopulators import UserKeywordPopulator, TestCasePopulator
from robot.parsing.model import Step

from robotide.robotapi import DataRow, is_list_var, is_scalar_var
from robotide.controller.basecontroller import ControllerWithParent
from robotide.controller.settingcontroller import (DocumentationController,
        FixtureController, TagsController, TimeoutController,
        TemplateController, ArgumentsController, MetadataController,
        ImportController, ReturnValueController, VariableController)
from robotide.publish import RideUserKeywordAdded, RideTestCaseAdded
from robotide import utils
from robotide.controller.arguments import parse_arguments_to_var_dict


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


class _TcUkBase(object):

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

    @property
    def _items(self):
        raise NotImplementedError(self.__class__)


class TestCaseTableController(_TableController, _TcUkBase):
    _item_name = 'Test case'

    def __iter__(self):
        return iter(TestCaseController(self, t) for t in self._table)

    def __getitem__(self, index):
        return TestCaseController(self, self._table.tests[index])

    def __len__(self):
        return len(self._items)

    def add(self, test_ctrl):
        test = test_ctrl.data
        test.parent = self.datafile
        self._table.tests.append(test)
        self.mark_dirty()

    def new(self, name):
        tc_controller = TestCaseController(self, self._table.add(name))
        self.mark_dirty()
        RideTestCaseAdded(datafile=self.datafile, name=name).publish()
        return tc_controller

    def delete(self, test):
        self._table.tests.remove(test)
        self.mark_dirty()

    @property
    def _items(self):
        return self._table.tests


class KeywordTableController(_TableController, _TcUkBase):
    _item_name = 'User keyword'

    def __iter__(self):
        return iter(UserKeywordController(self, kw) for kw in self._table)

    def __getitem__(self, index):
        return UserKeywordController(self, self._table.keywords[index])

    def __len__(self):
        return len(self._items)

    def add(self, kw_ctrl):
        kw = kw_ctrl.data
        kw.parent = self.datafile
        self._table.keywords.append(kw)
        self.mark_dirty()

    def new(self, name, argstr=''):
        kw_controller = UserKeywordController(self, self._table.add(name))
        kw_controller.arguments.set_value(argstr)
        self.mark_dirty()
        RideUserKeywordAdded(datafile=self.datafile, name=name).publish()
        return kw_controller

    def delete(self, kw):
        self._table.keywords.remove(kw)
        self.mark_dirty()

    @property
    def _items(self):
        return self._table.keywords


class _WithStepsController(ControllerWithParent):
    def __init__(self, parent_controller, data):
        self._parent = parent_controller
        self.data = data
        self._init(data)

    @property
    def name(self):
        return self.data.name

    @property
    def steps(self):
        return [StepController(self, s) for s in self.data.steps]

    def set_steps(self, steps):
        self.data.steps = steps

    def execute(self, command):
        return command.execute(self)

    def parse_steps_from_rows(self, rows):
        self.data.steps = []
        pop = self._populator(lambda name: self.data)
        for r in rows:
            r = DataRow([''] + r)
            pop.add(r)
        pop.populate()

    def rename(self, new_name):
        self.data.name = new_name
        self.mark_dirty()

    def copy(self, name):
        new = self._parent.new(name)
        for orig, copied in zip(self.settings, new.settings):
            if orig.is_set:
                copied.set_value(orig.value)
            copied.set_comment(orig.comment)
        new.data.steps = self.data.steps[:]
        return new

    def create_user_keyword(self, name, arg_values, observer):
        err = self.datafile_controller.validate_keyword_name(name)
        if err:
            raise ValueError(err)
        argstr = ' | '.join(('${arg%s}' % (i + 1) for i in range(len(arg_values))))
        controller = self.datafile_controller.new_keyword(name, argstr)
        observer(controller)

    def extract_keyword(self, name, argstr, step_range, observer):
        extracted_steps = self._extract_steps(step_range)
        self._replace_steps_with_kw(name, step_range)
        observer(self._create_extracted_kw(name, argstr, extracted_steps))

    def _extract_steps(self, step_range):
        rem_start, rem_end = step_range
        extracted_steps = self.data.steps[rem_start:rem_end + 1]
        return extracted_steps

    def _replace_steps_with_kw(self, name, step_range):
        steps_before_extraction_point = self.data.steps[:step_range[0]]
        extracted_kw_step = [Step([name])]
        steps_after_extraction_point = self.data.steps[step_range[1] + 1:]
        self.set_steps(steps_before_extraction_point + extracted_kw_step + 
                       steps_after_extraction_point)

    def _create_extracted_kw(self, name, argstr, extracted_steps):
        controller = self.datafile_controller.new_keyword(name, argstr)
        controller.set_steps(extracted_steps)
        return controller

    def validate_name(self, name):
        return self._parent.validate_name(name)


class TestCaseController(_WithStepsController):
    _populator = TestCasePopulator

    def _init(self, test):
        self._test = test
        self._listeners = Listeners()

    @property
    def settings(self):
        return [DocumentationController(self, self._test.doc),
                FixtureController(self, self._test.setup),
                FixtureController(self, self._test.teardown),
                TagsController(self, self._test.tags),
                TimeoutController(self, self._test.timeout),
                TemplateController(self, self._test.template)]

    def move_up(self):
        return self._parent.move_up(self._test)

    def move_down(self):
        return self._parent.move_down(self._test)

    def delete(self):
        return self._parent.delete(self._test)

    def validate_test_name(self, name):
        return self._parent.validate_name(name)

    def validate_keyword_name(self, name):
        return self.datafile_controller.validate_keyword_name(name)

    def get_local_variables(self):
        return {}

    def add_test_changed_listener(self, listener):
        self._listeners.add(listener)

    def notify_changed(self):
        self._listeners.notify(self)

class Listeners(object):

    def __init__(self):
        self._listeners = []

    def add(self, listener):
        self._listeners.append(listener)

    def notify(self, data):
        for l in self._listeners:
            l(data)


class UserKeywordController(_WithStepsController):
    _populator = UserKeywordPopulator

    def _init(self, kw):
        self._kw = kw

    def move_up(self):
        return self._parent.move_up(self._kw)

    def move_down(self):
        return self._parent.move_down(self._kw)

    def delete(self):
        self._parent.delete(self._kw)

    @property
    def settings(self):
        return [DocumentationController(self, self._kw.doc),
                ArgumentsController(self, self._kw.args),
                TimeoutController(self, self._kw.timeout),
                ReturnValueController(self, self._kw.return_)]

    @property
    def arguments(self):
        return ArgumentsController(self, self._kw.args)

    def validate_keyword_name(self, name):
        return self._parent.validate_name(name)

    def get_local_variables(self):
        return parse_arguments_to_var_dict(self._kw.args.value)


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

    def add_resource(self, name, comment=None):
        self._add_import(self._table.add_resource, name, comment)
        return self[-1]

    def add_variables(self, argstr, comment=None):
        self._add_import(self._table.add_variables, argstr, comment)
        return self[-1]

    def _add_import(self, adder, argstr, comment):
        name, args = self._split_to_name_and_args(argstr)
        adder(name, args, comment=comment)
        self._parent.mark_dirty()

    def _split_to_name_and_args(self, argstr):
        parts = utils.split_value(argstr)
        return parts[0], parts[1:]

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


class StepController(object):

    def __init__(self, parent, step):
        self._step = step
        self.parent = parent

    def __eq__(self, other):
        if self is other : return True
        if not other : return False
        return self._steps_are_equal(self._step, other._step)

    def _steps_are_equal(self, fst, snd):
        if fst is snd: return True
        if not snd: return False
        return (fst.assign == snd.assign and
                fst.keyword == snd.keyword and
                fst.args == snd.args)

    def as_list(self):
        return self._step.as_list()

    def contains_keyword(self, name):
        return utils.eq(self._step.keyword or '', name)

    def keyword_rename(self, new_name):
        self._step.keyword = new_name

    @property
    def keyword(self):
        return self._step.keyword

    @property
    def assign(self):
        return self._step.assign

    @property
    def args(self):
        return self._step.args

    @property
    def vars(self):
        return self._step.vars

    @property
    def steps(self):
        return self._step.steps

    @property
    def logical_name(self):
        return '%s (Step %d)' % (self.parent.name, self.parent.steps.index(self) + 1)

    def change(self, col, new_value):
        cells = self._step.as_list(include_comment=False)
        cells[col] = new_value
        self._step.__init__(cells, comment=self._step.comment)

