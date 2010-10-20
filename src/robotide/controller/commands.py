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


KEYWORD_NAME_FIELD = 'Keyword Name'
TESTCASE_NAME_FIELD = 'Test Case Name'

class Occurrence(object):

    def __init__(self, item, value):
        self._item = item
        self._value = value

    @property
    def item(self):
        return self._item

    @property
    def usage(self):
        return self._item.logical_name

    def replace_keyword(self, new_name):
        self._item.replace_keyword(new_name, self._value)

    def notify_value_changed(self):
        self._item.notify_value_changed()

class ItemNameController(object):

    def __init__(self, item):
        self._item = item

    def contains_keyword(self, name):
        return self._item.name == name

    def replace_keyword(self, new_name, old_value=None):
        self._item.rename(new_name)

    def notify_value_changed(self):
        self._item.notify_value_changed()

    @property
    def logical_name(self):
        return '%s (%s)' % (self._item.name, self._name_field)


class KeywordNameController(ItemNameController):
    _name_field = KEYWORD_NAME_FIELD

class TestCaseNameController(ItemNameController):
    _name_field = TESTCASE_NAME_FIELD


class _Command(object):

    def execute(self, context):
        return self._execute(context)

class _UndoableCommand(object):
    
    def execute(self, context):
        result = self._execute_without_redo_clear(context)
        context.clear_redo()
        return result
    
    def _execute_without_redo_clear(self, context):
        result = self._execute(context)
        context.push_to_undo(self._get_undo_command())
        return result
    
    @property
    def _get_undo_command(self):
        raise NotImplementedError(self.__class__.__name__)

class Undo(_Command):
    
    def execute(self, context):
        if not context.is_undo_empty():
            result = context.pop_from_undo()._execute_without_redo_clear(context)
            redo_command = context.pop_from_undo()
            context.push_to_redo(redo_command)
            return result

class Redo(_Command):
    
    def execute(self, context):
        if not context.is_redo_empty():
            return context.pop_from_redo()._execute_without_redo_clear(context)

class _StepsChangingCommand(_UndoableCommand):

    def _execute(self, context):
        if self.change_steps(context):
            context.notify_steps_changed()

    def change_steps(self, context):
        '''Return True if steps changed, False otherwise'''
        raise NotImplementedError(self.__class__.__name__)

    def _step(self, context):
        return context.steps[self._row]


class RenameOccurrences(_Command):

    def __init__(self, original_name, new_name):
        self._original_name = original_name
        self._new_name = new_name

    def _execute(self, context):
        occurrences = context.execute(FindOccurrences(self._original_name))
        for oc in occurrences:
            oc.replace_keyword(self._new_name)
            oc.notify_value_changed()


class FindOccurrences(_Command):

    def __init__(self, keyword_name):
        self._keyword_name = keyword_name

    def _execute(self, context):
        return self._find_occurrences_in(self._items_from(context))

    def _items_from(self, context):
        items = []
        for df in context.all_datafiles:
            items.extend(df.settings)
            for test in df.tests:
                items.append(TestCaseNameController(test))
                items.extend(test.steps + test.settings)
            for kw in df.keywords:
                items.append(KeywordNameController(kw))
                items.extend(kw.steps)
        return items

    def _find_occurrences_in(self, items):
        return [Occurrence(item, self._keyword_name) for item in items
                if item.contains_keyword(self._keyword_name)]


class ChangeCellValue(_StepsChangingCommand):

    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value

    def change_steps(self, context):
        steps = context.steps
        while len(steps) <= self._row:
            context.add_step(len(steps))
            steps = context.steps
        step = self._step(context)
        self._undo_command = ChangeCellValue(self._row, self._col, step.get_value(self._col))
        step.change(self._col, self._value)
        step.remove_empty_columns_from_end()
        return True

    def _get_undo_command(self):
        return self._undo_command


class Purify(_StepsChangingCommand):

    def change_steps(self, context):
        for step in context.steps:
            step.remove_empty_columns_from_end()
            if step.has_only_comment():
                step.remove_empty_columns_from_beginning()
        context.remove_empty_steps()
        return True

    def _get_undo_command(self):
        return None


class InsertCell(_StepsChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def change_steps(self, context):
        self._step(context).shift_right(self._col)
        return True

    def _get_undo_command(self):
        return DeleteCell(self._row, self._col)


class DeleteCell(_StepsChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def change_steps(self, context):
        step = self._step(context)
        self._undo_command = CompositeCommand(InsertCell(self._row, self._col), 
                                              ChangeCellValue(self._row, self._col, step.get_value(self._col)))
        step.shift_left(self._col)
        return True

    def _get_undo_command(self):
        return self._undo_command


class _RowChangingCommand(_StepsChangingCommand):

    def __init__(self, row):
        '''Command that will operate on a given logical `row` of test/user keyword.

        Giving -1 as `row` means that opeartion is done on the last row.
        '''
        self._row = row

    def change_steps(self, context):
        if len(context.steps) <= self._row:
            return False
        self._change_value(context)
        return True

class DeleteRow(_RowChangingCommand):
    def _change_value(self, context):
        step = context.steps[self._row]
        self._undo_command = CompositeCommand(AddRow(self._row), PasteArea((self._row, 0), [step.as_list()]))
        context.remove_step(self._row)

    def _get_undo_command(self):
        if hasattr(self, '_undo_command'):
            return self._undo_command
        return AddRow(self._row)

class AddRow(_RowChangingCommand):

    def _change_value(self, context):
        row = self._row if self._row != -1 else len(context.steps)
        context.add_step(row)

    def _get_undo_command(self):
        return DeleteRow(self._row)


class CommentRow(_RowChangingCommand):

    def _change_value(self, context):
        self._step(context).comment()
        return True

    def _get_undo_command(self):
        return UncommentRow(self._row)


class UncommentRow(_RowChangingCommand):

    def _change_value(self, context):
        self._step(context).uncomment()
        return True

    def _get_undo_command(self):
        return CommentRow(self._row)


class CompositeCommand(_StepsChangingCommand):

    def __init__(self, *commands):
        self._commands = commands

    def change_steps(self, context):
        executions = [(cmd.change_steps(context), cmd._get_undo_command()) for cmd in self._commands]
        undos = [undo for _,undo in executions]
        undos.reverse()
        self._undo_command = CompositeCommand(*undos)
        return any(changed for changed,_ in executions)

    def _get_undo_command(self):
        return self._undo_command

def DeleteRows(rows):
    return CompositeCommand(*[DeleteRow(r) for r in reversed(sorted(rows))])


def AddRows(rows):
    return CompositeCommand(*[AddRow(r) for r in sorted(rows)])


def CommentRows(rows):
    return CompositeCommand(*[CommentRow(r) for r in rows])


def UncommentRows(rows):
    return CompositeCommand(*[UncommentRow(r) for r in rows])


def ClearArea(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return CompositeCommand(*[ChangeCellValue(row, col, '')
                              for row in range(row_s,row_e+1)
                              for col in range(col_s, col_e+1)])


def PasteArea(top_left, content):
    row_s, col_s = top_left
    return CompositeCommand(*[ChangeCellValue(row+row_s, col+col_s, content[row][col])
                              for row in range(len(content))
                              for col in range(len(content[0]))])


def InsertCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return CompositeCommand(*[InsertCell(row, col)
                              for row in range(row_s,row_e+1)
                              for col in range(col_s, col_e+1)])


def DeleteCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return CompositeCommand(*[DeleteCell(row, col_s)
                              for row in range(row_s,row_e+1)
                              for _ in range(col_s, col_e+1)])
