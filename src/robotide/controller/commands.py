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
from robotide.publish.messages import RideTestCaseStepsChanged


KEYWORD_NAME_FIELD = 'Keyword Name'


class Occurrence(object):

    def __init__(self, item):
        self._item = item

    @property
    def usage(self):
        return self._item.logical_name

    def inform_keyword_name_changed(self, new_name):
        self._item.keyword_rename(new_name)


class KeywordNameController(object):

    def __init__(self, keyword):
        self._keyword = keyword

    def contains_keyword(self, name):
        return self._keyword.name == name

    def keyword_rename(self, new_name):
        self._keyword.rename(new_name)

    @property
    def logical_name(self):
        return '%s (%s)' % (self._keyword.name, KEYWORD_NAME_FIELD)


class _Command(object):

    def execute(self, context):
        return self._execute(context)


class _ValueChangingCommand(object):

    def execute(self, context):
        if self.change_value(context):
            RideTestCaseStepsChanged(test=context).publish()

    def change_value(self, context):
        '''Return True if value successfully changed, False otherwise'''
        raise NotImplementedError(self.__class__.__name__)

    def _step(self, context):
        return context.steps[self._row]


class RenameOccurrences(_ValueChangingCommand):

    def __init__(self, original_name, new_name):
        self._original_name = original_name
        self._new_name = new_name

    def change_value(self, context):
        occurrences = context.execute(FindOccurrences(self._original_name))
        if not occurrences:
            return False
        for oc in occurrences:
            oc.inform_keyword_name_changed(self._new_name)
        return True


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
                items.extend(test.steps + test.settings)
            for kw in df.keywords:
                items.append(KeywordNameController(kw))
                items.extend(kw.steps)
        return items

    def _find_occurrences_in(self, items):
        return [Occurrence(item) for item in items
                if item.contains_keyword(self._keyword_name)]


class ChangeCellValue(_ValueChangingCommand):

    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value

    def change_value(self, context):
        steps = context.steps
        while len(steps) <= self._row:
            context.add_step(len(steps))
            steps = context.steps
        step = self._step(context)
        step.change(self._col, self._value)
        step.remove_empty_columns_from_end()
        return True


class Purify(_ValueChangingCommand):

    def change_value(self, context):
        for step in context.steps:
            step.remove_empty_columns_from_end()
            if step.has_only_comment():
                step.remove_empty_columns_from_beginning()
        context.remove_empty_steps()
        return True


class InsertCell(_ValueChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def change_value(self, context):
        self._step(context).shift_right(self._col)
        return True


class DeleteCell(_ValueChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def change_value(self, context):
        self._step(context).shift_left(self._col)
        return True


class _RowChangingCommand(_ValueChangingCommand):

    def __init__(self, row):
        '''Command that will operate on a given logical `row` of test/user keyword.

        Giving -1 as `row` means that opeartion is done on the last row.
        '''
        self._row = row

    def change_value(self, context):
        if len(context.steps) <= self._row:
            return False
        self._change_value(context)
        return True


class DeleteRow(_RowChangingCommand):

    def _change_value(self, context):
        context.remove_step(self._row)


class AddRow(_RowChangingCommand):

    def _change_value(self, context):
        row = self._row if self._row != -1 else len(context.steps)
        context.add_step(row)


class CommentRow(_RowChangingCommand):

    def _change_value(self, context):
        self._step(context).comment()
        return True


class UncommentRow(_RowChangingCommand):

    def _change_value(self, context):
        self._step(context).uncomment()
        return True


class CompositeCommand(_ValueChangingCommand):

    def __init__(self, *commands):
        self._commands = commands

    def change_value(self, context):
        return any([cmd.change_value(context) for cmd in self._commands])


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
