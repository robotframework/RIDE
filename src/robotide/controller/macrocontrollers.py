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

from robotide.controller.basecontroller import ControllerWithParent,\
    _BaseController
from robotide.controller.settingcontrollers import (DocumentationController,
        FixtureController, TagsController, TimeoutController,
        TemplateController, ArgumentsController, ReturnValueController)
from robotide.controller.arguments import parse_arguments_to_var_dict
from robotide.controller.basecontroller import WithUndoRedoStacks
from robotide.publish.messages import RideItemStepsChanged, RideItemNameChanged,\
    RideItemSettingsChanged
from robotide import utils
import re
from robotide.controller.cellinfo import CellInfo, CellType, ContentType


KEYWORD_NAME_FIELD = 'Keyword Name'
TESTCASE_NAME_FIELD = 'Test Case Name'

def _empty_step():
    return Step([])


class ItemNameController(object):

    def __init__(self, item):
        self._item = item

    def contains_keyword(self, name):
        return self._item.name == name

    def replace_keyword(self, new_name, old_value=None):
        self._item.rename(new_name)

    def rename(self, new_name):
        self._item.rename(new_name)

    def notify_value_changed(self):
        self._item.notify_name_changed()

    @property
    def logical_name(self):
        return '%s (%s)' % (self._item.name, self._name_field)


class KeywordNameController(ItemNameController):
    _name_field = KEYWORD_NAME_FIELD


class TestCaseNameController(ItemNameController):
    _name_field = TESTCASE_NAME_FIELD


class _WithStepsController(ControllerWithParent, WithUndoRedoStacks):

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
                flattened_steps.extend(for_loop.steps)
            else:
                flattened_steps.append(StepController(self, step))
        return flattened_steps

    def step(self, index):
        return self.steps[index]

    def index_of_step(self, step):
        return [s._step for s in self.steps].index(step)

    def replace_step(self, index, new_step):
        self.data.steps[index] = new_step

    def move_step_up(self, index):
        self.step(index).move_up()

    def move_step_down(self, index):
        self.step(index).move_down()

    def set_steps(self, steps):
        self.data.steps = steps

    def execute(self, command):
        return command.execute(self)

    def update_namespace(self):
        self.datafile_controller.update_namespace()

    def get_cell_info(self, row, col, selection_content=None):
        if len(self.steps) <= row:
            return None
        return self.step(row).get_cell_info(col, selection_content)

    def get_keyword_info(self, kw_name):
        return self.datafile_controller.keyword_info(kw_name)

    def is_user_keyword(self, value):
        return self.datafile_controller.is_user_keyword(value)

    def is_library_keyword(self, value):
        return self.datafile_controller.is_library_keyword(value)

    def delete(self):
        return self._parent.delete(self)

    def rename(self, new_name):
        self.data.name = new_name.strip()
        self.mark_dirty()

    def copy(self, name):
        new = self._parent.new(name)
        for orig, copied in zip(self.settings, new.settings):
            if orig.is_set:
                copied.set_value(orig.value)
            copied.set_comment(orig.comment)
        new.data.steps = [Step(s.as_list()) for s in self.steps]
        return new

    def remove_empty_steps(self):
        steps = self.steps
        remove_these = [step for step in steps if self._is_empty_step(step)]
        remove_these.reverse()
        for step in remove_these :
            self._remove_step(step)

    def _is_empty_step(self, step):
        return step.as_list() == []

    def remove_step(self, index):
        self._remove_step(self.steps[index])

    def recreate(self):
        self._parent.add(self)

    def _remove_step(self, step):
        step.remove()

    def add_step(self, index, step=None):
        if step is None:
            step = _empty_step()
        if index == len(self.steps):
            self.data.steps.append(step)
        else:
            previous_step = self.step(index)
            previous_step.insert_before(step)

    def create_keyword(self, name, argstr):
        validation = self.datafile_controller.validate_keyword_name(name)
        if not validation.valid:
            raise ValueError(validation.error_message)
        return self.datafile_controller.create_keyword(name, argstr)

    def create_test(self, name):
        return self.datafile_controller.create_test(name)

    def extract_keyword(self, name, argstr, step_range):
        extracted_steps = self._extract_steps(step_range)
        self._replace_steps_with_kw(name, step_range)
        self._create_extracted_kw(name, argstr, extracted_steps)

    def _get_raw_steps(self):
        return self.data.steps

    def _set_raw_steps(self, steps):
        self.data.steps = steps

    def _extract_steps(self, step_range):
        rem_start, rem_end = step_range
        extracted_steps = self.steps[rem_start:rem_end + 1]
        return self._convert_controller_to_steps(extracted_steps)

    def _convert_controller_to_steps(self, step_controllers):
        return [Step(s.as_list()) for s in step_controllers]

    def _replace_steps_with_kw(self, name, step_range):
        steps_before_extraction_point = self._convert_controller_to_steps(self.steps[:step_range[0]])
        extracted_kw_step = [Step([name])]
        steps_after_extraction_point = self._convert_controller_to_steps(self.steps[step_range[1] + 1:])
        self.set_steps(steps_before_extraction_point + extracted_kw_step +
                       steps_after_extraction_point)

    def _create_extracted_kw(self, name, argstr, extracted_steps):
        controller = self.datafile_controller.create_keyword(name, argstr)
        controller.set_steps(extracted_steps)
        return controller

    def validate_name(self, name):
        return self._parent.validate_name(name)

    def notify_name_changed(self):
        self._notify(RideItemNameChanged)

    def notify_settings_changed(self):
        self._notify(RideItemSettingsChanged)

    def notify_steps_changed(self):
        self._notify(RideItemStepsChanged)

    def _notify(self, messageclass):
        self.mark_dirty()
        messageclass(item=self).publish()


class TestCaseController(_BaseController, _WithStepsController):
    _populator = TestCasePopulator

    def _init(self, test):
        self._test = test

    def __eq__(self, other):
        if self is other : return True
        if other.__class__ != self.__class__ : return False
        return self._test == other._test

    @property
    def test_name(self):
        return TestCaseNameController(self)

    @property
    def tags(self):
        return TagsController(self, self._test.tags)

    def add_tag(self, tag):
        self.tags.add(tag)

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

    def validate_test_name(self, name):
        return self._parent.validate_name(name)

    def validate_keyword_name(self, name):
        return self.datafile_controller.validate_keyword_name(name)

    def get_local_variables(self):
        return {}


class UserKeywordController(_BaseController, _WithStepsController):
    _populator = UserKeywordPopulator

    def _init(self, kw):
        self._kw = kw

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self._kw == other._kw

    @property
    def keyword_name(self):
        return KeywordNameController(self)

    def move_up(self):
        return self._parent.move_up(self._kw)

    def move_down(self):
        return self._parent.move_down(self._kw)

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



class StepController(object):

    def __init__(self, parent, step):
        self._step = step
        self.parent = parent
        self._remove_whitespace_from_comment()

    def _remove_whitespace_from_comment(self):
        # TODO: This can be removed with RF 2.6
        if self._step.comment:
            self._step.comment = self._step.comment.strip()

    def get_keyword_info(self, kw):
        if not kw:
            return None
        return self.parent.get_keyword_info(kw)

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

    def get_cell_info(self, col, selection_content):
        cell_type = self._get_cell_type(col, selection_content)
        content_type = self._get_content_type(col)
        return CellInfo(content_type, cell_type)

    def _get_cell_type(self, col, selection_content):
        # TODO: refactor
        if selection_content and self._selection_matches(selection_content, self.get_value(col)):
            return CellType.HIGHLIGHTED
        col -= len(self._step.assign)
        if col < 0:
            return CellType.MANDATORY
        info = self.get_keyword_info(self._step.keyword)
        if not info:
            return CellType.UNKNOWN
        elif col == 0:
            return CellType.MANDATORY
        args = info.arguments
        args_amount = len(args)
        if args_amount == 0:
            return CellType.MANDATORY_EMPTY
        if col >= args_amount and self._last_argument_is_varargs(args):
            return CellType.OPTIONAL
        if self._has_list_var_value_before(col-1):
            return CellType.UNKNOWN
        if col > args_amount:
            return CellType.MANDATORY_EMPTY
        defaults = [arg for arg in args if '=' in arg]
        if col <= args_amount-len(defaults):
            return CellType.MANDATORY
        return CellType.OPTIONAL

    def _selection_matches(self, selection_content, cell_value):
        # TODO: refactor
        selection = utils.normalize(selection_content, ignore=['_'])
        if not selection:
            return False
        cell = utils.normalize(cell_value, ignore=['_'])
        if selection == cell:
            return True
        match = self._match_variable(selection)
        if match:
            if match.groups()[0] in cell:
                return True
            vars = self._find_variable_basenames(cell)
            if vars:
                for var_basename in vars:
                    if var_basename == match.groups()[1]:
                        return True
        return False

    def _last_argument_is_varargs(self, args):
        return args[-1].startswith('*')

    def _has_list_var_value_before(self, arg_index):
        for idx, value in enumerate(self.args):
            if idx > arg_index:
                return False
            if self._is_list_variable(value):
                return True
        return False

    def _get_content_type(self, col):
        if self._is_commented(col):
            return ContentType.COMMENTED
        if self._get_last_none_empty_col_idx() < col:
            return ContentType.EMPTY
        value = self.get_value(col)
        if self._is_variable(value):
            return ContentType.VARIABLE
        if self.is_user_keyword(value):
            return ContentType.USER_KEYWORD
        if self.is_library_keyword(value):
            return ContentType.LIBRARY_KEYWORD
        return ContentType.STRING

    def _get_last_none_empty_col_idx(self):
        values = self.as_list()
        for i in reversed(range(len(values))):
            if values[i].strip() != '':
                return i
        return None

    def _is_variable(self, value):
        return self._match_variable(value)

    def _match_variable(self, value):
        return re.match('([\$\@]{(.*?)})=?', value)

    def _find_variable_basenames(self, value):
        return re.findall('\${(.+?)[^\s\w]+.*?}?', value)

    def _is_list_variable(self, value):
        return re.match('\@{.*}', value)

    def is_user_keyword(self, value):
        return self.parent.is_user_keyword(value)

    def is_library_keyword(self, value):
        return self.parent.is_library_keyword(value)

    def as_list(self):
        return self._step.as_list()

    def contains_keyword(self, name):
        return any(utils.eq(item, name) for item in [self.keyword or ''] + self.args)

    def replace_keyword(self, new_name, old_name):
        if utils.eq(old_name, self.keyword or ''):
            self._step.keyword = new_name
        for index, value in enumerate(self.args):
            if utils.eq(old_name, value):
                self._step.args[index] = new_name

    @property
    def datafile(self):
        return self.parent.datafile

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
        return '%s (Step %d)' % (self.parent.name,
                                 self.parent.data.steps.index(self._step) + 1)

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

    def _is_commented(self, col):
        if self._has_comment_keyword():
            return col > self._keyword_column
        for i in range(min(col+1, len(self.as_list()))):
            if self.get_value(i).strip().startswith('#'):
                return True
        return False

    @property
    def _keyword_column(self):
        return 0

    def _has_comment_keyword(self):
        if self.keyword is None:
            return False
        return self.keyword.strip().lower() == "comment"

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

    def insert_before(self, new_step):
        steps = self.parent._get_raw_steps()
        index = steps.index(self._step)
        self.parent._set_raw_steps(steps[:index]+[new_step]+steps[index:])

    def insert_after(self, new_step):
        steps = self.parent._get_raw_steps()
        index = steps.index(self._step)+1
        self.parent._set_raw_steps(steps[:index]+[new_step]+steps[index:])

    def remove_empty_columns_from_end(self):
        cells = self.as_list()
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

    def move_up(self):
        previous_step = self.parent.step(self._index()-1)
        self.remove()
        previous_step.insert_before(self._step)

    def move_down(self):
        next_step = self.parent.step(self._index()+1)
        self.remove()
        next_step.insert_after(self._step)

    def _index(self):
        return self.parent.index_of_step(self._step)

    def has_only_comment(self):
        non_empty_cells = [cell for cell in self._step.as_list() if cell.strip() != '']
        return len(non_empty_cells) == 1 and non_empty_cells[0].startswith('# ')

    def _get_comment(self, cells):
        if not cells:
            return None
        return cells[-1][2:].strip() if cells[-1].startswith('# ') else None

    def _recreate(self, cells, comment=None):
        self._step.__init__(cells, comment)

    def notify_value_changed(self):
        self.parent.notify_steps_changed()


class ForLoopStepController(StepController):

    def move_up(self):
        previous_step = self.parent.step(self._index()-1)
        self._get_raw_steps().insert(0, previous_step._step)
        previous_step.remove()

    def move_down(self):
        next_step = self.step(self._index()+1)
        next_step.move_up()

    def insert_after(self, new_step):
        self._get_raw_steps().insert(0, new_step)

    def step(self, index):
        return self.parent.step(index)

    def _remove_whitespace_from_comment(self):
        pass

    def _has_comment_keyword(self):
        return False

    def _get_raw_steps(self):
        return self._step.steps

    def _set_raw_steps(self, steps):
        self._step.steps = steps

    def _get_cell_type(self, col):
        until_range = len(self._step.vars)+1
        if col <= until_range:
            return CellType.MANDATORY
        if not self._step.range:
            return CellType.OPTIONAL
        if col <= until_range+2:
            return CellType.MANDATORY
        if col == until_range+3:
            return CellType.OPTIONAL
        return CellType.MANDATORY_EMPTY

    @property
    def steps(self):
        return [IntendedStepController(self, sub_step) for sub_step in self._get_raw_steps()]

    def index_of_step(self, step):
        index_in_for_loop = self._get_raw_steps().index(step)
        return self._index()+index_in_for_loop+1

    def _get_comment(self, cells):
        return None

    def comment(self):
        self._replace_with_new_cells(['Comment']+self.as_list())

    def uncomment(self):
        pass

    def contains_keyword(self, name):
        return False

    def add_step(self, step):
        self._get_raw_steps().append(step)

    def _recreate(self, cells, comment=None):
        if not self._represent_valid_for_loop_header(cells):
            self._replace_with_new_cells(cells)
        else:
            steps = self._get_raw_steps()
            self._step.__init__(cells[1:])
            self._set_raw_steps(steps)

    def remove(self):
        steps = self.parent.data.steps
        index = steps.index(self._step)
        steps.remove(self._step)
        self.parent.data.steps = steps[:index] + self._get_raw_steps() + steps[index:]
        self._step.steps = []

    def _represent_valid_for_loop_header(self, cells):
        if cells[0] != self.as_list()[0]:
            return False
        in_token_index = len(self.vars)+1
        if cells[in_token_index] != self.as_list()[in_token_index]:
            return False
        return True

    def _replace_with_new_cells(self, cells):
        index = self.parent.index_of_step(self._step)
        self.parent.replace_step(index, Step(cells))
        self._get_raw_steps().reverse()
        for substep in self.steps:
            self.parent.add_step(index+1, Step(substep.as_list()))

    def notify_steps_changed(self):
        self.notify_value_changed()


class IntendedStepController(StepController):

    @property
    def _keyword_column(self):
        return 1

    def as_list(self):
        return ['']+self._step.as_list()

    def _get_cell_type(self, col):
        if col == 0:
            return CellType.MANDATORY_EMPTY
        return StepController._get_cell_type(self, col-1)

    def _get_content_type(self, col):
        if col == 0:
            return ContentType.EMPTY
        return StepController._get_content_type(self, col)

    def comment(self):
        self._step.__init__(['Comment'] + self._step.as_list())

    def uncomment(self):
        if self._step.keyword == 'Comment':
            self._step.__init__(self._step.as_list()[1:])

    def _recreate(self, cells, comment=None):
        if cells[0] == '':
            cells = cells[1:]
            self._step.__init__(cells)
            if self._step not in self.parent._get_raw_steps():
                self.parent.add_step(self._step)
        else:
            index = self.parent._get_raw_steps().index(self._step)
            index_of_parent = self.parent.parent.index_of_step(self.parent._step)
            self.parent._replace_with_new_cells(self.parent.as_list())
            self.parent.parent.replace_step(index+index_of_parent+1, Step(cells))

    def remove(self):
        self.parent._get_raw_steps().remove(self._step)
