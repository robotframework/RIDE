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
from robotide.publish.messages import RideItemStepsChanged, RideItemNameChanged,\
    RideItemSettingsChanged


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


class _WithUndoRedoStacks(object):
    
    @property
    def _undo(self):
        if not hasattr(self, '_undo_stack'):
            self._undo_stack = []
        return self._undo_stack

    @property
    def _redo(self):
        if not hasattr(self, '_redo_stack'):
            self._redo_stack = []
        return self._redo_stack
    
    def is_undo_empty(self):
        return self._undo == []
    
    def pop_from_undo(self):
        return self._undo.pop()
    
    def push_to_undo(self, command):
        self._undo.append(command)

    def clear_redo(self):
        self._redo_stack = []

    def is_redo_empty(self):
        return self._redo == []

    def pop_from_redo(self):
        return self._redo.pop()

    def push_to_redo(self, command):
        self._redo.append(command)

class _WithStepsController(ControllerWithParent, _WithUndoRedoStacks):

    def __init__(self, parent_controller, data):
        self._parent = parent_controller
        self.data = data
        self._init(data)

    @property
    def name(self):
        return self.data.name

    @property
    def steps(self):
        flattened_steps = []
        for step in self.data.steps:
            if step.is_for_loop():
                for_loop = ForLoopStepController(self, step)
                flattened_steps.append(for_loop)
                for sub_step in step.steps:
                    flattened_steps.append(IntendedStepController(for_loop, sub_step))
            else:
                flattened_steps.append(StepController(self, step))
        return flattened_steps

    def index_of_step(self, step):
        return self.data.steps.index(step)

    def replace_step(self, index, new_step):
        self.data.steps[index] = new_step

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

    def remove_empty_steps(self):
        steps = self.steps
        remove_these = [step for step in steps if self._is_empty_step(step)]
        remove_these.reverse()
        for step in remove_these :
            self._remove_step(step)

    def _is_empty_step(self, step):
        return step.as_list() == []

    def _empty_step(self):
        return Step([])

    def remove_step(self, index):
        self._remove_step(self.steps[index])

    def _remove_step(self, step):
        step.remove()

    def add_step(self, index, step = None):
        if step == None : step = self._empty_step()
        steps = self.data.steps
        self.data.steps = steps[:index]+[step]+steps[index:]

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

    def notify_value_changed(self):
        self._notify(RideItemNameChanged)

    def notify_settings_changed(self):
        self._notify(RideItemSettingsChanged)

    def notify_steps_changed(self):
        self._notify(RideItemStepsChanged)

    def _notify(self, messageclass):
        self.mark_dirty()
        messageclass(item=self).publish()

class TestCaseController(_WithStepsController):
    _populator = TestCasePopulator

    def _init(self, test):
        self._test = test

    def __eq__(self, other):
        if self is other : return True
        if other.__class__ != self.__class__ : return False
        return self._test == other._test

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


class UserKeywordController(_WithStepsController):
    _populator = UserKeywordPopulator

    def _init(self, kw):
        self._kw = kw

    def __eq__(self, other):
        if self is other : return True
        if other.__class__ != self.__class__ : return False
        return self._kw == other._kw

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


class StepController(object):

    def __init__(self, parent, step):
        self._step = step
        self.parent = parent

    def __eq__(self, other):
        if self is other : return True
        return self._steps_are_equal(self._step, other._step)

    def _steps_are_equal(self, fst, snd):
        if fst is snd: return True
        if not snd: return False
        return (fst.assign == snd.assign and
                fst.keyword == snd.keyword and
                fst.args == snd.args)

    def get_value(self, col):
        values = self.as_list()
        if len(values) <= col :
            return ''
        return values[col]

    def as_list(self):
        return self._step.as_list()

    def contains_keyword(self, name):
        return utils.eq(self._step.keyword or '', name)

    def rename_keyword(self, new_name):
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
    def logical_name(self):
        return '%s (Step %d)' % (self.parent.name, self.parent.steps.index(self) + 1)

    def change(self, col, new_value):
        cells = self.as_list()
        if col >= len(cells) :
            cells = cells + ['' for _ in range(col - len(cells) + 1)]
        cells[col] = new_value
        comment = self._get_comment(cells)
        if comment:
            cells.pop()
        self._recreate(cells, comment)

    def comment(self):
        self.shift_right(0)
        self.change(0, 'Comment')

    def uncomment(self):
        if self._step.keyword == 'Comment':
            self.shift_left(0)

    def shift_right(self, from_column):
        cells = self.as_list()
        comment = self._get_comment(cells)
        if len(cells) > from_column:
            if comment:
                cells.pop()
            cells = cells[:from_column] + [''] + cells[from_column:]
            self._recreate(cells, comment)

    def shift_left(self, from_column):
        cells = self.as_list()
        comment = self._get_comment(cells)
        if len(cells) > from_column:
            if comment:
                cells.pop()
            cells = cells[:from_column] + cells[from_column+1:]
            self._recreate(cells, comment)

    def remove_empty_columns_from_end(self):
        cells = self._step.as_list()
        while cells != [] and cells[-1].strip() == '':
            cells.pop()
        self._recreate(cells)

    def remove_empty_columns_from_beginning(self):
        cells = self._step.as_list()
        while cells != [] and cells[0].strip() == '':
            cells = cells[1:]
        self._recreate(cells)

    def remove(self):
        self.parent.data.steps.remove(self._step)

    def has_only_comment(self):
        non_empty_cells = [cell for cell in self._step.as_list() if cell.strip() != '']
        return len(non_empty_cells) == 1 and non_empty_cells[0].startswith('# ')

    def _get_comment(self, cells):
        return cells[-1][2:] if cells[-1].startswith('# ') else None

    def _recreate(self, cells, comment=None):
        self._step.__init__(cells, comment)

    def notify_value_changed(self):
        self.parent.notify_steps_changed()


class ForLoopStepController(StepController):

    @property
    def steps(self):
        return self._step.steps

    def _get_comment(self, cells):
        return None

    def comment(self):
        self._replace_with_new_cells(['Comment']+self.as_list())

    def uncomment(self):
        pass

    def contains_keyword(self, name):
        return False

    def add_step(self, step):
        self.steps.append(step)

    def _recreate(self, cells, comment=None):
        if cells[0] != self.as_list()[0]:
            self._replace_with_new_cells(cells)
        else:
            self._step.__init__(cells[1:])

    def remove(self):
        steps = self.parent.data.steps
        index = steps.index(self._step)
        steps.remove(self._step)
        self.parent.data.steps = steps[:index] + self._step.steps + steps[index:]

    def _replace_with_new_cells(self, cells):
        index = self.parent.index_of_step(self._step)
        self.parent.replace_step(index, Step(cells))
        for substep in self._step.steps:
            self.parent.add_step(index+1, Step(['']+substep.as_list()))

    def notify_steps_changed(self):
        self.notify_value_changed()


class IntendedStepController(StepController):

    def as_list(self):
        return ['']+self._step.as_list()

    def comment(self):
        self._step.__init__(['Comment'] + self._step.as_list())

    def uncomment(self):
        if self._step.keyword == 'Comment':
            self._step.__init__(self._step.as_list()[1:])

    def _recreate(self, cells, comment=None):
        if cells[0] == '':
            cells = cells[1:]
        self._step.__init__(cells)
        if self._step not in self.parent.steps:
            self.parent.add_step(self._step)

    def remove(self):
        self.parent.steps.remove(self._step)
