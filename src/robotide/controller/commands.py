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

class RenameOccurrences(_Command):

    def __init__(self, original_name, new_name):
        self._original_name = original_name
        self._new_name = new_name

    def _execute(self, context):
        occurrences = context.execute(FindOccurrences(self._original_name))
        for oc in occurrences:
            oc.inform_keyword_name_changed(self._new_name)

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


class _ValueChangingCommand(object):

    def execute(self, context):
        result = self.execute_with(context)
        context.notify_changed()
        return result


class ChangeCellValue(_ValueChangingCommand):
    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value

    def execute_with(self, context):
        steps = context.steps
        while len(steps) <= self._row:
            context.add_step(len(steps))
            steps = context.steps
        step = context.steps[self._row]
        step.change(self._col, self._value)
        step.remove_empty_columns_from_end()

class DeleteRow(_ValueChangingCommand):
    def __init__(self, row):
        self._row = row
    
    def execute_with(self, context):
        context.remove_step(self._row)

class AddRow(_ValueChangingCommand):

    def __init__(self, row = None):
        self._row = row
    
    def execute_with(self, context):
        row = self._row
        if row is None: row = len(context.steps)
        context.add_step(row)

class Purify(_ValueChangingCommand):

    def execute_with(self, context):
        for step in context.steps:
            step.remove_empty_columns_from_end()
            if step.has_only_comment():
                step.remove_empty_columns_from_beginning()
        context.remove_empty_steps()

class InsertCell(_ValueChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def execute_with(self, context):
        context.steps[self._row].shift_right(self._col)

class DeleteCell(_ValueChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def execute_with(self, context):
        context.steps[self._row].shift_left(self._col)

class CompositeCommand(_ValueChangingCommand):

    def __init__(self, *commands):
        self._commands = commands

    def execute_with(self, context):
        for cmd in self._commands:
            cmd.execute_with(context)

def DeleteRows(start, end):
    return CompositeCommand(*([DeleteRow(start)] * (end + 1 -start)))

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