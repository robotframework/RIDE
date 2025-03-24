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
from .cellinfo import CellPosition, CellType, CellInfo, CellContent, ContentType, UPPERCASE_KWS
from ..publish.messages import RideItemNameChanged
from ..namespace.local_namespace import local_namespace
from ..utils import variablematcher

BDD_ENGLISH = 'given|when|then|and|but'

def obtain_bdd_prefixes(language):
    from robotide.lib.compat.parsing.language import Language
    lang = Language.from_name(language[0] if isinstance(language, list) else language)
    bdd_prefixes = [f"{x}|" for x in lang.bdd_prefixes]
    bdd_prefixes = "".join(bdd_prefixes).strip('|')
    return bdd_prefixes


class StepController(_BaseController):

    indent = None

    def __init__(self, parent, step):
        self.continuing_kw = None
        self._init(parent, step)
        if hasattr(self.parent, 'language'):
            self._language = self.parent.language[0] if isinstance(self.parent.language, list) else self.parent.language
        else:
            self._language = 'en'
        if self._language and self._language.lower() not in ['en', 'english']:
            bdd_prefix = f"{obtain_bdd_prefixes(self._language)}|{BDD_ENGLISH}"
        else:
            bdd_prefix = BDD_ENGLISH
        self._GIVEN_WHEN_THEN_MATCHER = re.compile(fr'^({bdd_prefix})\s*', re.IGNORECASE)
        # print(f"DEBUG: stepcontrollers.py StepController INIT {self.parent.language}")
        self.step_controller_step.args = self._change_last_empty_to_empty_var(
            self.step_controller_step.args, self.step_controller_step.comment)

    def _init(self, parent, step):
        self.parent = parent
        self.step_controller_step = step
        self.indent = []
        index = 0
        if isinstance(self.step_controller_step, list):
            while index < len(self.step_controller_step) and self.step_controller_step[index] == '':
                self.indent.append('')
        elif isinstance(self.step_controller_step, robotapi.Step):
            cells = self.step_controller_step.as_list()
            for index in range(0, len(cells)):
                if cells[index] == '':
                    self.increase_indent()
        else:
            self.step_controller_step.args = self.step_controller_step.comment = []

    @property
    def display_name(self):
        return 'Step'

    @property
    def datafile_controller(self):
        return self.parent.datafile_controller

    @staticmethod
    def _change_last_empty_to_empty_var(args, comment):
        if not args:  # and not comment:
            return []
        if comment:
            return args
        return args[:-1] + ['${EMPTY}'] if args[-1] == '' else args

    def get_keyword_info(self, kw):
        if not kw:
            return None
        return self.parent.get_keyword_info(kw)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, StepController):
            return False
        return self._steps_are_equal(self.step_controller_step, other.step_controller_step)

    @staticmethod
    def _steps_are_equal(fst, snd):
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

    def get_cell_info(self, col):
        position = self._get_cell_position(col)
        content = self._get_content_with_type(col, position)
        if content.type == ContentType.COMMENTED:
            return self._build_cell_info(content, CellPosition(CellType.OPTIONAL, None))
        return self._build_cell_info(content, position)

    @property
    def assignments(self):
        return self.step_controller_step.assign

    def is_assigning(self, value):
        for assignment in self.assignments:
            if assignment.replace('=', '').strip() == value.replace('=', '').strip():
                return True
        if value.strip().endswith('='):
            return True
        return False

    def _build_cell_info(self, content, position):
        return CellInfo(content, position)

    def _get_cell_position(self, column):
        col = column
        if self.parent.has_template():
            return CellPosition(CellType.UNKNOWN, None)
        column -= len(self.step_controller_step.assign)
        value_at_col = self.get_value(col)
        info = self.get_keyword_info(value_at_col)  # Getting info for the keyword cell
        keyword_col = col if col >= self._keyword_column else self._keyword_column
        if info:
            casesensitive = (value_at_col.upper() != value_at_col and value_at_col.upper() in UPPERCASE_KWS)
            if casesensitive:
                return CellPosition(CellType.UNKNOWN, ContentType.STRING)
            return CellPosition(CellType.KEYWORD, None)
        else:
            while not info and keyword_col > 0 and keyword_col > self._keyword_column:
                keyword_col -= 1
                value_at_col = self.get_value(keyword_col)
                info = self.get_keyword_info(value_at_col)  # Getting info for the previous cell
            casesensitive = (value_at_col.upper() != value_at_col and value_at_col.upper() in UPPERCASE_KWS)
            if casesensitive:
                return CellPosition(CellType.UNKNOWN, None)
        if info:
            args = info.arguments
        else:
            args = []
            value_at_col = self.get_value(col)
            if self.keyword == '...' and self._index() > 0:  # Any block starting with ... is in error
                if value_at_col == '...':
                    drow = 1
                    self.continuing_kw = self.parent.step(self._index()-drow).keyword
                    while self.continuing_kw == '...' and self._index()-drow > 0:
                        drow += 1
                        self.continuing_kw = self.parent.step(self._index() - drow).keyword
                info = self.get_keyword_info(self.continuing_kw)  # Getting info for the previous step kw
                if info:
                    args = info.arguments
        args_amount = len(args)
        if (column > keyword_col and (self.get_value(keyword_col) == "FOR" or self.get_value(keyword_col) == "VAR")
                and self.is_assigning(value_at_col)):
            # print(f"DEBUG: stepcontrollers.py StepController _get_cell_position VAR or FOR assign "
            #       f"value_at_col={value_at_col}")
            return CellPosition(CellType.ASSIGN, None)
        if column <= keyword_col and self.is_assigning(value_at_col):
            return CellPosition(CellType.ASSIGN, None)
        if col < keyword_col:
            return CellPosition(CellType.UNKNOWN, None)
        if not info and not self.is_assigning(value_at_col)\
                and not self.is_assigning(self.get_value(self._keyword_column)) and col >= keyword_col:
            return CellPosition(CellType.UNKNOWN, None)
        if args_amount == 0:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        mandatory_args_amount = self._number_of_mandatory_arguments(args, args_amount)
        """
        # DEBUG: This causes @ or & cells unknown, disable for now 
        if self._has_list_or_dict_var_value_before(col - 1):
            return CellPosition(CellType.UNKNOWN, None)
        """
        if col <= keyword_col + mandatory_args_amount:
            return CellPosition(CellType.MANDATORY, args[col-keyword_col - 1])
        if col >= keyword_col + args_amount - mandatory_args_amount and self._last_argument_is_varargs(args):
            # print(f"DEBUG: stepcontrollers _get_cell_position last is vararg={args[-1]}")
            return CellPosition(CellType.OPTIONAL, args[-1])
        if keyword_col + mandatory_args_amount < col <= keyword_col + args_amount:
            return CellPosition(CellType.OPTIONAL, args[col-keyword_col-1])
        return CellPosition(CellType.MUST_BE_EMPTY, None)

    def _number_of_mandatory_arguments(self, args, args_amount):
        defaults = [arg for arg in args if '=' in arg]
        n = args_amount - len(defaults)
        # detect if @{}, named only indicator is present and decrease counter
        for arg in args:
            if arg == '@{}' or arg.startswith('*'):
                n -= 1
                break
        if self._last_argument_is_varargs(args):
            n -= 1
        return n if n >= 0 else 0

    @staticmethod
    def _last_argument_is_varargs(args):
        return args[-1].startswith('*') or args[-1].startswith('&{')

    """
    # DEBUG: This is not used anywhere
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
    """

    def _get_content_with_type(self, col, position):
        value = self.get_value(col)
        if self._is_commented(col):
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
        try:
            is_known = self._get_local_namespace().has_name(value)
        except AttributeError:
            return False
        if is_known:
            return False
        inner_value = value[2:-1]
        modified = re.split(r'\W', inner_value, 1)[0]
        return not self._get_local_namespace().has_name('%s{%s}' % (value[0], modified))

    def _get_local_namespace(self):
        index = self.parent.index_of_step(self.step_controller_step)
        return local_namespace(
            self.parent, self.datafile_controller.namespace, index)

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
        return self.step_controller_step.as_list()

    def contains_variable(self, name):
        return any(variablematcher.value_contains_variable(item, name)
                   for item in self.as_list())

    def contains_variable_assignment(self, name):
        return any(variablematcher.value_contains_variable(item, "%s=" % name)
                   for item in self.as_list())

    def contains_keyword(self, name):
        for item in [self.keyword or ''] + self.args:
            matching = self._kw_name_match(item, name)
            if matching is not None:
                return matching
        return False
        """    
        return any(self._kw_name_match(item, name)
                   for item in [self.keyword or ''] + self.args)
        """

    def _kw_name_match(self, item, expected):
        if isinstance(expected, str):
            return utils.eq(item, expected) or (self._GIVEN_WHEN_THEN_MATCHER.match(item) and
                                                utils.eq(self._GIVEN_WHEN_THEN_MATCHER.sub('', item), expected))
        matcher = expected.match(item)
        # if matcher:
        #     old_prefix = matcher.group(1)
        #     print(f"DEBUG: stepcontrollers.py StepController kw_name_match: RE expected={expected}"
        #           f" matcher={matcher} old_prefix={old_prefix}")
        return matcher

    def replace_keyword(self, new_name, old_name):
        # DEBUG: Create setters for Step.name and Step.args
        new_match = self._kw_name_match(self.keyword or '', old_name)
        if new_match:
            # print(f"DEBUG: stepcontrollers.py StepController replace_keyword: ACTUAL CHANGE old_name={old_name}"
            #       f" new_name={new_name} new_match={new_match}")
            self.step_controller_step.name = self.step_controller_step.cells[self.step_controller_step.inner_kw_pos] = \
                self._kw_name_replace(self.keyword, new_name, old_name)
        for index, value in enumerate(self.args):
            if self._kw_name_match(value, old_name):
                self.step_controller_step.args[index] = self.step_controller_step.cells[
                    self.step_controller_step.inner_kw_pos + 1 + index] = \
                    self._kw_name_replace(value, new_name, old_name)

    def _kw_name_replace(self, old_value, new_match, old_match):
        # Here we should have a match for keywords prefixed with resource name
        # print(f"DEBUG: stepcontrollers.py StepController _kw_name_replace: ENTER old_value={old_value}"
        #       f" old_match={old_match} new_match={new_match}")
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
        return self.step_controller_step.name

    @property
    def assign(self):
        return self.step_controller_step.assign

    @property
    def args(self):
        return self.step_controller_step.args

    @property
    def vars(self):
        return self.step_controller_step.vars

    def change(self, col, new_value):
        cells = self.as_list()
        if col >= len(cells):
            cells = cells + ['' for _ in range(col - len(cells) + 1)]
        cells[col] = new_value
        comment = self._get_comment(cells)
        if comment:
            cells.pop()
        self.recreate(cells, comment)

    def insert_value_before(self, col, new_value):
        self.shift_right(col)
        self.change(col, new_value)

    def comment(self):
        col = self._first_non_empty_cell()  # .step_controller_step.inner_kw_pos
        self.insert_value_before(col, 'Comment')

    def sharp_comment(self):
        col = self._first_non_empty_cell()
        self.insert_sharp_comment(col)

    def insert_sharp_comment(self, col):
        cell_value = self.get_value(col)
        new_value = "# " + cell_value
        self.change(col, new_value)

    def sharp_uncomment(self):
        col = self._first_non_empty_cell()
        self.remove_sharp_comment(col)

    def remove_sharp_comment(self, col):
        cell_value = self.get_value(col)
        if cell_value.startswith('#'):
            new_value = cell_value.lstrip('#').lstrip(' ').replace('\\ ', ' ')
        else:
            return
        self.change(col, new_value)

    def _is_commented(self, col):
        if self._has_comment_keyword():
            return col > self._keyword_column
        for i in range(min(col + 1, len(self.as_list()))):
            if self.get_value(i).startswith('#'):
                return True
        return False

    def _first_non_empty_cell(self):
        index = self.step_controller_step.first_non_empty_cell()
        return index

    @property
    def _keyword_column(self):
        return self.step_controller_step.inner_kw_pos  # ._first_non_empty_cell()

    def recalculate_keyword_column(self):
        index = self._first_non_empty_cell()
        cells = self.as_list()
        if 0 < len(cells) == index:
            self.step_controller_step.inner_kw_pos = index - 1
            return
        if index < len(cells) and cells[index] == '':
            return
        while index < len(cells) and (len(cells[index]) > 0 and cells[index][0] in ['$', '@', '&', '%']):
            index += 1
        self.step_controller_step.inner_kw_pos = index

    def _has_comment_keyword(self):
        if self.keyword is None:
            return False
        return self.keyword.strip().lower() == "comment" or self.keyword.strip().lower() == 'builtin.comment'

    def uncomment(self):
        index_of_comment = self._first_non_empty_cell()
        if self.step_controller_step.as_list()[index_of_comment].lower() == 'comment' or\
                self.step_controller_step.as_list()[index_of_comment].lower() == 'builtin.comment':
            self.shift_left(index_of_comment, True)
            self.recalculate_keyword_column()

    def shift_right(self, from_column):
        cells = self.as_list()
        comment = self._get_comment(cells)
        if len(cells) > from_column:
            if comment:
                cells.pop()
            cells = cells[:from_column] + [''] + cells[from_column:]
            self.recreate(cells, comment)

    def shift_left(self, from_column, delete=False):
        cells = self.as_list()
        while not delete and from_column > 0 and cells[from_column] != '':
            from_column -= 1
        if not delete and from_column == 0 and cells[from_column] != '':
            return
        if len(cells) > from_column:
            cells = cells[:from_column] + cells[from_column + 1:]
            self.recreate(cells)

    @staticmethod
    def first_non_empty_cell(cells):
        index = 0
        while index < len(cells) and cells[index] == '':
            index += 1
        return index

    def insert_before(self, new_step):
        steps = self.parent.get_raw_steps()
        index = steps.index(self.step_controller_step)
        if not new_step or not new_step.as_list():
            new_step = robotapi.Step([])
        if index > 0:
            upper_indent = steps[index-1].first_non_empty_cell()  # self.first_non_empty_cell(steps[index-1].as_list())
            current_indent = new_step.first_non_empty_cell()  # self.first_non_empty_cell(new_step.as_list())
            delta_indent = upper_indent - current_indent
            if delta_indent > 0:
                e_list = []
                for _ in range(1, delta_indent):
                    e_list.append('')
                new_step = robotapi.Step(e_list + new_step.as_list(indent=True))
            elif delta_indent < 0 and len(new_step.as_list()) > 1:
                for _ in range(delta_indent, 0):
                    if new_step.as_list()[0] == '':
                        new_step = robotapi.Step(new_step.as_list(indent=True)[1:])
            elif delta_indent == 0 and len(steps[index-1].as_list()) > upper_indent:
                if steps[index-1].as_list()[upper_indent-1] in ['END'] \
                        or steps[index-1].as_list()[upper_indent] in ['FOR']:
                    new_step = robotapi.Step([''] + new_step.as_list(indent=True))
            self.parent.set_raw_steps(steps[:index] + [new_step] + steps[index:])
        else:
            current_indent = len(new_step.indent)
            delta_indent = current_indent - len(self.step_controller_step.indent)
            if delta_indent > 0:
                for _ in range(0, delta_indent):
                    if new_step.as_list()[0] == '':
                        new_step = robotapi.Step(new_step.as_list(indent=False)[1:])
            else:
                new_step = robotapi.Step(new_step.as_list(indent=False))
            self.parent.set_raw_steps([new_step] + steps[index:])

    def insert_after(self, new_step):
        steps = self.parent.get_raw_steps()
        index = steps.index(self.step_controller_step) + 1
        if not self._is_end_step(new_step.as_list()):
            if self._is_intended_step(steps[index-1].as_list()):
                if not self._is_intended_step(new_step.as_list()):
                    new_step.increase_indent()  # shift_right(0)  # DEBUG Hard coded!
            else:
                if self._is_intended_step(new_step.as_list()) and isinstance(new_step, StepController):
                    new_step.decrease_indent()   # shift_left(1)  # DEBUG Hard coded!
        self.parent.set_raw_steps(steps[:index] + [new_step] + steps[index:])

    def remove_empty_columns_from_end(self):
        cells = self.as_list()
        while cells != [] and cells[-1].strip() == '':
            cells.pop()
        self.recreate(cells)

    def remove_empty_columns_from_beginning(self):
        cells = self.step_controller_step.as_list()
        if cells != [] and cells[0].strip() == '':
            cells = cells[1:]
        self.recreate(cells)

    def remove(self):
        self.parent.data.steps.remove(self.step_controller_step)
        self.parent.clear_cached_steps()

    def move_up(self):
        previous_step = self.parent.step(self._index() - 1)
        self.remove()
        previous_step.insert_before(self.step_controller_step)

    def move_down(self):
        next_step = self.parent.step(self._index() + 1)
        self.remove()
        next_step.insert_after(self.step_controller_step)

    def _index(self):
        return self.parent.index_of_step(self.step_controller_step)

    def has_only_comment(self):
        non_empty_cells = [cell for cell
                           in self.step_controller_step.as_list() if cell.strip() != '']
        return len(non_empty_cells) == 1 and \
            non_empty_cells[0].startswith('#')

    def _get_comment(self, cells):
        if not cells:
            return None
        return cells[-1].strip() if cells[-1].startswith('#') else None

    def recreate(self, cells, comment=None):
        self.step_controller_step.__init__(cells, comment)
        self.recalculate_keyword_column()

    def _is_partial_for_loop_step(self, cells):
        return cells and (cells[self._keyword_column].replace(' ', '').upper() == ':FOR'
                          or cells[self._keyword_column] == 'FOR')

    def _is_for_loop(self):
        return self.keyword == 'FOR'

    def _is_intended_step(self, cells):
        return cells and not cells[0].strip() and any(c.strip() for c in cells) and self._index() > 0

    @staticmethod
    def _is_end_step(cells):
        return cells and ('END' in cells)  # cells[0] == 'END' # DEBUG: Improve check

    def _recreate_as_intended_step(self, for_loop_step, cells, comment, index):
        self.remove()
        for_loop_step.add_step(robotapi.Step(cells[:], comment))
        self._recreate_next_step(index)

    def _recreate_next_step(self, index):
        if len(self.parent.steps) > index + 1:
            next_step = self.parent.step(index + 1)
            next_step.recreate(next_step.as_list())

    def notify_value_changed(self, old_name=None, new_name=None):
        # print(f"DEBUG: stepcontrollers.py StepController notify_value_changed: ENTER old_name={old_name}"
        #      f" parent={self.parent.name} new_name={new_name}  calling self.parent.notify_steps_changed()")
        if old_name is not None:
            RideItemNameChanged(item=self, old_name=old_name, new_name=new_name).publish()
        self.parent.notify_steps_changed(old_name)

    def increase_indent(self):
        self.indent.append('')
        return len(self.indent)

    def decrease_indent(self):
        self.indent = self.indent[:-1] if len(self.indent) > 0 else []
        return len(self.indent)

    @property
    def steps(self):
        return [IntendedStepController(self, sub_step)
                for sub_step in self.get_raw_steps()]

    def __len__(self):
        return len(self.step_controller_step)


class ForLoopStepController(StepController):

    def __init__(self, parent, step):
        StepController.__init__(self, parent, step)
        self.inner_kw_pos = self._first_non_empty_cell()

    @property
    def name(self):
        return self.parent.name

    @property
    def assignments(self):
        return self.step_controller_step.vars

    """
    @property
    def _keyword_column(self):
        return self.inner_kw_pos
    """

    def move_up(self):
        previous_step = self.parent.step(self._index() - 1)
        if isinstance(previous_step, ForLoopStepController):
            self._swap_forloop_headers(previous_step)
        else:
            self.get_raw_steps().insert(0, previous_step.step_controller_step)
            previous_step.remove()

    def _swap_forloop_headers(self, previous_step):
        previous_step.step_controller_step.steps = self.step_controller_step.steps
        self.step_controller_step.steps = []
        steps = self.parent.get_raw_steps()
        i = steps.index(self.step_controller_step)
        steps[i - 1] = self.step_controller_step
        steps[i] = previous_step.step_controller_step
        self.parent.set_raw_steps(steps)

    def move_down(self):
        next_step = self.step(self._index() + 1)
        next_step.move_up()
        if len(self.step_controller_step.steps) == 0:
            self._recreate_complete_for_loop_header(cells=self.as_list())

    def insert_after(self, new_step):
        self.get_raw_steps().insert(0, new_step)

    def step(self, index):
        return self.parent.step(index)

    def _has_comment_keyword(self):
        return False

    def get_raw_steps(self):
        return self.step_controller_step.steps

    def set_raw_steps(self, steps):
        self.step_controller_step.steps = steps

    def _get_cell_position(self, col):
        until_range = len(self.step_controller_step.vars) + 1
        flavor = self.step_controller_step.flavor
        if col == self._keyword_column:
            return CellPosition(CellType.KEYWORD, None)
        if col < self._keyword_column + until_range:
            return CellPosition(CellType.ASSIGN, self.step_controller_step.vars[:])
        if col == self._keyword_column + until_range:
            return CellPosition(CellType.MANDATORY, None)
        if 'IN RANGE' not in flavor:
            return CellPosition(CellType.OPTIONAL, None)
        if col <= self._keyword_column + until_range + 1:
            return CellPosition(CellType.MANDATORY, None)
        if col <= self._keyword_column + until_range + 3:
            return CellPosition(CellType.OPTIONAL, None)
        return CellPosition(CellType.MUST_BE_EMPTY, None)

    def get_cell_info(self, col):
        position = self._get_cell_position(col)
        content = self._get_content_with_type(col, position)
        return self._build_cell_info(content, position)

    def _build_cell_info(self, content, position):
        return CellInfo(content, position, for_loop=True)

    @property
    def steps(self):
        return [IntendedStepController(self, sub_step)
                for sub_step in self.get_raw_steps()]

    def index_of_step(self, step):
        index_in_for_loop = self.get_raw_steps().index(step)
        return self._index() + index_in_for_loop + 1

    def _get_comment(self, cells):
        return None

    def comment(self):
        print(f"\nDEBUG: ForLoopStepController RAW STEPS: {self.get_raw_steps()}")
        for i in self.get_raw_steps():
            print(f"\nDEBUG: ForLoopStepController PRINT STEPS: {i.as_list()}")
        col = self.step_controller_step.inner_kw_pos
        header = self.as_list()
        if col > 0:
            self._replace_with_new_cells(header[0:col-1] + ['Comment'] + header[col:])
        else:
            self._replace_with_new_cells(['Comment'] + header)

    def contains_keyword(self, name):
        return False

    def add_step(self, step):
        print(f"\nDEBUG: ForLoopStepController enter add_step step={step.as_list()}")
        self.get_raw_steps().append(step)

    def recreate(self, cells, comment=None, delete=False):
        kw_index = None
        for idx in range(0, len(cells)):
            if cells[idx] == '':
                continue
            if cells[idx] == 'FOR':
                kw_index = idx
            break
        if kw_index and not delete:  # Avoid IndentedStep when DeleteCells
            if comment:
                self._recreate_complete_for_loop_header(['', cells[:], comment[:]])
            else:
                self._recreate_complete_for_loop_header([''] + cells)
        else:
            new_cells = cells[:]
            index = self._index()
            self.parent.replace_step(index, robotapi.Step(new_cells, comment))
        self.recalculate_keyword_column()

    def _recreate_complete_for_loop_header(self, cells):
        self.step_controller_step.__init__(self.parent, cells[:])

    def remove(self):
        steps = self.parent.data.steps
        index = steps.index(self.step_controller_step)
        steps.remove(self.step_controller_step)
        self.parent.data.steps = \
            steps[:index] + self.get_raw_steps() + steps[index:]
        self.step_controller_step.steps = []

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
        index = self.parent.index_of_step(self.step_controller_step)
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

    def _get_cell_position(self, col):
        if col < self._keyword_column:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        return StepController._get_cell_position(self, col)

    def _get_local_namespace(self):
        p = self.parent.parent
        index = p.index_of_step(self.step_controller_step)
        return local_namespace(p, self.datafile_controller.namespace, index)

    def _get_content_with_type(self, col, position):
        if col < self._keyword_column:
            return CellContent(ContentType.EMPTY, None)
        return StepController._get_content_with_type(self, col, position)

    def recreate(self, cells, comment=None, delete=False):
        if (cells == [] or cells[0] == '') and not delete:  # Avoid IndentedStep when DeleteCells
            self.step_controller_step.__init__(cells[:], comment=comment)
            if self.step_controller_step not in self.parent.get_raw_steps():
                self.parent.add_step(self.step_controller_step)
        else:
            self.step_controller_step.__init__(cells[:], comment=comment)
            if self.step_controller_step not in self.parent.get_raw_steps():
                self.parent.add_step(self.step_controller_step)
            if not delete:
                self._recreate_as_normal_step(cells, comment)
        self.recalculate_keyword_column()

    def _recreate_as_normal_step(self, cells, comment=None):
        steps = self.parent.steps
        index = [s.step_controller_step for s in steps].index(self.step_controller_step)
        for i, step in reversed(list(enumerate(steps))):
            if i == index:
                break
            step.replace_with_normal_step(i, step.as_list())
        self.replace_with_normal_step(index, cells, comment)

    def replace_with_normal_step(self, index, cells=None, comment=None):
        index_of_parent = self.parent.parent.index_of_step(self.parent.step_controller_step)
        self.parent.parent.add_step(
            index_of_parent + index + 2,
            robotapi.Step(cells or self.as_list(), comment=comment))
        self.parent.get_raw_steps().pop(index)

    def remove(self):
        self.parent.get_raw_steps().remove(self.step_controller_step)

    def remove_empty_columns_from_end(self):
        if self._invalid:
            return
        StepController.remove_empty_columns_from_end(self)
