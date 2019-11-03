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

from itertools import chain
import time
import os
import re

from robotide.namespace.embeddedargs import EmbeddedArgsHandler
from robotide.publish.messages import RideSelectResource, RideFileNameChanged, RideSaving, RideSaved, RideSaveAll, RideExcludesChanged
from robotide.namespace.namespace import _VariableStash

from robotide.utils import PY3
if PY3:
    from robotide.utils import basestring
from robotide.utils import overrides, variablematcher
from robotide.controller.filecontrollers import ResourceFileController
from robotide.controller.macrocontrollers import KeywordNameController, ForLoopStepController, TestCaseController
from robotide.controller.settingcontrollers import _SettingController, VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.controller.validators import BaseNameValidator


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
        if self._in_variable_table():
            return "Variable Table"
        elif self._in_settings():
            return self._item.label
        elif self._in_kw_name():
            return 'Keyword Name'
        return 'Steps' if self.count == 1 else 'Steps (%d usages)' % self.count

    def _in_settings(self):
        return isinstance(self._item, _SettingController)

    def _in_variable_table(self):
        return isinstance(self._item, VariableTableController)

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

    modifying = True

    def execute(self, context):
        raise NotImplementedError(self.__class__)

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self._params_str())

    def _params_str(self):
        return ', '.join(self._format_param(p) for p in self._params())

    def _format_param(self, param):
        if isinstance(param, basestring):
            return '"%s"' % param
        return str(param)

    def _params(self):
        return []


class CopyMacroAs(_Command):

    def __init__(self, new_name):
        self._new_name = new_name

    def execute(self, context):
        context.copy(self._new_name)

    def _params(self):
        return [self._new_name]


class ChangeTag(_Command):

    def __init__(self, tag, value):
        self._tag = tag
        self._value = value.strip()

    def _params(self):
        return (self._tag, self._value)

    def execute(self, context):
        tags = [tag for tag in context if tag.controller == context]
        context.set_value(self._create_value(tags))
        context.notify_value_changed()

    def _create_value(self, old_values):
        if old_values == [] and self._tag.is_empty():
            return self._value
        return ' | '.join(value for value in
                          self._create_value_list(old_values)
                          if value != '')

    def _create_value_list(self, old_values):
        if self._tag.is_empty():
            return [v.name for v in old_values] + [self._value]
        else:
            new_list = []
            for v in old_values:
                if v != self._tag:
                    new_list.append(v.name)
            if self._value not in new_list:
                new_list += [self._value]
            return new_list


class DeleteTag(_Command):

    def execute(self, tag):
        tag.delete()
        tag.controller.notify_value_changed()


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
            result = context.pop_from_undo()._execute_without_redo_clear(
                context)
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

    def _params(self):
        return [self._destination]

    def execute(self, context):
        context.delete()
        self._destination.add_test_or_keyword(context)


class CreateNewResource(_Command):

    def __init__(self, path):
        self._path = path

    def execute(self, context):
        res = context.new_resource(self._path)
        RideSelectResource(item=res).publish()
        return res


class SetDataFile(_Command):

    def __init__(self, datafile):
        self._datafile = datafile

    def execute(self, context):
        context.mark_dirty()
        context.set_datafile(self._datafile)


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
        try:
            return context.steps[self._row]
        except IndexError:
            return NonExistingStep()


class NonExistingStep(object):
    def __getattr__(self, name):
        return lambda *args: ''


class NullObserver(object):
    notify = finish = lambda x: None


class RenameKeywordOccurrences(_ReversibleCommand):

    _gherkin_prefix = re.compile('^(Given|When|Then|And|But) ', re.IGNORECASE)

    def __init__(self, original_name, new_name, observer, keyword_info=None):
        self._original_name, self._new_name = self._check_gherkin(new_name,
                                                                  original_name
                                                                  )
        self._observer = observer
        self._keyword_info = keyword_info
        self._occurrences = None

    def _check_gherkin(self, new_name, original_name):
        was_gherkin, keyword_name = self._get_gherkin(original_name)
        is_gherkin, new_keyword_name = self._get_gherkin(new_name)
        if was_gherkin and not is_gherkin:
            keyword_name = original_name
        if not was_gherkin and is_gherkin:
            # When we change non-gherkin to gherkin, the keyword changes too.
            # The workaround is not to Rename keyword, but only edit field.
            new_keyword_name = new_name
        if was_gherkin and is_gherkin:
            # Check if the first word has changed
            if original_name.split(' ', 1)[0].lower() != new_name.split(
                    ' ', 1)[0].lower():
                new_keyword_name = new_name
                keyword_name = original_name
        return keyword_name, new_keyword_name

    def _get_gherkin(self, original_name):
        keyword_value = re.sub(self._gherkin_prefix, '', original_name)
        value_is_gherkin = (keyword_value != original_name)
        return value_is_gherkin, keyword_value

    def _params(self):
        return (self._original_name, self._new_name,
                self._observer, self._keyword_info)

    def _execute(self, context):
        self._observer.notify()
        self._occurrences = \
            self._find_occurrences(context) if self._occurrences is None \
            else self._occurrences
        self._replace_keywords_in(self._occurrences)
        context.update_namespace()
        self._notify_values_changed(self._occurrences)
        self._observer.finish()

    def _find_occurrences(self, context):
        occurrences = []
        for occ in context.execute(FindOccurrences(
                self._original_name, keyword_info=self._keyword_info)):
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

    def _params(self):
        return (self._new_name)

    def _execute(self, context):
        old_name  = context.name
        context.test_name.rename(self._new_name)
        context.test_name._item.notify_name_changed(old_name)

    def _get_undo_command(self):
        return self


class RenameFile(_Command):

    def __init__(self, new_basename):
        self._new_basename = new_basename
        self._validator = BaseNameValidator(new_basename)

    def execute(self, context):
        validation_result = self._validator.validate(context)
        if validation_result:
            old_filename = context.filename
            context.set_basename(self._new_basename.strip())
            RideFileNameChanged(datafile=context,
                                old_filename=old_filename).publish()
        return validation_result


class Include(_Command):

    def execute(self, excluded_controller):
        directory_controller = excluded_controller.remove_from_excludes()
        RideExcludesChanged(old_controller=excluded_controller,
                            new_controller=directory_controller).publish()


class Exclude(_Command):

    def execute(self, directory_controller):
        excluded_controller = directory_controller.exclude()
        RideExcludesChanged(old_controller=directory_controller,
                            new_controller=excluded_controller).publish()


class RenameResourceFile(_Command):

    def __init__(self, new_basename, get_should_modify_imports):
        self._new_basename = new_basename
        self._should_modify_imports = get_should_modify_imports

    def execute(self, context):
        validation_result = BaseNameValidator(
            self._new_basename).validate(context)
        if validation_result:
            old_filename = context.filename
            modify_imports = self._should_modify_imports()
            if modify_imports is None:
                return
            if modify_imports:
                context.set_basename_and_modify_imports(self._new_basename)
            else:
                context.set_basename(self._new_basename)
            RideFileNameChanged(datafile=context,
                                old_filename=old_filename).publish()
        return validation_result


class SortKeywords(_ReversibleCommand):
    index_difference = None

    def _execute(self, context):
        index_difference = context.sort_keywords()
        self._undo_command = RestoreKeywordOrder(index_difference)

    def _get_undo_command(self):
        return self._undo_command


class RestoreKeywordOrder(_ReversibleCommand):

    def __init__(self, index_difference):
        self._index_difference = index_difference

    def _execute(self, context):
        context.restore_keyword_order(self._index_difference)

    def _get_undo_command(self):
        return SortKeywords()


class _ItemCommand(_Command):

    def __init__(self, item):
        self._item = item


class UpdateDocumentation(_ItemCommand):

    def execute(self, context):
        context.editable_value = self._item


class MoveUp(_ItemCommand):

    def execute(self, context):
        context.move_up(self._item)


class MoveDown(_ItemCommand):

    def execute(self, context):
        context.move_down(self._item)


class DeleteItem(_ItemCommand):

    def execute(self, context):
        context.delete(self._item)


class ClearSetting(_Command):

    def execute(self, context):
        context.clear()


class DeleteFile(_Command):

    def execute(self, context):
        context.remove_from_filesystem()
        context.remove()

class OpenContainingFolder(_Command):
    modifying  = False

    def execute(self, context):
        context.open_filemanager()

class RemoveReadOnly(_Command):
    
    def execute(self, context):
        context.remove_readonly()
        
class DeleteFolder(_Command):

    def execute(self, context):
        context.remove_folder_from_filesystem()
        context.remove_from_model()


class SetValues(_Command):

    def __init__(self, values, comment):
        self._values = values
        self._comment = comment

    def execute(self, context):
        context.set_value(*self._values)
        context.set_comment(self._comment)


class AddLibrary(_Command):

    def __init__(self, values, comment):
        self._values = values
        self._comment = comment

    def execute(self, context):
        lib = context.add_library(*self._values)
        lib.set_comment(self._comment)
        return lib


class AddResource(_Command):

    def __init__(self, values, comment):
        self._values = values
        self._comment = comment

    def execute(self, context):
        res = context.add_resource(*self._values)
        res.set_comment(self._comment)
        return res


class AddVariablesFileImport(_Command):

    def __init__(self, values, comment):
        self._values = values
        self._comment = comment

    def execute(self, context):
        var = context.add_variables(*self._values)
        var.set_comment(self._comment)
        return var


class DeleteResourceAndImports(DeleteFile):

    def execute(self, context):
        context.remove_static_imports_to_this()
        DeleteFile.execute(self, context)


class DeleteFolderAndImports(DeleteFolder):

    def execute(self, context):
        context.remove_static_imports_to_this()
        DeleteFolder.execute(self, context)


class UpdateVariable(_Command):

    def __init__(self, new_name, new_value, new_comment):
        self._new_name = new_name
        self._new_value = new_value
        self._new_comment = new_comment

    def execute(self, context):
        has_data = context.has_data()
        context.set_value(self._new_name, self._new_value)
        context.set_comment(self._new_comment)
        if has_data:
            context.notify_value_changed()
        else:
            context.notify_variable_added()


class UpdateVariableName(_Command):

    def __init__(self, new_name):
        self._new_name = new_name

    def execute(self, context):
        context.execute(UpdateVariable(self._new_name, context.value,
                                       context.comment))


class FindOccurrences(_Command):
    modifying = False

    def __init__(self, keyword_name, keyword_info=None):
        if keyword_name.strip() == '':
            raise ValueError('Keyword name can not be "%s"' % keyword_name)
        self._keyword_name = keyword_name
        self._keyword_info = keyword_info
        self._keyword_regexp = self._create_regexp(keyword_name)

    def _create_regexp(self, keyword_name):
        if variablematcher.contains_scalar_variable(keyword_name) and \
                not variablematcher.is_variable(keyword_name):
            kw = lambda: 0
            kw.arguments = None
            kw.name = keyword_name
            return EmbeddedArgsHandler(kw).name_regexp

    def execute(self, context):
        self._keyword_source = \
            self._keyword_info and self._keyword_info.source or \
            self._find_keyword_source(context.datafile_controller)
        return self._find_occurrences_in(self._items_from(context))

    def _items_from(self, context):
        for df in context.datafiles:
            self._yield_for_other_threads()
            if self._items_from_datafile_should_be_checked(df):
                for item in self._items_from_datafile(df):
                    yield item

    def _items_from_datafile_should_be_checked(self, datafile):
        if datafile.filename and \
           os.path.basename(datafile.filename) == self._keyword_source:
            return True
        return self._find_keyword_source(datafile) == self._keyword_source

    def _items_from_datafile(self, df):
        for setting in df.settings:
            yield setting
        for test_items in (self._items_from_test(test) for test in df.tests):
            for item in test_items:
                yield item
        for kw_items in (self._items_from_keyword(kw) for kw in df.keywords):
            for item in kw_items:
                yield item

    def _items_from_keyword(self, kw):
        return chain([kw.keyword_name] if kw.source == self._keyword_source
                     else [], kw.steps, [kw.teardown] if kw.teardown else [])

    def _items_from_test(self, test):
        return chain(test.settings, test.steps)

    def _find_keyword_source(self, datafile_controller):
        item_info = datafile_controller.keyword_info(self._keyword_name)
        return item_info.source if item_info else None

    def _find_occurrences_in(self, items):
        return (Occurrence(item, self._keyword_name) for item in items
                if self._contains_item(item))

    def _contains_item(self, item):
        self._yield_for_other_threads()
        return item.contains_keyword(
            self._keyword_regexp or self._keyword_name)

    def _yield_for_other_threads(self):
        # GIL !?#!!!
        # THIS IS TO ENSURE THAT OTHER THREADS WILL GET SOME SPACE ALSO
        time.sleep(0)


class FindVariableOccurrences(FindOccurrences):

    @overrides(FindOccurrences)
    def _contains_item(self, item):
        self._yield_for_other_threads()
        return item.contains_variable(self._keyword_name)

    def _items_from_datafile(self, df):
        for itm in FindOccurrences._items_from_datafile(self, df):
            yield itm
        yield df.variables

    def _items_from_controller(self, ctrl):
        if isinstance(ctrl, TestCaseController):
            return self._items_from_test(ctrl)
        else:
            return self._items_from_keyword(ctrl)

    def _items_from_keyword(self, kw):
        return chain([kw.keyword_name], kw.steps, kw.settings)

    def _items_from(self, context):
        self._context = context
        if self._is_local_variable(self._keyword_name, context):
            for item in self._items_from_controller(context):
                yield item
        else:
            for df in context.datafiles:
                self._yield_for_other_threads()
                if self._items_from_datafile_should_be_checked(df):
                    for item in self._items_from_datafile(df):
                        yield item

    def _items_from_datafile_should_be_checked(self, datafile):
        if self._is_file_variable(self._keyword_name, self._context):
            return datafile in [self._context.datafile_controller] + \
                self._get_all_where_used(self._context)
        elif self._is_imported_variable(self._keyword_name, self._context):
            return datafile in [self._get_source_of_imported_var(
                                self._keyword_name, self._context)] + \
                self._get_all_where_used(self._get_source_of_imported_var(
                                         self._keyword_name, self._context))
        else:
            return True

    def _is_local_variable(self, name, context):
        if isinstance(context, VariableController):
            return False
        return name in context.get_local_variables() or \
            any(step.contains_variable_assignment(name)
                for step in context.steps)

    def _is_file_variable(self, name, context):
        return context.datafile_controller.variables.contains_variable(name)

    def _is_imported_variable(self, name, context):
        return self._get_source_of_imported_var(name, context) not in \
            [None, context.datafile_controller]

    def _is_builtin_variable(self, name):
        return name in list(_VariableStash.global_variables.keys())

    def _get_source_of_imported_var(self, name, context):
        for df in self._get_all_imported(context):
            if df.variables.contains_variable(name):
                return df
        return None

    def _get_all_imported(self, context):
        files = [context.datafile_controller]
        for f in files:
            files += [imp.get_imported_controller()
                      for imp in f.imports if imp.is_resource and
                      imp.get_imported_controller() not in files]
        return files

    def _get_all_where_used(self, context):
        files = [context.datafile_controller]
        for f in files:
            if isinstance(f, ResourceFileController):
                files += [imp.datafile_controller
                          for imp in f.get_where_used()]
        return files


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


class _AddDataFile(_Command):

    def __init__(self, path):
        self._path = path

    def execute(self, context):
        ctrl = self._add_data_file(context)
        context.notify_suite_added(ctrl)
        return ctrl

    def _add_data_file(self, context):
        raise NotImplementedError(self.__class__.__name__)


class AddTestCaseFile(_AddDataFile):

    def _add_data_file(self, context):
        return context.new_test_case_file(self._path)


class AddTestDataDirectory(_AddDataFile):

    def _add_data_file(self, context):
        return context.new_test_data_directory(self._path)


class CreateNewFileProject(_Command):

    def __init__(self, path):
        self._path = path

    def execute(self, context):
        context.new_file_project(self._path)


class CreateNewDirectoryProject(_Command):

    def __init__(self, path):
        self._path = path

    def execute(self, context):
        context.new_directory_project(self._path)


class SetFileFormat(_Command):

    def __init__(self, format):
        self._format = format

    def execute(self, context):
        context.save_with_new_format(self._format)


class SetFileFormatRecuresively(_Command):

    def __init__(self, format):
        self._format = format

    def execute(self, context):
        context.save_with_new_format_recursive(self._format)


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

    def __str__(self):
        return 'AddVariable("%s", "%s", "%s")' % \
            (self._name, self._value, self._comment)


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

    def _params(self):
        return (self._name, self._args, self._rows)

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
                            DeleteCells(
                                (row, col + 1), (row, col + len(cells) - 1)))


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
        self._undo_command = ChangeCellValue(
            self._row, self._col, step.get_value(self._col))
        step.change(self._col, self._value)
        self._step(context).remove_empty_columns_from_end()
        assert self._validate_postcondition(context),'Should have correct value after change'
        return True

    def _validate_postcondition(self, context):
        value = self._step(context).get_value(self._col).strip()
        should_be = self._value.strip()
        if value == should_be:
            return True
        return self._col == 0 and\
               (value.replace(' ', '') == 'FOR' and
                should_be.replace(' ', '') == 'FOR') or\
               (value.replace(' ', '') == 'FOR' and
                should_be.replace(' ', '').upper() == ':FOR') or\
               (value.replace(' ', '') == 'END' and
                should_be.replace(' ', '') == 'END')

    def _get_undo_command(self):
        return self._undo_command

    def __str__(self):
        return '%s(%s, %s, "%s")' % \
            (self.__class__.__name__, self._row, self._col, self._value)


class SaveFile(_Command):

    def execute(self, context):
        RideSaving(path=context.filename, datafile=context).publish()
        datafile_controller = context.datafile_controller
        for macro_controller in chain(
                datafile_controller.tests, datafile_controller.keywords):
            macro_controller.execute(Purify())
        datafile_controller.save()
        datafile_controller.unmark_dirty()
        RideSaved(path=context.filename).publish()


class SaveAll(_Command):

    def execute(self, context):
        for datafile_controller in context._get_all_dirty_controllers():
            if datafile_controller.has_format():
                datafile_controller.execute(SaveFile())
        RideSaveAll().publish()


class Purify(_Command):

    def execute(self, context):
        i = 0
        while True:
            if len(context.steps) <= i:
                break
            # Steps can changes during this operation
            # this is why index based iteration - step reference can be stale
            step = context.steps[i]
            step.remove_empty_columns_from_end()
            if step.has_only_comment():
                step.remove_empty_columns_from_beginning()
            i += 1
        context.execute(DeleteRows(context.get_empty_rows()))
        context.notify_steps_changed()


class InsertCell(_StepsChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def _params_str(self):
        return '%s, %s' % (self._row, self._col)

    def change_steps(self, context):
        self._step(context).shift_right(self._col)
        assert self._step(context).get_value(self._col) == '', \
            'Should have an empty value after insert'
        return True

    def _get_undo_command(self):
        return DeleteCell(self._row, self._col)


class DeleteCell(_StepsChangingCommand):

    def __init__(self, row, col):
        self._row = row
        self._col = col

    def _params(self):
        return (self._row, self._col)

    def change_steps(self, context):
        step = self._step(context)
        self._undo_command = StepsChangingCompositeCommand(
            InsertCell(self._row, self._col),
            ChangeCellValue(self._row, self._col,
                            step.get_value(self._col)))
        step.shift_left(self._col)
        return True

    def _get_undo_command(self):
        return self._undo_command


class _RowChangingCommand(_StepsChangingCommand):

    def __init__(self, row):
        '''Command that will operate on a given logical `row` of test/user keyword.

        Giving -1 as `row` means that operation is done on the last row.
        '''
        self._row = row

    def change_steps(self, context):
        if len(context.steps) <= self._row:
            return False
        self._change_value(context)
        return True

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self._row)


class DeleteRow(_RowChangingCommand):

    def _change_value(self, context):
        step = context.steps[self._row]
        self._undo_command = StepsChangingCompositeCommand(
            AddRow(self._row), PasteArea((self._row, 0), [step.as_list()]))
        context.remove_step(self._row)

    def _get_undo_command(self):
        if hasattr(self, '_undo_command'):
            return self._undo_command
        return AddRow(self._row)


class AddRow(_RowChangingCommand):

    def _change_value(self, context):
        row = self._row if self._row != -1 else len(context.steps)
        context.add_step(row)
        assert not(any(i for i in self._step(context).as_list() if i)), \
            'Should have an empty row after add instead %r' % \
            self._step(context).as_list()

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

    def _params(self):
        return [self._rows]

    def change_steps(self, context):
        if len(self._rows) == 0 or self._last_row > len(context.steps) - 1 or \
                self._first_row == 0:
            return False
        number_of_steps_before = len(context.steps)
        for row in self._rows:
            keep_indent = (context.steps[row].as_list()[0] == 'END' and  context.steps[row - 1].as_list()[0] == '')
            avoid_ident = (context.steps[row].as_list()[0] == 'FOR' and  context.steps[row - 1].as_list()[0] == 'END')
            new_indent = (context.steps[row - 1].as_list()[0] == 'END' and
                           context.steps[row].as_list()[0] != 'FOR')
            context.move_step_up(row)
            if avoid_ident:  # Special case FOR going up END
                context.steps[row].shift_left(0)
            if keep_indent:
                if not avoid_ident:
                    context.steps[row].shift_left(0)
                context.steps[row - 1].shift_left(0)  # END needs to be shifted too
            if new_indent:
                context.steps[row - 1].shift_right(0)
        assert len(context.steps) == number_of_steps_before
        return True

    @property
    def _last_row(self):
        return self._rows[-1]

    @property
    def _first_row(self):
        return self._rows[0]

    def _get_undo_command(self):
        return MoveRowsDown([r - 1 for r in self._rows if r > 0])


class MoveRowsDown(_StepsChangingCommand):

    def __init__(self, rows):
        self._rows = rows

    def _params(self):
        return [self._rows]

    def change_steps(self, context):
        if len(self._rows) == 0 or self._last_row >= len(context.steps) - 1:
            return False
        number_of_steps_before = len(context.steps)
        for row in reversed(self._rows):
            avoid_indent = False
            try:
                keep_indent = (context.steps[row].as_list()[0] == 'END' and context.steps[row-1].as_list()[0] == '')
                if context.steps[row].as_list()[0] == 'END' and context.steps[row+1].as_list()[0] == 'FOR':
                    keep_indent = False
                    avoid_indent = True  # Special case for END going after FOR
            except IndexError:
                keep_indent = False
            try:
                remove_indent = (context.steps[row].as_list()[0] == 'FOR' and context.steps[row+1].as_list()[1] == '')
            except IndexError:
                remove_indent = False
            if context.steps[row-1].as_list()[0] == 'FOR' and context.steps[row].as_list()[0] != '':  # Special case move after For
                keep_indent = True
            context.move_step_down(row)
            if avoid_indent and context.steps[row+1].as_list()[1] == 'END':
                context.steps[row+1].shift_left(0)
            if keep_indent:
                context.steps[row].shift_right(0)
            if remove_indent:
                context.steps[row].shift_left(0)
        assert len(context.steps) == number_of_steps_before
        return True

    @property
    def _last_row(self):
        return self._rows[-1]

    def _get_undo_command(self):
        return MoveRowsUp([r + 1 for r in self._rows])


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
        return [(cmd._execute(context), cmd._get_undo_command())
                for cmd in self._commands]


class StepsChangingCompositeCommand(_StepsChangingCommand, CompositeCommand):

    def __init__(self, *commands):
        self._commands = commands

    def change_steps(self, context):
        return any(changed
                   for changed in CompositeCommand._execute(self, context))

    def _get_undo_command(self):
        return self._undo_command

    def _create_undo_command(self, undos):
        return StepsChangingCompositeCommand(*undos)

    def _executions(self, context):
        return [(cmd.change_steps(context), cmd._get_undo_command())
                for cmd in self._commands]


def DeleteRows(rows):
    return StepsChangingCompositeCommand(*[DeleteRow(r)
                                         for r in reversed(sorted(rows))])


def AddRows(rows):
    # TODO: Refactor to use AddRows(_StepsChangingCommand) command
    first_row = sorted(rows)[0]
    return StepsChangingCompositeCommand(*[AddRow(first_row) for _ in rows])


def CommentRows(rows):
    return StepsChangingCompositeCommand(*[CommentRow(r) for r in rows])


def UncommentRows(rows):
    return StepsChangingCompositeCommand(*[UncommentRow(r) for r in rows])


def ClearArea(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(
        *[ChangeCellValue(row, col, '')
          for row in range(row_s, row_e + 1)
          for col in range(col_s, col_e + 1)])


def PasteArea(top_left, content):
    row_s, col_s = top_left
    return StepsChangingCompositeCommand(
        *[ChangeCellValue(row + row_s, col + col_s, content[row][col])
          for row in range(len(content))
          for col in range(len(content[row]))])


def InsertArea(top_left, content):
    row, _ = top_left
    return StepsChangingCompositeCommand(
        AddRows([row+i for i in range(len(content))]),
        PasteArea(top_left, content))


def _rows_from_selection(selection):
    res = []
    for row, col in selection:
        if row not in res:
            res += [row]
    return res


def _cols_from_selection(selection):
    res = []
    for row, col in selection:
        if col not in res:
            res += [col]
    return res


def InsertCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(
        *[InsertCell(row, col)
          for row in range(row_s, row_e + 1)
          for col in range(col_s, col_e + 1)])


def DeleteCells(top_left, bottom_right):
    row_s, col_s = top_left
    row_e, col_e = bottom_right
    return StepsChangingCompositeCommand(
        *[DeleteCell(row, col_s)
          for row in range(row_s, row_e + 1)
          for _ in range(col_s, col_e + 1)])
