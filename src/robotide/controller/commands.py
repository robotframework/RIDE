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

class CellValueChanged(_Command):
    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value

    def _execute(self, context):
        steps = context.steps
        while len(steps) <= self._row:
            context.add_step(len(steps))
            steps = context.steps
        step = context.steps[self._row]
        step.change(self._col, self._value)
        context.notify_changed()

class RowDelete(_Command):
    def __init__(self, row):
        self._row = row
    
    def _execute(self, context):
        context.remove_step(self._row)
        context.notify_changed()

class RowAdd(_Command):
    def __init__(self, row = None):
        self._row = row
    
    def _execute(self, context):
        row = self._row
        if row is None: row = len(context.steps)
        context.add_step(row)
        context.notify_changed()

class Purify(_Command):
    def _execute(self, context):
        for step in context.steps:
            step.remove_empty_columns_from_end()
        context.remove_empty_steps()
        context.notify_changed()