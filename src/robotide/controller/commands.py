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

from itertools import chain

from robotide.controller.macrocontrollers import KeywordNameController, \
        ForLoopStepController
from robotide.controller.settingcontrollers import _SettingController
import time


class Occurrence(object):

    def __init__(self, item, value):
        self._item = item
        self._value = value
        self._replaced = False
        self.count = 1

    def __eq__(self, other):
        if not isinstance(other, Occurrence):
            return False
        return (self.parent is other.parent and
                self._in_steps() and other._in_steps())

    @property
    def item(self):
        return self._item

    @property
    def source(self):
        return self.datafile.source

    @property
    def datafile(self):
        return self._item.datafile

    @property
    def parent(self):
        if self._in_for_loop():
            return self._item.parent.parent
        return self._item.parent

    @property
    def location(self):
        return self._item.parent.name

    @property
    def usage(self):
        if self._in_settings():
            return self._item.label
        elif self._in_kw_name():
            return 'Keyword Name'
        return 'Steps' if self.count == 1 else 'Steps (%d usages)' % self.count

    def _in_settings(self):
        return isinstance(self._item, _SettingController)

    def _in_kw_name(self):
        return isinstance(self._item, KeywordNameController)

    def _in_steps(self):
        return not (self._in_settings() or self._in_kw_name())

    def _in_for_loop(self):
        return isinstance(self._item.parent, ForLoopStepController)

    def replace_keyword(self, new_name):
        self._item.replace_keyword(*self._get_replace_values(new_name))
        self._replaced = not self._replaced

    def _get_replace_values(self, new_name):
        if self._replaced:
            return self._value, new_name
        return new_name, self._value

    def notify_value_changed(self):
        self._item.notify_value_changed()


class _Command(object):

    def execute(self, context):
        raise NotImplementedError(self.__class__)


class CopyMacroAs(_Command):

    def __init__(self, new_name):
        self._new_name = new_name

    def execute(self, context):
        context.copy(self._new_name)


class _ReversibleCommand(_Command):

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


class MoveTo(_Command):

    def __init__(self, destination):
        self._destination = destination

    def execute(self, context):
        context.delete()
        self._destination.add_test_or_keyword(context)

class CreateNewResource(_Command):

    def __init__(self, path):
        self._path = path

    def execute(self, context):
        res = context.new_resource(self._path)
        context.update_default_dir(self._path)
        return res


class _StepsChangingCommand(_ReversibleCommand):

    def _execute(self, context):
        if self.change_steps(context):
            context.notify_steps_changed()
            return True
        return False

    def change_steps(self, context):
        '''Return True if steps changed, False otherwise'''
        raise NotImplementedError(self.__class__.__name__)

    def _step(self, context):
        return context.steps[self._row]


class NullObserver(object):

    notify = finish = lambda x:None


class RenameKeywordOccurrences(_ReversibleCommand):

    def __init__(self, original_name, new_name, observer):
        self._original_name = original_name
        self._new_name = new_name
        self._observer = observer
        self._occurrences = None

    def _execute(self, context):
        self._observer.notify()
        self._occurrences = self._find_occurrences(context) if self._occurrences is None \
                            else self._occurrences
        self._replace_keywords_in(self._occurrences)
        context.update_namespace()
        self._notify_values_changed(self._occurrences)
        self._observer.finish()

    def _find_occurrences(self, context):
        occurrences = []
        for occ in context.execute(FindOccurrences(self._original_name)):
            self._observer.notify()
            occurrences.append(occ)
        self._observer.notify()
        return occurrences

    def _replace_keywords_in(self, occurrences):
        for oc in occurrences:
            oc.replace_keyword(self._new_name)
            self._observer.notify()

    def _notify_values_changed(self, occurrences):
        for oc in occurrences:
            oc.notify_value_changed()
            self._observer.notify()

    def _get_undo_command(self):
        self._observer = NullObserver()
        return self


class RenameTest(_ReversibleCommand):

    def __init__(self, new_name):
        self._new_name = new_name

    def _execute(self, context):
        context.test_name.rename(self._new_name)
        context.test_name.notify_value_changed()

    def _get_undo_command(self):
        return self


class UpdateVariable(_Command):

    def __init__(self, new_name, new_value, new_comment):
        self._new_name = new_name
        self._new_value = new_value
        self._new_comment = new_comment

    def execute(self, context):
        context.set_value(self._new_name, self._new_value)
        context.set_comment(self._new_comment)
        context.notify_value_changed()


class FindOccurrences(_Command):

    def __init__(self, keyword_name, keyword_info=None):
        if keyword_name.strip() == '':
            raise ValueError('Keyword name can not be "%s"' % keyword_name)
        self._keyword_name = keyword_name
        self._keyword_info = keyword_info

    def execute(self, context):
        self._keyword_source = self._keyword_info and self._keyword_info.source or \
                               self._find_keyword_source(context.datafile_controller)
        return self._find_occurrences_in(self._items_from(context))

    def _items_from(self, context):
        for df in context.all_datafiles:
            self._yield_for_other_threads()
            if self._find_keyword_source(df) == self._keyword_source:
                for item in self._items_from_datafile(df):
                    yield item

    def _items_from_datafile(self, df):
        for setting in df.settings:
            yield setting
        for items_from_test in (self._items_from_test(test) for test in df.tests):
            for item in items_from_test:
                yield item
        for items_from_keyword in (self._items_from_keyword(kw) for kw in df.keywords):
            for item in items_from_keyword:
                yield item

    def _items_from_keyword(self, kw):
        return chain([kw.keyword_name] if kw.source == self._keyword_source else [],
                     kw.steps)

    def _items_from_test(self, test):
        return chain(test.settings, test.steps)

    def _find_keyword_source(self, datafile_controller):
        item_info = datafile_controller.keyword_info(self._keyword_name)
        return item_info.source if item_info else None

    def _find_occurrences_in(self, items):
        return (Occurrence(item, self._keyword_name) for item in items
                if self._contains_keyword(item))

    def _contains_keyword(self, item):
        self._yield_for_other_threads()
        return item.contains_keyword(self._keyword_name)

    def _yield_for_other_threads(self):
        # GIL !?#!!!
        # THIS IS TO ENSURE THAT OTHER THREADS WILL GET SOME SPACE ALSO
        time.sleep(0)


def AddKeywordFromCells(cells):
    if not cells:
        raise ValueError('Keyword can not be empty')
    while cells[0] == '':
        cells.pop(0)
    name = cells[0]
    args = cells[1:]
    argstr = ' | '.join(('${arg%s}' % (i + 1) for i in range(len(args))))
    return AddKeyword(name, argstr)


class AddKeyword(_ReversibleCommand):

    def __init__(self, new_kw_name, args=None):
        self._kw_name = new_kw_name
        self._args = args or []

    def _execute(self, context):
        kw = context.create_keyword(self._kw_name, self._args)
        self._undo_command = RemoveMacro(kw)
        return kw

    def _get_undo_command(self):
        return self._undo_command


class AddTestCase(_Command):

    def __init__(self, new_test_name):
        self._test_name = new_test_name

    def execute(self, context):
        return context.create_test(self._test_name)


class AddSuite(_Command):

    def __init__(self, data):
        self._data = data

    def execute(self, context):
        ctrl = context.new_datafile(self._data)
        context.notify_suite_added(ctrl)
        return ctrl


class RemoveVariable(_ReversibleCommand):

    def __init__(self, var_controller):
        self._var_controller = var_controller
        self._undo_command = AddVariable(var_controller.name,
                                         var_controller.value,
                                         var_controller.comment)

    def _execute(self, context):
        context.datafile_controller.\
            variables.remove_var(self._var_controller)

    def _get_undo_command(self):
        return self._undo_command


class AddVariable(_ReversibleCommand):

    def __init__(self, name, value, comment):
        self._name = name
        self._value = value
        self._comment = comment

    def _execute(self, context):
        var_controller = context.datafile_controller.\
            variables.add_variable(self._name, self._value, self._comment)
        self._undo_command = RemoveVariable(var_controller)
        return var_controller

    def _get_undo_command(self):
        return self._undo_command


class RecreateMacro(_ReversibleCommand):

    def __init__(self, user_script):
        self._user_script = user_script

    def _execute(self, context):
        self._user_script.recreate()

    def _get_undo_command(self):
        return RemoveMacro(self._user_script)


class RemoveMacro(_ReversibleCommand):

    def __init__(self, item):
        self._item = item

    def _execute(self, context):
        self._item.delete()

    def _get_undo_command(self):
        return RecreateMacro(self._item)


class ExtractKeyword(_Command):

    def __init__(self, new_kw_name, new_kw_args, step_range):
        self._name = new_kw_name
        self._args = new_kw_args
        self._rows = step_range

    def execute(self, context):
        context.extract_keyword(self._name, self._args, self._rows)
        context.notify_steps_changed()
        context.clear_undo()


def ExtractScalar(name, value, comment, cell):
    return CompositeCommand(AddVariable(name, value, comment),
                            ChangeCellValue(cell[0], cell[1], name))


def ExtractList(name, value, comment, cells):
    row, col = cells[0]
    return CompositeCommand(AddVariable(name, value, comment),
                            ChangeCellValue(row, col, name),
                            DeleteCells((row, col+1), (row, col+len(cells)-1)))


class ChangeCellValue(_StepsChangingCommand):

    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value if isinstance(value, unicode) else unicode(value, 'utf-8')

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

class SaveFile(_Command):

    def execute(self, context):
        datafile_controller = context.datafile_controller
        for macro_controller in chain(datafile_controller.tests, datafile_controller.keywords):
            macro_controller.execute(Purify())
        datafile_controller.save()
        datafile_controller.unmark_dirty()

class SaveAll(_Command):

    def execute(self, context):
        for datafile_controller in context._get_all_dirty_controllers():
            datafile_controller.execute(SaveFile())

class Purify(_Command):

    def execute(self, context):
        for step in context.steps:
            step.remove_empty_columns_from_end()
            if step.has_only_comment():
                step.remove_empty_columns_from_beginning()
        context.remove_empty_steps()
        context.notify_steps_changed()


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
        self._undo_command = StepsChangingCompositeCommand(InsertCell(self._row, self._col),
                                              ChangeCellValue(self._row, self._col,
                                                              step.get_value(self._col)))
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
        self._undo_command = StepsChangingCompositeCommand(AddRow(self._row), PasteArea((self._row, 0), [step.as_list()]))
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


class MoveRowsUp(_StepsChangingCommand):

    def __init__(self, rows):
        self._rows = rows

    def change_steps(self, context):
        if self._last_row > len(context.steps)-1 or self._first_row == 0:
            return False
        for row in self._rows:
            context.move_step_up(row)
        return True

    @property
    def _last_row(self):
        return self._rows[-1]

    @property
    def _first_row(self):
        return self._rows[0]

    def _get_undo_command(self):
        return MoveRowsDown([r-1 for r in self._rows])


class MoveRowsDown(_StepsChangingCommand):

    def __init__(self, rows):
        self._rows = rows

    def change_steps(self, context):
        if self._last_row >= len(context.steps)-1:
            return False
        for row in reversed(self._rows):
            context.move_step_down(row)
        return True

    @property
    def _last_row(self):
        return self._rows[-1]

    def _get_undo_command(self):
        return MoveRowsUp([r+1 for r in self._rows])


class CompositeCommand(_ReversibleCommand):

    def __init__(self, *commands):
        self._commands = commands

    def _execute(self, context):
        executions = self._executions(context)
        undos = [undo for _, undo in executions]
        undos.reverse()
        self._undo_command = self._create_undo_command(undos)
        return [result for result, _ in executions]

    def _get_undo_command(self):
        return self._undo_command

    def _create_undo_command(self, undos):
        return CompositeCommand(*undos)

    def _executions(self, context):
        return [(cmd._execute(context), cmd._get_undo_command()) for cmd in self._commands]


class StepsChangingCompositeCommand(_StepsChangingCommand, CompositeCommand):

    def __init__(self, *commands):
        self._commands = commands

    def change_steps(self, context):
        return any(changed for changed in CompositeCommand._execute(self, context))

    def _get_undo_command(self):
        return self._undo_command

    def _create_undo_command(self, undos):
        return StepsChangingCompositeCommand(*undos)

    def _executions(self, context):
        return [(cmd.change_steps(context), cmd._get_undo_command()) for cmd in self._commands]


def DeleteRows(rows):
    return StepsChangingCompositeCommand(*[DeleteRow(r) for r in reversed(sorted(rows))])


def AddRows(rows):
    return StepsChangingCompositeCommand(*[AddRow(r) for r in reversed(sorted(rows))])


def CommentRows(rows):
    return StepsChangingCompositeCommand(*[CommentRow(r) for r in rows])


def UncommentRows(rows):
    return StepsChangingCompositeCommand(*[UncommentRow(r) for r in rows])


def ClearArea(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(*[ChangeCellValue(row, col, '')
                              for row in range(row_s,row_e+1)
                              for col in range(col_s, col_e+1)])


def PasteArea(top_left, content):
    row_s, col_s = top_left
    return StepsChangingCompositeCommand(*[ChangeCellValue(row+row_s, col+col_s, content[row][col])
                              for row in range(len(content))
                              for col in range(len(content[0]))])


def InsertCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(*[InsertCell(row, col)
                              for row in range(row_s,row_e+1)
                              for col in range(col_s, col_e+1)])


def DeleteCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(*[DeleteCell(row, col_s)
                              for row in range(row_s,row_e+1)
                              for _ in range(col_s, col_e+1)])
