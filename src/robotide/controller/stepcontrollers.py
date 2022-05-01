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

import re

from .. import robotapi, utils
from .basecontroller import _BaseController
from .cellinfo import (CellPosition, CellType, CellInfo, CellContent, ContentType)
from ..namespace.local_namespace import LocalNamespace
from ..utils import variablematcher


class StepController(_BaseController):

    _GIVEN_WHEN_THEN_MATCHER = re.compile(r'^(given|when|then|and|but)\s*',
                                          re.I)

    def __init__(self, parent, step):
        self._init(parent, step)
        self._step.args = self._change_last_empty_to_empty_var(
            self._step.args, self._step.comment)

    def _init(self, parent, step):
        self.parent = parent
        self._step = step
        self.indent = []
        # print(f"DEBUG: StepController init self._step.name: {self._step.name if self._step.name else None }")
        # self._cell_info_cache = {}

    @property
    def display_name(self):
        return 'Step'

    @property
    def datafile_controller(self):
        return self.parent.datafile_controller

    def _change_last_empty_to_empty_var(self, args, comment):
        if not args and not comment:
            return []
        if comment:
            print(f"DEBUG: Stepcontroller _change_last_empty_to_empty_var comment block values: {args}  {comment.as_list()}")  # {args[0]}")
            return args + comment.as_list()
        # print(f"DEBUG: Stepcontroller _change_last_empty_to_empty_var ")  #{args[0]}")
        # DEBUG no longer return var
        return args[:-1] + ['${EMPTY}'] if args and args[-1] == '' else args
        # DEBUG use revert old code return args[:-1] + [''] if args and args[-1] == '' else args

    def get_keyword_info(self, kw):
        if not kw:
            return None
        return self.parent.get_keyword_info(kw)

    def __eq__(self, other):
        if self is other:
            return True
        return self._steps_are_equal(self._step, other._step)

    def _steps_are_equal(self, fst, snd):
        if fst is snd:
            return True
        if not snd:
            return False
        return (fst.assign == snd.assign and
                fst.name == snd.name and
                fst.args == snd.args)

    def get_value(self, col):
        values = self.as_list()
        if len(values) <= col:
            return ''
        return values[col]

    """    
    def get_cell_info(self, col):
        if col not in self._cell_info_cache:
            position = self._get_cell_position(col)
            print(f"DEBUG: Stepcontroller get_cell_info position({col}) {position.type} {position.argument_name}")
            content = self._get_content_with_type(col, position)
            self._cell_info_cache[col] = self._build_cell_info(content, position)
        else:
            print(f"DEBUG: Stepcontroller get_cell_info position({col}) IN CACHE *******")
        return self._cell_info_cache[col]
    """

    def get_cell_info(self, col):
        # print(f"DEBUG: Stepcontroller ENTER get_cell_info position({col}) {'W'*col if col == 2 else ''}")
        position = self._get_cell_position(col)
        # print(f"DEBUG: Stepcontroller get_cell_info position({col}) {position.type} {position.argument_name}")
        content = self._get_content_with_type(col, position)
        # print(f"DEBUG: Stepcontroller get_cell_info position({col}) content.type={content.type} value={content.value}")
        return self._build_cell_info(content, position)

    @property
    def assignments(self):
        return self._step.assign

    def is_assigning(self, value):
        for assignment in self.assignments:
            if assignment.replace('=', '').strip() == \
                    value.replace('=', '').strip():
                return True
        return False

    def _build_cell_info(self, content, position):
        return CellInfo(content, position)

    def _get_cell_position(self, column):
        # TODO: refactor
        ########## print(f"DEBUG: Stepcontroller Enter _get_cell_position {column} keyword_column={self._keyword_column}")
        if self.parent.has_template():
            return CellPosition(CellType.UNKNOWN, None)
        column -= len(self._step.assign)
        # print(f"DEBUG: Stepcontroller _get_cell_position not in template processing {column}"
        #       f" current keyword_column={self._keyword_column} step name: {self._step.name}")
        if column < 0:
            return CellPosition(CellType.ASSIGN, None)
        info = self.get_keyword_info(self._step.name)
        # if info:
            # print(f"DEBUG: Stepcontroller _get_cell_position info {info.name if info else None} info.args {info.arguments}")
        if not info:
            return CellPosition(CellType.UNKNOWN, None)
        if column == self._keyword_column:
            # print(f"DEBUG: Stepcontroller _get_cell_position return KEYWORD {column} info {info.name if info else None}")
            return CellPosition(CellType.KEYWORD, None)
        args = info.arguments
        args_amount = len(args)
        if args_amount == 0:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        if column >= args_amount and self._last_argument_is_varargs(args):
            return CellPosition(CellType.OPTIONAL, args[-1])
        if self._has_list_or_dict_var_value_before(column - 1):
            return CellPosition(CellType.UNKNOWN, None)
        if column - self._keyword_column > args_amount:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        if column - self._keyword_column <= self._number_of_mandatory_arguments(args, args_amount):
            return CellPosition(CellType.MANDATORY, args[column-self._keyword_column - 1])
        return CellPosition(CellType.OPTIONAL, args[-1])

    def _number_of_mandatory_arguments(self, args, args_amount):
        defaults = [arg for arg in args if '=' in arg]
        n = args_amount - len(defaults)
        if self._last_argument_is_varargs(args):
            n -= 1
        # print(f"DEBUG: Stepcontroller _number_of_mandatory_arguments=={n} args_amount={args_amount} defaults={len(defaults)}")
        return n

    def _last_argument_is_varargs(self, args):
        return args[-1].startswith('*')

    def _has_list_or_dict_var_value_before(self, arg_index):
        if self.args:
            for idx, value in enumerate(self.args):
                if idx > arg_index:
                    return False
                if variablematcher.is_list_variable(value) and \
                   not variablematcher.is_list_variable_subitem(value):
                    return True
                if robotapi.is_dict_var(value) and \
                   not variablematcher.is_dict_var_access(value):
                    return True
        return False

    def _get_content_with_type(self, col, position):
        value = self.get_value(col)
        # print(f"DEBUG: Stepcontroller _get_content_with_type col {col} value {value}")
        if self._is_commented(col):
            # print(f"DEBUG: Stepcontroller _get_content_with_type _is_commented True")
            return CellContent(ContentType.COMMENTED, value)
        last_none_empty = self._get_last_none_empty_col_idx()
        if isinstance(last_none_empty, int) and last_none_empty < col:
            return CellContent(ContentType.EMPTY, value)
        if variablematcher.is_variable(value):
            if self._is_unknow_variable(value, position):
                return CellContent(ContentType.UNKNOWN_VARIABLE, value)
            return CellContent(ContentType.VARIABLE, value)
        if self.is_user_keyword(value):
            return CellContent(
                ContentType.USER_KEYWORD, value,
                self.get_keyword_info(value).source)
        if self.is_library_keyword(value):
            return CellContent(
                ContentType.LIBRARY_KEYWORD, value,
                self.get_keyword_info(value).source)
        if value == 'END':  # DEBUG Don't consider start column (col == 0 and)
            return CellContent(ContentType.END, value)
        return CellContent(ContentType.STRING, value)

    def _is_unknow_variable(self, value, position):
        if position.type == CellType.ASSIGN:
            return False
        is_known = self._get_local_namespace().has_name(value)
        if is_known:
            return False
        inner_value = value[2:-1]
        modified = re.split(r'\W', inner_value, 1)[0]
        # print(f"\nDEBUG: Stepcontrollers value: {value} inner_value: {inner_value} modified: {modified}")
        return not self._get_local_namespace().has_name(
            '%s{%s}' % (value[0], modified))

    def _get_local_namespace(self):
        index = self.parent.index_of_step(self._step)
        return LocalNamespace(
            self.parent, self.datafile_controller._namespace, index)

    def _get_last_none_empty_col_idx(self):
        values = self.as_list()
        for i in reversed(range(len(values))):
            if values[i].strip() != '':
                return i
        return None

    def is_modifiable(self):
        return self.datafile_controller.is_modifiable()

    def is_user_keyword(self, value):
        return self.parent.is_user_keyword(value)

    def is_library_keyword(self, value):
        return self.parent.is_library_keyword(value)

    def as_list(self):
        # print(f"\nDEBUG: Stepcontrollers enter as_list")
        return self._step.as_list()

    def contains_variable(self, name):
        return any(variablematcher.value_contains_variable(item, name)
                   for item in self.as_list())

    def contains_variable_assignment(self, name):
        return any(variablematcher.value_contains_variable(item, "%s=" % name)
                   for item in self.as_list())

    def contains_keyword(self, name):
        return any(self._kw_name_match(item, name)
                   for item in [self.keyword or ''] + self.args)

    def _kw_name_match(self, item, expected):
        if isinstance(expected, str):
            return utils.eq(item, expected) or (
                self._GIVEN_WHEN_THEN_MATCHER.match(item) and
                utils.eq(
                    self._GIVEN_WHEN_THEN_MATCHER.sub('', item), expected))
        return expected.match(item)

    def replace_keyword(self, new_name, old_name):
        if self._kw_name_match(self.keyword or '', old_name):
            self._step.name = self._kw_name_replace(
                self.keyword, new_name, old_name)
        for index, value in enumerate(self.args):
            if self._kw_name_match(value, old_name):
                self._step.args[index] = self._kw_name_replace(
                    value, new_name, old_name)

    def _kw_name_replace(self, old_value, new_match, old_match):
        old_prefix_matcher = self._GIVEN_WHEN_THEN_MATCHER.match(old_value)
        if not old_prefix_matcher:
            return new_match
        old_prefix = old_prefix_matcher.group(0)
        old_match_matcher = self._GIVEN_WHEN_THEN_MATCHER.match(old_match)
        if old_match_matcher and old_match_matcher.group(0) == old_prefix:
            return new_match
        return old_prefix + new_match

    @property
    def datafile(self):
        return self.parent.datafile

    @property
    def keyword(self):
        return self._step.name

    @property
    def assign(self):
        return self._step.assign

    @property
    def args(self):
        return self._step.args

    @property
    def vars(self):
        return self._step.vars

    def change(self, col, new_value):
        cells = self.as_list()
        print(f"DEBUG: enter change at StepController: {cells}\n col: {col} new_value: {new_value}")
        if col >= len(cells):
            cells = cells + ['' for _ in range(col - len(cells) + 1)]
        cells[col] = new_value
        comment = self._get_comment(cells)
        print(f"DEBUG: change at StepController: comment: {comment} \ncells before recreate {cells[:]} ")
        if comment:
            cells.pop()
        self._recreate(cells, comment)

    def insert_value_before(self, col, new_value):
        self.shift_right(col)
        self.change(col, new_value)

    def comment(self):
        #print(f"DEBUG: enter comment at StepController: {self._step.as_list()} kwcolumn={self._keyword_column}")
        # comment_pos = self._keyword_column  # Because it changes after shift_right
        #self.shift_right(0)
        # print(f"DEBUG: after shift_right comment at StepController: {self._step.as_list()} kwcolumn={self._keyword_column}")
        # self.change(0, 'Comment')
        self.insert_value_before(0, 'Comment')

    def _is_commented(self, col):
        # print(f"DEBUG: Stepcontroller enter _is_commented col {col}")
        if self._has_comment_keyword():
            return col > self._keyword_column
        for i in range(min(col + 1, len(self.as_list()))):
            if self.get_value(i).startswith('# '):
                return True
        return False

    def _first_non_empty_cell(self):
        print(f"DEBUG: Stepcontroller enter _first_non_empty_cell")
        cells = self.as_list()
        if cells:
            print(f"DEBUG: Stepcontroller _first_non_empty_cell: {cells}")
        index = 0
        while index < len(cells) and cells[index] == '':
            index += 1
        # print(f"DEBUG: model _first_non_empty_cell returning index={index}")
        return index

    @property
    def _keyword_column(self):
        return self._step.inner_kw_pos  # ._first_non_empty_cell()

    def recalculate_keyword_column(self):
        self._step.inner_kw_pos = self._first_non_empty_cell()

    def _has_comment_keyword(self):
        # print(f"DEBUG: Stepcontroller enter _has_comment_keyword keyword {self.keyword}")
        if self.keyword is None:
            return False
        return self.keyword.strip().lower() == "comment"

    def uncomment(self):
        print(f"DEBUG: StepController Enter uncomment: {self._step.as_list()}")
        if self._step.name == 'Comment':
            self.shift_left(0)

    def shift_right(self, from_column):
        # print(f"DEBUG: StepController shift_right enter:index:{from_column}")
        cells = self.as_list()
        comment = self._get_comment(cells)
        # print(f"DEBUG: StepController shift_right enter:index:{from_column} {cells} {comment}")
        if len(cells) > from_column:
            if comment:
                cells.pop()
            cells = cells[:from_column] + [''] + cells[from_column:]
            print(f"DEBUG: StepController shift_right before recreate: {cells}")  # {comment}")
            # DEBUG include comment
            self._recreate(cells, comment)

    def shift_left(self, from_column):
        cells = self.as_list()
        comment = self._get_comment(cells)
        if len(cells) > from_column:
            if comment:
                # print(f"DEBUG: StepController shift_left removing comment: {comment}")
                cells.pop()
            cells = cells[:from_column] + cells[from_column + 1:]
            self._recreate(cells, comment)

    @staticmethod
    def first_non_empty_cell(cells):
        index = 0
        while index < len(cells) and cells[index] == '':
            index += 1
        return index

    def insert_before(self, new_step):
        # print(f"DEBUG: StepController Enter insert_before")
        steps = self.parent.get_raw_steps()
        index = steps.index(self._step)
        print(f"DEBUG: StepController insert_before index={index}")  #  new {new_step.as_list()}"
        #      f"step {self._step.as_list()} indexed={steps[index].as_list()}")
        if not new_step or not new_step.as_list():
            new_step = robotapi.Step([''])
        """
        if self._is_end_step(new_step.as_list()):
            if self._is_intended_step(steps[index].as_list()):
                if self.parent.step(index).as_list()[0] == '':
                    self.parent.step(index).shift_left(0)  # DEBUG Hard coded!
                steps = self.parent.get_raw_steps()
        el
        """
        if index > 0:
            upper_indent = self.first_non_empty_cell(steps[index-1].as_list())
            current_indent = self.first_non_empty_cell(new_step.as_list())
            delta_indent = upper_indent - current_indent
            # if index > 0 and self._is_intended_step(self.parent.step(index-1).as_list()):
            print(f"DEBUG: StepController insert_before calculate identation prev_step={steps[index-1].as_list()} "
                  f"delta_indent={delta_indent} upper_indent={upper_indent} current_indent={current_indent}")
            if delta_indent > 0:
                e_list = []
                for _ in range(1, delta_indent):
                    e_list.append('')
                new_step = robotapi.Step(e_list + new_step.as_list(indent=True))
            elif delta_indent < 0 and len(new_step.as_list()) > 1:
                for _ in range(delta_indent, 0):
                    if new_step.as_list()[0] == '':
                        print(f"DEBUG: insert_before shift left")
                        new_step = robotapi.Step(new_step.as_list(indent=True)[1:])
            elif delta_indent == 0 and len(steps[index-1].as_list()) > upper_indent:  # and
                print(f"DEBUG: insert_before index-1={index-1} upper_indent={upper_indent} step={steps[index - 1].as_list()}")
                if steps[index-1].as_list()[upper_indent-1] == 'END':
                    new_step = robotapi.Step([''] + new_step.as_list(indent=True))
            self.parent.set_raw_steps(steps[:index] + [new_step] + steps[index:])
        else:
            new_step = robotapi.Step(new_step.as_list(indent=False))
            print(f"DEBUG: insert_before index={index} new_step: {new_step.as_list()}")
            self.parent.set_raw_steps([new_step] + steps[index:])

    def insert_after(self, new_step):
        steps = self.parent.get_raw_steps()
        index = steps.index(self._step) + 1
        print(f"DEBUG: insert_after index={index} new_step: {new_step.as_list()}"
              f"step {self._step.as_list()} indexed-1={steps[index-1].as_list()}")
        if not self._is_end_step(new_step.as_list()):
            if self._is_intended_step(steps[index-1].as_list()):
                if not self._is_intended_step(new_step.as_list()):
                    new_step.shift_right(0)  # DEBUG Hard coded!
            else:
                if self._is_intended_step(new_step.as_list()) and isinstance(new_step, StepController):
                    # print(f"DEBUG: insert_after shitfing_left new_step: {new_step.as_list()}")
                    new_step.shift_left(1)  # DEBUG Hard coded!
        self.parent.set_raw_steps(steps[:index] + [new_step] + steps[index:])

    def remove_empty_columns_from_end(self):
        cells = self.as_list()
        while cells != [] and cells[-1].strip() == '':
            cells.pop()
        self._recreate(cells)

    def remove_empty_columns_from_beginning(self):
        cells = self._step.as_list()
        print(f"DEBUG: remove_empty_columns_from_beginning {cells[:]} \nIndex first non-empty={self._keyword_column}")
        if cells != [] and cells[0].strip() == '':
            cells = cells[1:]
        self._recreate(cells)

    def remove(self):
        self.parent.data.steps.remove(self._step)
        self.parent._clear_cached_steps()

    def move_up(self):
        print(f"DEBUG: StepController ENTER move_up")
        previous_step = self.parent.step(self._index() - 1)
        self.remove()
        previous_step.insert_before(self._step)

    def move_down(self):
        next_step = self.parent.step(self._index() + 1)
        self.remove()
        next_step.insert_after(self._step)

    def _index(self):
        return self.parent.index_of_step(self._step)

    def has_only_comment(self):
        non_empty_cells = [cell for cell
                           in self._step.as_list() if cell.strip() != '']
        return len(non_empty_cells) == 1 and \
            non_empty_cells[0].startswith('#')

    def _get_comment(self, cells):
        if not cells:
            return None
        return cells[-1][2:].strip() if cells[-1].startswith('# ') else None

    def _recreate(self, cells, comment=None):
        print(f"DEBUG: enter _recreate: {cells} self.step={self._step.as_list()}")
        """
        if self._is_partial_for_loop_step(cells):
            print(f"DEBUG: _recreate _recreate_as_partial_for_loop before: {cells}")
            self._recreate_as_partial_for_loop(cells, comment)
            # print(f"DEBUG: _recreate _recreate_as_partial_for_loop after: {cells}")
        
        elif self._is_intended_step(cells):
            i = self._index()
            previous_step = self.parent.step(i - 1)
            print(f"DEBUG: _recreate _is_intended_step: {previous_step.as_list()}")
            if type(previous_step) == ForLoopStepController:
                # print(f"DEBUG: _recreate _is_intended_step FOR loop: {previous_step.as_list()}")
                self._recreate_as_intended_step(previous_step, cells, comment, i)
                # print(f"DEBUG: _recreate _is_intended_step after: {previous_step.as_list()}")
            elif type(previous_step) == IntendedStepController:
                print(f"DEBUG: _recreate _is_intended_step before: {previous_step.as_list()}")
                self._recreate_as_intended_step(previous_step.parent, cells, comment, i)
            else:
                print(f"DEBUG: _recreate Indented Step init before: {cells} comment {comment}")
                self._step.__init__(cells, comment)
                self.recalculate_keyword_column()
                return
        """
        print(f"DEBUG: _recreate init before: {cells} comment {comment}")
        # self._step.__init__(cells, comment)
        # i = self._index()
        # previous_step = self.parent.step(i - 1)
        # self.remove()
        self._step.__init__(cells, comment)
        # self.insert_before(robotapi.Step(cells, comment))
        # self.remove()
        # self._init(previous_step, robotapi.Step(cells, comment))
        print(f"DEBUG: _recreate init after before recalculate: {self._step.as_list()}")
        self.recalculate_keyword_column()
        print(f"DEBUG: _recreate init after recalculate: {self._step.as_list()}")

    def _is_partial_for_loop_step(self, cells):
        print(f"DEBUG: _is_partial_for_loop_step : {cells} index={self._keyword_column}")
        return cells and (cells[self._keyword_column].replace(' ', '').upper() == ':FOR'
                          or cells[self._keyword_column] == 'FOR')

    def _is_intended_step(self, cells):
        print(f"DEBUG: _is_intended_step cells {cells}")
        return cells and not cells[0].strip() and any(c.strip() for c in cells) and self._index() > 0

    def _is_end_step(self, cells):
        return cells and ('END' in cells)  # cells[0] == 'END' # TODO Improve check

    def _recreate_as_partial_for_loop(self, cells, comment):
        index = self._index()
        print(f"\nDEBUG: Stepcontrollers _recreate_as_partial_for_loop : cells[0]: {cells[0]}"
              f" cells[1:]: {cells[1:] if len(cells)>1 else ['']}")
        self.parent.replace_step(index, PartialForLoop(
            cells[1:] if len(cells)>1 else [''], first_cell=cells[0], comment=comment))
        self._recreate_next_step(index)

    def _recreate_as_intended_step(self, for_loop_step, cells, comment, index):
        self.remove()
        print(f"\nDEBUG: Stepcontrollers _recreate_as_intended_step : add indent {cells[:]}")
        for_loop_step.add_step(robotapi.Step(cells[:], comment))
        self._recreate_next_step(index)

    def _recreate_next_step(self, index):
        if len(self.parent.steps) > index + 1:
                next_step = self.parent.step(index + 1)
                print(f"\nDEBUG: Stepcontrollers _recreate_next_step : add indent {next_step.as_list()}")
                next_step._recreate(next_step.as_list())

    def notify_value_changed(self):
        self.parent.notify_steps_changed()


class PartialForLoop(robotapi.ForLoop):

    parent = None

    def __init__(self, cells, first_cell='FOR', comment=None):
        self._cells = cells
        self._first_cell = first_cell
        robotapi.ForLoop.__init__(self, self.parent, cells, comment)

    def as_list(self, indent=False, include_comment=False):
        print(f"\nDEBUG: PartialForLoop enter as_list")
        return [self._first_cell] + self._cells + self.comment.as_list()


class ForLoopStepController(StepController):

    def __init__(self, parent, step):
        StepController.__init__(self, parent, step)
        self.inner_kw_pos = self._first_non_empty_cell()
        # self.indent = []

    @property
    def name(self):
        return self.parent.name

    @property
    def assignments(self):
        return self._step.vars

    @property
    def _keyword_column(self):
        return self.inner_kw_pos

    def move_up(self):
        print(f"DEBUG: ForLoopStepController ENTER move_up")
        previous_step = self.parent.step(self._index() - 1)
        if isinstance(previous_step, ForLoopStepController):
            self._swap_forloop_headers(previous_step)
        else:
            print(f"DEBUG: ForLoopStepController move_up insert INDENT ")
            self.get_raw_steps().insert(0, previous_step._step)
            previous_step.remove()

    def _swap_forloop_headers(self, previous_step):
        previous_step._step.steps = self._step.steps
        self._step.steps = []
        steps = self.parent.get_raw_steps()
        i = steps.index(self._step)
        steps[i - 1] = self._step
        steps[i] = previous_step._step
        self.parent.set_raw_steps(steps)

    def move_down(self):
        next_step = self.step(self._index() + 1)
        next_step.move_up()
        if len(self._step.steps) == 0:
            print(f"DEBUG: ForLoopStepController move_down calling _recreate_complete_for_loop_header")
            self._recreate_complete_for_loop_header(cells=self.as_list())

    def insert_after(self, new_step):
        self.get_raw_steps().insert(0, new_step)

    def step(self, index):
        return self.parent.step(index)

    def _has_comment_keyword(self):
        return False

    def get_raw_steps(self):
        return self._step.steps

    def set_raw_steps(self, steps):
        self._step.steps = steps

    def _get_cell_position(self, col):
        # print(f"DEBUG: enter _get_cell_position at ForLoopStepController: col={col}")
        until_range = len(self._step.vars) + 1
        flavor = self._step.flavor
        if col == 0:
            return CellPosition(CellType.MANDATORY, None)
        if col < until_range:
            return CellPosition(CellType.ASSIGN, None)
        if col == until_range:
            return CellPosition(CellType.MANDATORY, None)
        if 'RANGE' not in flavor:
            return CellPosition(CellType.OPTIONAL, None)
        if col <= until_range + 1:
            return CellPosition(CellType.MANDATORY, None)
        if col <= until_range + 3:
            return CellPosition(CellType.OPTIONAL, None)
        return CellPosition(CellType.MUST_BE_EMPTY, None)

    def _build_cell_info(self, content, position):
        return CellInfo(content, position, for_loop=True)

    @property
    def steps(self):
        return [IntendedStepController(self, sub_step)
                for sub_step in self.get_raw_steps()]

    def index_of_step(self, step):
        print(f"DEBUG: ForLoopStepController ENTER index_of_step")
        print(f"DEBUG: ForLoopStepController step={step} steps={self.as_list()}")
        index_in_for_loop = self.get_raw_steps().index(step)
        return self._index() + index_in_for_loop + 1

    def _get_comment(self, cells):
        return None

    def comment(self):
        print(f"DEBUG: enter comment ForLoopStepController: self {self.as_list()}")
        print(f"DEBUG: comment ForLoopStepController: keyword_column {self._keyword_column}")
        # kw_column = self._keyword_column
        # self.shift_right(0)
        # self.change(0, 'Comment')
        self._replace_with_new_cells(['Comment'] + self.as_list())

    def uncomment(self):
        print(f"DEBUG: enter uncomment ForLoopStepController: self {self.as_list()}")
        if self.as_list()[self._keyword_column] == 'Comment':
            kw_column = self._keyword_column
            self.shift_right(kw_column)
            self.change(kw_column, '')
            self.shift_left(self._keyword_column)

    def contains_keyword(self, name):
        return False

    def add_step(self, step):
        self.get_raw_steps().append(step)

    def _recreate(self, cells, comment=None):
        print(f"DEBUG: enter _recreate ForLoopStepController: {cells}")
        print(f"DEBUG: enter _recreate ForLoopStepController initial = {cells[0]}")
        if cells[self._step.inner_kw_pos] != 'FOR':
            new_cells = cells[0:]
            index = self._index()
            self.parent.replace_step(index, robotapi.Step(new_cells, comment))
            return
        else:
            self._step.__init__(self.parent, cells[self._step.inner_kw_pos:])
        self.recalculate_keyword_column()
        # if not self._represent_valid_for_loop_header(cells):
        #     self._recreate_partial_for_loop_header(cells, comment)
        #else:
        #
        # DEBUG: Do nothing :)
        # self._recreate_complete_for_loop_header(cells)

    def _recreate_complete_for_loop_header(self, cells):
        # print(f"DEBUG: enter _recreate_complete_for_loop_header ForLoopStepController: {cells}")
        # steps = self.get_raw_steps()
        self._step.__init__(self.parent, cells[:])
        # self.set_raw_steps(steps)

    def _recreate_partial_for_loop_header(self, cells, comment):
        # print(f"DEBUG: enter _recreate_partial_for_loop_header ForLoopStepController: {cells}")
        if not cells or (cells[self._keyword_column].replace(' ', '').upper() != ':FOR'
                         and cells[self._keyword_column].replace(' ', '') != 'FOR'):
            self._replace_with_new_cells(cells)
        else:
            steps = self.get_raw_steps()
            i = self._index()
            StepController._recreate_as_partial_for_loop(self, cells, comment)
            self.parent.step(i).set_raw_steps(steps)

    def remove(self):
        steps = self.parent.data.steps
        index = steps.index(self._step)
        steps.remove(self._step)
        self.parent.data.steps = \
            steps[:index] + self.get_raw_steps() + steps[index:]
        self._step.steps = []

    def _represent_valid_for_loop_header(self, cells):
        if not cells:
            return False
        if cells[0] != self.as_list()[0]:
            return False
        in_token_index = len(self.vars) + 1
        if len(cells) <= in_token_index:
            return False
        if len(self.as_list()) <= in_token_index:
            return False
        if cells[in_token_index] != self.as_list()[in_token_index]:
            return False
        return True

    def _replace_with_new_cells(self, cells):
        index = self.parent.index_of_step(self._step)
        self.parent.replace_step(index, robotapi.Step(cells))
        self.get_raw_steps().reverse()
        for substep in self.steps:
            self.parent.add_step(index + 1, robotapi.Step(substep.as_list()))

    def notify_steps_changed(self):
        self.notify_value_changed()

    def has_template(self):
        return self.parent.has_template()


class IntendedStepController(StepController):

    _invalid = False

    def _first_non_empty_cell(self):
        cells = self.as_list()
        # print(f"DEBUG: IntendedStepController enter _first_non_empty_cell cells={cells}")
        index = 0
        while index < len(cells) and cells[index] == '':
            index += 1
        return index

    @property
    def _keyword_column(self):
        return self._first_non_empty_cell()

    def as_list(self):
        row = self._step.as_list()
        # print(f"\nDEBUG: IntendedStepController enter as_list {row[:]}")
        if not row:
            return []
        if row[0] != '':
            return ['', ''] + row
        return [''] + row  # DEBUG removed [''] +

    def _get_cell_position(self, col):
        # print(f"DEBUG: enter _get_cell_position at IntendedStepController: col={col}")
        if col < self._keyword_column:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        return StepController._get_cell_position(self, col)

    def _get_local_namespace(self):
        p = self.parent.parent
        index = p.index_of_step(self._step)
        return LocalNamespace(p, self.datafile_controller._namespace, index)

    def _get_content_with_type(self, col, position):
        if col < self._keyword_column:
            return CellContent(ContentType.EMPTY, None)
        return StepController._get_content_with_type(self, col, position)

    def comment(self):
        print(f"DEBUG: enter comment IntendedStepController: self {self.as_list()}")
        # comment_pos = self._keyword_column
        self.shift_right(0)
        self.change(0, 'Comment')
        # self._step.__init__(['Comment'] + self._step.as_list())

    def uncomment(self):
        print(f"DEBUG: enter uncomment IntendedStepController: self {self.as_list()}")
        if self._step.name == 'Comment':
            kw_column = self._keyword_column
            self.shift_right(kw_column)
            self.change(kw_column, '')
            self.shift_left(self._keyword_column)
            # self._step.__init__(self._step.as_list()[1:])

    def _recreate(self, cells, comment=None):
        # TODO refactor
        print(f"DEBUG: enter _recreate IntendedStepController: {cells[:]} self {self._step.as_list(indent=True)}")
        if cells == [] or cells[0] == '':
            for idx in range(0, len(cells)):
                if cells[idx] != '':
                    break
            print(f"DEBUG: enter _recreate IntendedStepController init INDENTED kw_column {idx} ")
            self._step.__init__(cells[idx:], comment=comment)  # self._keyword_column
            if self._step not in self.parent.get_raw_steps():
                self.parent.add_step(self._step)
        else:
            print(f"DEBUG: enter _recreate IntendedStepController init NORMAL STEP")
            self._step.__init__(cells[:], comment=comment)
            if self._step not in self.parent.get_raw_steps():
                self.parent.add_step(self._step)
            self._recreate_as_normal_step(cells, comment)
            ## self._invalid = True

    def _recreate_as_normal_step(self, cells, comment=None):
        steps = self.parent.steps
        index = [s._step for s in steps].index(self._step)
        for i, step in reversed(list(enumerate(steps))):
            if i == index:
                break
            step._replace_with_normal_step(i, step.as_list())
        self._replace_with_normal_step(index, cells, comment)

    def _replace_with_normal_step(self, index, cells=None, comment=None):
        index_of_parent = self.parent.parent.index_of_step(self.parent._step)
        print(f"DEBUG: enter _recreate _replace_with_normal_step: {cells}, index={index} "
              f"index_of_parent={index_of_parent}\nadd_step to index={index_of_parent + index + 2}")
        self.parent.parent.add_step(
            index_of_parent + index + 2,
            robotapi.Step(cells or self.as_list(), comment=comment))
        self.parent.get_raw_steps().pop(index)

    def remove(self):
        self.parent.get_raw_steps().remove(self._step)

    # @utils.overrides(StepController)
    def remove_empty_columns_from_end(self):
        if self._invalid:
            return
        StepController.remove_empty_columns_from_end(self)
