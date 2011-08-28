from robot.parsing.model import Step
from robotide import utils
from robotide.controller.cellinfo import CellPosition, CellType, CellInfo,\
    CellContent, ContentType


class StepController(object):

    def __init__(self, parent, step):
        self._init(parent, step)
        self._step.args = self._change_last_empty_to_empty_var(self._step.args, self._step.comment)
        self._step.comment = self._remove_whitespace(self._step.comment)

    def _init(self, parent, step):
        self.parent = parent
        self._step = step
        self._cell_info_cache = {}

    def _change_last_empty_to_empty_var(self, args, comment):
        if comment:
            return args
        return args[:-1] + ['${EMPTY}'] if args and args[-1] == '' else args

    def _remove_whitespace(self, comment):
        # TODO: This can be removed with RF 2.6
        return comment.strip() if comment else comment

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

    def get_cell_info(self, col):
        if col not in self._cell_info_cache:
            position = self._get_cell_position(col)
            content = self._get_content_with_type(col)
            self._cell_info_cache[col] = self._build_cell_info(content, position)
        return self._cell_info_cache[col]

    def is_assigning(self, value):
        for assignment in self._step.assign:
            if assignment.replace('=', '').strip() == value:
                return True
        return False

    def _build_cell_info(self, content, position):
        return CellInfo(content, position)

    def _get_cell_position(self, col):
        # TODO: refactor
        if self.parent.has_template():
            return CellPosition(CellType.UNKNOWN, None)
        col -= len(self._step.assign)
        if col < 0:
            return CellPosition(CellType.ASSIGN, None)
        if col == 0:
            return CellPosition(CellType.KEYWORD, None)
        info = self.get_keyword_info(self._step.keyword)
        if not info:
            return CellPosition(CellType.UNKNOWN, None)
        args = info.arguments
        args_amount = len(args)
        if args_amount == 0:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        if col >= args_amount and self._last_argument_is_varargs(args):
            return CellPosition(CellType.OPTIONAL, args[-1])
        if self._has_list_var_value_before(col-1):
            return CellPosition(CellType.UNKNOWN, None)
        if col > args_amount:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        defaults = [arg for arg in args if '=' in arg]
        if col <= args_amount-len(defaults):
            return CellPosition(CellType.MANDATORY, args[col-1])
        return CellPosition(CellType.OPTIONAL, args[col-1])

    def _last_argument_is_varargs(self, args):
        return args[-1].startswith('*')

    def _has_list_var_value_before(self, arg_index):
        for idx, value in enumerate(self.args):
            if idx > arg_index:
                return False
            if utils.is_list_variable(value):
                return True
        return False

    def _get_content_with_type(self, col):
        value = self.get_value(col)
        if self._is_commented(col):
            return CellContent(ContentType.COMMENTED, value, None)
        if self._get_last_none_empty_col_idx() < col:
            return CellContent(ContentType.EMPTY, value, None)
        if utils.is_variable(value):
            return CellContent(ContentType.VARIABLE, value, None)
        if self.is_user_keyword(value):
            return CellContent(ContentType.USER_KEYWORD, value, self.get_keyword_info(value).source)
        if self.is_library_keyword(value):
            return CellContent(ContentType.LIBRARY_KEYWORD, value, self.get_keyword_info(value).source)
        return CellContent(ContentType.STRING, value, None)

    def _get_last_none_empty_col_idx(self):
        values = self.as_list()
        for i in reversed(range(len(values))):
            if values[i].strip() != '':
                return i
        return None

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

    def __init__(self, parent, step):
        self._init(parent, step)

    @property
    def name(self):
        return self.parent.name

    def move_up(self):
        previous_step = self.parent.step(self._index()-1)
        self._get_raw_steps().insert(0, previous_step._step)
        previous_step.remove()

    def move_down(self):
        next_step = self.step(self._index()+1)
        next_step.move_up()
        if len(self._step.steps) == 0:
            self._replace_with_new_cells(cells=self.as_list())

    def insert_after(self, new_step):
        self._get_raw_steps().insert(0, new_step)

    def step(self, index):
        return self.parent.step(index)

    def _has_comment_keyword(self):
        return False

    def _get_raw_steps(self):
        return self._step.steps

    def _set_raw_steps(self, steps):
        self._step.steps = steps

    def _get_cell_position(self, col):
        until_range = len(self._step.vars)+1
        if col <= until_range:
            return CellPosition(CellType.MANDATORY, None)
        if not self._step.range:
            return CellPosition(CellType.OPTIONAL, None)
        if col <= until_range+1:
            return CellPosition(CellType.MANDATORY, None)
        if col <= until_range+3:
            return CellPosition(CellType.OPTIONAL, None)
        return CellPosition(CellType.MUST_BE_EMPTY, None)

    def _build_cell_info(self, content, position):
        return CellInfo(content, position, for_loop=True)

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

    def has_template(self):
        return self.parent.has_template()


class IntendedStepController(StepController):

    @property
    def _keyword_column(self):
        return 1

    def as_list(self):
        return ['']+self._step.as_list()

    def _get_cell_position(self, col):
        if col == 0:
            return CellPosition(CellType.MUST_BE_EMPTY, None)
        return StepController._get_cell_position(self, col-1)

    def _get_content_with_type(self, col):
        if col == 0:
            return CellContent(ContentType.EMPTY, None, None)
        return StepController._get_content_with_type(self, col)

    def comment(self):
        self._step.__init__(['Comment'] + self._step.as_list())

    def uncomment(self):
        if self._step.keyword == 'Comment':
            self._step.__init__(self._step.as_list()[1:])

    def _recreate(self, cells, comment=None):
        if cells == [] or cells[0] == '':
            self._step.__init__(cells[1:] if cells != [] else [])
            if self._step not in self.parent._get_raw_steps():
                self.parent.add_step(self._step)
        else:
            index = self.parent._get_raw_steps().index(self._step)
            index_of_parent = self.parent.parent.index_of_step(self.parent._step)
            self.parent._replace_with_new_cells(self.parent.as_list())
            self.parent.parent.replace_step(index+index_of_parent+1, Step(cells))

    def remove(self):
        self.parent._get_raw_steps().remove(self._step)
