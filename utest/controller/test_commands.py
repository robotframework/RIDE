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

import sys
import pathlib
import unittest
from robotide.controller.tags import DefaultTag
from robotide.controller.ctrlcommands import *
from robotide.editor.formatters import ListToStringFormatter

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
SCRIPT_DIR = os.path.dirname(pathlib.Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)

try:
    from base_command_test import TestCaseCommandTest  # .base_command_test
except ModuleNotFoundError:
    from .base_command_test import TestCaseCommandTest

try:
    from controller_creator import *
except ModuleNotFoundError:
    from .controller_creator import *


class UnmodifyingCommandsTest(unittest.TestCase):

    def test_unmodifying(self):
        self.assertFalse(FindOccurrences.modifying)


class FileHandlingCommandsTest(TestCaseCommandTest):

    def test_file_saving(self):
        self._file_saved = False
        self._exec(SaveFile())
        assert self._file_saved
        assert not self._ctrl.datafile_controller.dirty

    def test_file_saving_purifies(self):
        self._add_empty_step_to_macro()
        other_name = self._ctrl.name + 'foo'
        self._copy_macro_as(other_name)
        print(f"DEBUG: test_file_saving_purifies: before SaveFile")
        print(f"DEBUG: test_file_saving_purifies: steps: ")
        for i in self._ctrl.steps:
            print(f"{i.as_list()}")
        self._exec(SaveFile(reformat=True))
        print(f"DEBUG: test_file_saving_purifies: steps: ")
        for i in self._ctrl.steps:
            print(f"{i.as_list()}")
        assert len(self._ctrl.steps) == self._orig_number_of_steps + 1
        other = self._get_macro_by_name(other_name)
        assert len(other.steps) == self._orig_number_of_steps + 1

    def test_undo_after_file_save_does_not_break(self):
        self._exec(SaveFile())
        self._exec(Undo())

    def _add_empty_step_to_macro(self):
        self._exec(ChangeCellValue(self._orig_number_of_steps+1, 10, 'A'))
        self._verify_step_number_change(2)

    def _copy_macro_as(self, name):
        self._exec(CopyMacroAs(name))


class MacroCopyingTest(TestCaseCommandTest):

    def test_copy_macro(self):
        new_name = self._ctrl.name + '1'
        original_macro_number = len(self._get_macros())
        self._exec(CopyMacroAs(new_name))
        macro_names = [m.name for m in self._get_macros()]
        assert self._ctrl.name in macro_names
        assert new_name in macro_names
        assert len(macro_names) == original_macro_number+1
        assert (len(self._get_macro_by_name(new_name).steps) ==
                      len(self._ctrl.steps))

    def test_copy_does_not_change_original(self):
        new_name = self._ctrl.name + '2'
        self._exec(CopyMacroAs(new_name))
        copy = self._get_copy(new_name)
        copy.execute(ChangeCellValue(0, 0, 'Changed Step'))
        assert ['']+self._data_step_as_list(self._ctrl.steps[0].keyword) == self._data_step_as_list(STEP1_KEYWORD)
        assert copy.steps[0].keyword == 'Changed Step'

    def _get_copy(self,name):
        copies = [m for m in self._get_macros() if m.name == name]
        assert len(copies) == 1
        return copies[0]

    def test_copy_macro_inherits_default_tag(self):
        suite = self._ctrl.datafile_controller
        tag_name = 'konsukiepre'
        suite.default_tags.add(DefaultTag(tag_name))
        assert any(True for tag in self._ctrl.tags if tag.name == tag_name)
        new_name = self._ctrl.name + '3'
        self._exec(CopyMacroAs(new_name))
        assert any(True for tag in self._get_copy(new_name).tags if tag.name == tag_name)


class TestCaseEditingTest(TestCaseCommandTest):

    def test_changing_one_cell(self):
        self._exec(ChangeCellValue(0, 0, 'Changed Step'))
        assert self._steps[0].keyword == 'Changed Step'

    def test_changing_first_cell_in_for_loop_step(self):
        step_index = self._data_row(FOR_LOOP_STEP1)
        value = 'Foo'
        self._exec(ChangeCellValue(step_index, 1, value, insert=True))
        # for s in self._steps:
        #     print(f"{s.as_list()}")
        self.assertEqual(self._steps[step_index].as_list(),
                         ['', value] + self._data_step_as_list(FOR_LOOP_STEP1)[2:])

    def test_empty_second_cell_in_for_loop_step(self):
        step_index = self._data_row(FOR_LOOP_STEP1)
        value = ''
        self._exec(ChangeCellValue(step_index, 1, value))
        assert self._steps[step_index].as_list()[1] == value

    def test_undo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[1]
        changed_cell_value = 'Changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value))
        assert self._steps[0].keyword == changed_cell_value
        self._exec(Undo())
        assert self._steps[0].keyword == original_cell_value
        self._exec(Redo())
        assert self._steps[0].keyword == changed_cell_value

    def test_undo_when_nothing_to_undo(self):
        self._exec(Undo())
        assert self._number_of_test_changes == 0

    def test_redo_when_nothing_to_redo(self):
        self._exec(Redo())
        assert self._number_of_test_changes == 0

    def test_undo_undo_redo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[1]
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Again changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        assert self._steps[0].keyword == changed_cell_value_1
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        assert self._steps[0].keyword == changed_cell_value_2
        self._exec(Undo())
        assert self._steps[0].keyword == changed_cell_value_1
        self._exec(Undo())
        assert self._steps[0].keyword == original_cell_value
        self._exec(Redo())
        assert self._steps[0].keyword == changed_cell_value_1
        self._exec(Redo())
        assert self._steps[0].keyword == changed_cell_value_2

    def test_redo_does_nothing_after_state_changing_command_that_is_not_undo(self):
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Changed Step again'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        self._exec(Undo())
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        self._exec(Redo())
        assert self._steps[0].keyword == changed_cell_value_2

    def test_changing_cell_value_after_last_column_adds_empty_columns(self):
        self._exec(ChangeCellValue(0, 2, 'Hello'))
        assert self._steps[0].args == ['arg', 'Hello']

    def test_changing_cell_value_after_last_row_adds_empty_rows(self):
        self._exec(ChangeCellValue(len(self._data)+5, 0, 'Hello'))
        assert self._steps[len(self._data)+5].keyword == 'Hello'

    def test_changing_for_loop_header_value(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 0, 'Keyword'))
        assert (self._steps[self._data_row(FOR_LOOP_HEADER)].as_list() ==
                ['Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[2:])
        self._verify_step_unchanged(FOR_LOOP_STEP1)
        assert len(self._steps) == self._orig_number_of_steps

    def test_changing_for_loop_header_argument(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 1, 'Keyword'))
        assert (self._steps[self._data_row(FOR_LOOP_HEADER)].as_list() ==
                ['FOR', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[3:])
        self._verify_step_unchanged(FOR_LOOP_STEP1)
        assert len(self._steps) == self._orig_number_of_steps

    def test_changing_for_loop_header_in_clause(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 2, 'Keyword'))
        assert (self._steps[self._data_row(FOR_LOOP_HEADER)].as_list() ==
                ['FOR', '${i}', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[4:])
        assert self._steps[self._data_row(FOR_LOOP_STEP1)].as_list() == self._data_step_as_list(FOR_LOOP_STEP1[2:])
        # assert self._steps[self._data_row(FOR_LOOP_STEP1)].as_list() == self._data_step_as_list(FOR_LOOP_END[2:])
        assert len(self._steps) == self._orig_number_of_steps

    def test_deleting_row(self):
        self._exec(DeleteRow(0))
        self._verify_step_number_change(-1)
        self._verify_row_does_not_exist(STEP1)

    def test_undoing_row_delete(self):
        self._exec(DeleteRow(0))
        self._exec(Undo())
        assert len(self._steps) == self._orig_number_of_steps
        self._verify_step(0, 'Step 1', ['arg'])

    def test_delete_row_inside_of_for_loop(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_STEP1)))
        assert len(self._steps) == self._orig_number_of_steps-1
        self._verify_row_does_not_exist(FOR_LOOP_STEP1)

    def test_delete_for_loop_header_row(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_HEADER)))
        assert len(self._steps) == self._orig_number_of_steps-1
        self._verify_row_does_not_exist(FOR_LOOP_HEADER)

    def test_adding_row_last(self):
        self._exec(AddRow(-1))
        assert len(self._steps) == self._orig_number_of_steps+1
        assert self._steps[self._orig_number_of_steps].as_list() == []

    def test_adding_row_first(self):
        self._exec(AddRow(0))
        assert len(self._steps) == self._orig_number_of_steps+1
        assert self._steps[0].as_list() == []

    def test_adding_row_middle(self):
        self._exec(AddRow(1))
        assert len(self._steps) == self._orig_number_of_steps+1
        assert self._steps[1].as_list() == []

    def test_adding_row_in_for_loop_body(self):
        row_in_for_loop = self._data_row(FOR_LOOP_STEP2)
        self._exec(AddRow(row_in_for_loop))
        assert len(self._steps) == self._orig_number_of_steps+1
        assert self._steps[row_in_for_loop].as_list() == ['']

    def test_inserting_cell_when_for_loop_is_last(self):
        row_after_for_loop = self._data_row(STEP_AFTER_FOR_LOOP)
        self._exec(DeleteRow(row_after_for_loop))
        self._exec(DeleteRow(row_after_for_loop))
        assert self._steps[-1].as_list() == ['END']
        self._exec(InsertCell(0,0))
        self._verify_step(0, '', ['', 'Step 1', 'arg'])

    def test_add_multiple_rows(self):
        self._exec(add_rows([1, 2]))
        self._verify_step_number_change(2)
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step_is_empty(1)
        self._verify_step_is_empty(2)
        self._verify_step(3, 'Step 2', ['a1', 'a2', 'a3'])

    def test_undo_multiple_rows_add(self):
        self._exec(add_rows([3, 2, 1, 4, 5, 6, 9, 8, 7, 10]))
        self._exec(Undo())
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step(1, 'Step 2', ['a1', 'a2', 'a3'])

    def test_purify_removes_empty_rows(self):
        self._exec(AddRow(-1))
        self._exec(AddRow(1))
        self._exec(AddRow(2))
        assert len(self._steps) == self._orig_number_of_steps+3
        self._exec(Purify())
        assert len(self._steps) == self._orig_number_of_steps

    def test_purify_can_be_undone(self):
        self._exec(AddRow(1))
        self._exec(AddRow(2))
        assert len(self._steps) == self._orig_number_of_steps + 2
        ## print(f"DEBUG: before Purify {self.debug()}")
        print(f"DEBUG: before Purify")
        self._exec(Purify())
        assert len(self._steps) == self._orig_number_of_steps
        self._exec(Undo())
        assert len(self._steps) == self._orig_number_of_steps + 2

    def test_purify_removes_rows_with_no_data(self):
        self._exec(ChangeCellValue(0,0, ''))
        self._exec(ChangeCellValue(0,1, ''))
        self._exec(Purify())
        assert len(self._steps) == self._orig_number_of_steps - 1

    def test_can_add_values_to_empty_row(self):
        self._exec(AddRow(-1))
        self._exec(ChangeCellValue(0, 3, 'HELLO'))
        assert self._steps[0].args == ['arg', '', 'HELLO']

    def test__comment_is_kept_unchanged(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 0, ''))
        self._exec(Purify())
        assert self._steps[index].as_list() == ['', '# this is a comment']

    def test_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 1, '# new comment'))
        self._verify_step(index, 'Foo', [], '# new comment')

    def test_cell_value_after_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 2, 'something'))
        assert self._steps[index].as_list() == ['Foo', '# this is a comment', 'something']

    def test_change_keyword_value_in_indented_step(self):
        index = self._data_row(FOR_LOOP_STEP1)
        self._exec(ChangeCellValue(index, 1, 'Blog'))
        assert self._steps[index].keyword == 'Blog'
        assert len(self._steps) == self._orig_number_of_steps

    def test_delete_multiple_rows(self):
        self._exec(delete_rows([2, 0]))
        assert len(self._steps) == self._orig_number_of_steps-2
        self._verify_row_does_not_exist(STEP1)
        self._verify_row_does_not_exist(STEP_WITH_COMMENT)
        self._verify_number_of_test_changes(1)

    def test_deleting_rows_below_existing_steps_should_do_nothing(self):
        self._exec(delete_rows([1000, 960]))
        self._verify_number_of_test_changes(0)

    def test_inserting_rows_below_existing_steps_should_do_nothing(self):
        self._exec(add_rows([1001, 1002]))
        self._verify_number_of_test_changes(0)

    def test_clear_area(self):
        self._exec(clear_area((0, 1), (1, 2)))
        self._verify_step(0, 'Step 1')
        self._verify_step(1, 'Step 2', ['', '', 'a3'])

    def test_paste_area(self):
        self._exec(paste_area((0, 0), [['Changed Step 1', '', ''],
                                       ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2', 'a3'])

    def test_paste_area_different_length_rows(self):
        self._exec(paste_area((0, 0), [['Changed Step 1', '', '', '', '\t'],
                                       ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2', 'a3'])

    def test_insert_area_inserts_cells_before_selected_cell(self):
        self._exec(insert_area((0, 0), [['Changed Step 1', '', ''],
                                        ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2'])
        self._verify_step(2, 'Step 1', ['arg'])

    def test_insert_area_inserts_cells_before_selected_cell_different_length_rows(self):
        self._exec(insert_area((0, 0), [['Changed Step 1', '', '', '\t'],
                                        ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2'])
        self._verify_step(2, 'Step 1', ['arg'])

    def test_insert_cell(self):
        self._exec(insert_cells((0, 1), (0, 1)))
        self._verify_step(0, 'Step 1', ['', 'arg'])

    def test_inserting_cells_outside_step(self):
        self._exec(insert_cells((0, 10), (0, 10)))
        self._verify_step(0, 'Step 1', ['arg'])

    def test_insert_cell_before_comment(self):
        self._exec(insert_cells((2, 1), (2, 1)))
        self._verify_step(2, 'Foo', [''], exp_comment='# this is a comment')

    def test_inserting_many_cells(self):
        self._exec(insert_cells((0, 1), (1, 2)))
        self._verify_step(0, 'Step 1', ['', '', 'arg'])
        self._verify_step(1, 'Step 2', ['', '', 'a1', 'a2', 'a3'])

    def test_inserting_inside_for_step(self):
        self._exec(InsertCell(4,2))
        print(f"DEBUG: After insert cell, 4,2:")
        for s in self._steps:
            print(f"{s.as_list()}")
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                         self._data_step_as_list(FOR_LOOP_STEP1)[1:3] + ['']
                         + self._data_step_as_list(FOR_LOOP_STEP1)[3:])
        self._exec(InsertCell(4, 3))
        print(f"DEBUG: After insert cell, 4,3:")
        for s in self._steps:
            print(f"{s.as_list()}")
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                         self._data_step_as_list(FOR_LOOP_STEP1)[1:3] + ['']
                         + [''] + self._data_step_as_list(FOR_LOOP_STEP1)[3:])

    def test_deleting_inside_for_step(self):
        self._exec(DeleteCell(4,0))
        for s in self._steps:
            print(f"{s.as_list()}")
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                         self._data_step_as_list(FOR_LOOP_STEP1)[2:])
        self._exec(DeleteCell(4, 0))
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                         [self._data_step_as_list(FOR_LOOP_STEP1)[3]])

    def test_delete_many_cells(self):
        self._exec(delete_cells((0, 1), (1, 2)))
        self._verify_step(0, 'Step 1', [])
        self._verify_step(1, 'Step 2', ['a3'])

    def test_delete_cells_in_for_loop_and_undo(self):
        start_row = self._data_row(FOR_LOOP_STEP1)
        end_row = self._data_row(FOR_LOOP_STEP2)
        # print(f"DEBUG: test_delete_cells_in_for_loop_and_undo enter:")
        self._exec(delete_cells((start_row, 0), (end_row, 10)))
        for s in self._steps:
            print(f"{s.as_list()}")
        # FIXME
        assert self._steps[start_row].as_list() == []
        assert self._steps[end_row].as_list() == []
        self._exec(Undo())
        print(f"DEBUG: test_delete_cells_in_for_loop_and_undo AFTER Undo:")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._verify_steps_unchanged(FOR_LOOP_STEP1, FOR_LOOP_STEP2)  # FIXME

    def test_commenting(self):
        self._exec(comment_rows([0]))
        print(f"DEBUG: test_commenting AFTER CommentRows:")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._verify_step(0, 'Comment', ['Step 1', 'arg'])

    def test_commenting_many_rows(self):
        self._exec(comment_rows([1, 2, 3, 4]))
        for s in self._steps:
            print(f"{s.as_list()}")
        self.assertEqual(self._steps[self._data_row(STEP2)].as_list(), ['Comment'] + self._data_step_as_list(STEP2)[1:])
        self.assertEqual(self._steps[self._data_row(STEP_WITH_COMMENT)].as_list(), ['Comment'] + self._data_step_as_list(STEP_WITH_COMMENT)[1:])
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(), ['Comment'] + self._data_step_as_list(FOR_LOOP_HEADER)[1:])
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                         ['', 'Comment'] + self._data_step_as_list(FOR_LOOP_STEP1)[2:])

    def test_commenting_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        print(f"DEBUG: test_commenting_step_in_for_loop: BEFORE comment: {self._steps[row].as_list()}")
        self._exec(comment_rows([row]))
        # FIXME
        print(f"DEBUG: test_commenting_step_in_for_loop:  Changed={self._steps[row].as_list()}\n"
              f"original={self._data_step_as_list(FOR_LOOP_STEP1)}")
        assert self._steps[row].as_list() == ['', 'Comment'] + self._data_step_as_list(FOR_LOOP_STEP1)[2:]

    def test_commenting_for_loop_end(self):
        row = self._data_row(FOR_LOOP_END)
        print(f"DEBUG: test_commenting_for_loop_end: original row={BASE_DATA[row+1]}")
        self._exec(comment_rows([row]))
        print(f"DEBUG: test_commenting_for_loop_end: after CommentRows")
        # for s in self._steps:
        #    print(f"{s.as_list()}")
        print(f"DEBUG: test_commenting_for_loop_end: commented row={self._steps[row].as_list()}")
        assert (self._steps[row].as_list() ==
                ['Comment'] + self._data_step_as_list(FOR_LOOP_END)[1:])

    def test_uncommenting_single_row(self):
        self._exec(comment_rows([0]))
        self._exec(uncomment_rows([0]))
        assert self._steps[0].as_list() == self._data_step_as_list(STEP1)[1:]

    def test_uncommenting_row_with_variables(self):
        self._exec(ChangeCellValue(0, 0, "${var1}"))
        self._exec(ChangeCellValue(0, 1, "${var2}="))
        self._exec(ChangeCellValue(0, 2, "My Keyword"))
        self._exec(ChangeCellValue(0, 3, "${variable1}"))
        self._exec(ChangeCellValue(0, 4, "${variable2}"))
        # print(f"DEBUG: test_uncommenting_row_with_variables: initial row={self._steps[0].as_list()}")
        assert self._steps[0].as_list() == ["${var1}", "${var2}=", "My Keyword", "${variable1}", "${variable2}"]
        self._exec(comment_rows([0]))
        assert self._steps[0].as_list() == ["Comment", "${var1}", "${var2}=", "My Keyword", "${variable1}", "${variable2}"]
        self._exec(uncomment_rows([0]))
        # print(f"DEBUG: test_uncommenting_row_with_variables: commented row={self._steps[0].as_list()}")
        assert self._steps[0].as_list() == ["${var1}", "${var2}=", "My Keyword", "${variable1}", "${variable2}"]

    def test_uncommenting_row_with_triple_variables(self):
        # print(f"DEBUG: test_uncommenting_row_with_variables: ENTER initial row={self._steps[0].as_list()}")
        self._exec(ChangeCellValue(0, 0, "${var1}"))
        # print(f"DEBUG: test_uncommenting_row_with_variables: AFTER var1 change initial row={self._steps[0].as_list()}")
        self._exec(ChangeCellValue(0, 1, "${var2}"))
        # print(f"DEBUG: test_uncommenting_row_with_variables: AFTER var2 change initial row={self._steps[0].as_list()}")
        self._exec(ChangeCellValue(0, 2, "${var3}="))
        self._exec(ChangeCellValue(0, 3, "My Keyword"))
        self._exec(ChangeCellValue(0, 4, "${variable1}"))
        # print(f"DEBUG: test_uncommenting_row_with_variables: initial row={self._steps[0].as_list()}")
        assert self._steps[0].as_list() == ["${var1}", "${var2}", "${var3}=", "My Keyword", "${variable1}"]
        self._exec(comment_rows([0]))
        assert self._steps[0].as_list() == ["Comment", "${var1}", "${var2}", "${var3}=", "My Keyword", "${variable1}"]
        self._exec(uncomment_rows([0]))
        # print(f"DEBUG: test_uncommenting_row_with_variables: commented row={self._steps[0].as_list()}")
        assert self._steps[0].as_list() == ["${var1}", "${var2}", "${var3}=", "My Keyword", "${variable1}"]

    def test_commenting_row_with_for(self):
        print(f"DEBUG: Before CommentRow with FOR")
        self._exec(comment_rows([3]))
        print(f"DEBUG: After CommentRow with FOR")
        for s in self._steps:
            print(f"{s.as_list()}")
        assert (self._steps[3].as_list() ==
                ['Comment'] + self._data_step_as_list(FOR_LOOP_HEADER)[1:])
        assert (self._steps[4].as_list() ==
                self._data_step_as_list(FOR_LOOP_STEP1)[1:])

    def test_uncommenting_rows(self):
        self._exec(comment_rows([1, 2, 3, 4, 6]))
        print(f"DEBUG: After CommentRows")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._exec(uncomment_rows([1, 2, 3, 4, 6]))
        print(f"DEBUG: After UncommentRows")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._verify_steps_unchanged(STEP1, STEP2, STEP_WITH_COMMENT, FOR_LOOP_HEADER, FOR_LOOP_STEP1, FOR_LOOP_END)

    def test_uncommenting_commented_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        self._exec(comment_rows([row]))
        self._exec(uncomment_rows([row]))
        self._verify_step_unchanged(FOR_LOOP_STEP1)
        # assert_equal(self._steps[row].as_list(), self._data_step_as_list(FOR_LOOP_STEP1)[:])

    def test_uncommenting_does_nothing_if_not_commented(self):
        self._exec(uncomment_rows([1, 2, 3, 4, 6]))
        print(f"\nAfter UncommentRows")
        for row in self._steps:
            print(f"{row.as_list()}")
        self._verify_steps_unchanged(STEP2, STEP_WITH_COMMENT, FOR_LOOP_HEADER, FOR_LOOP_STEP1, FOR_LOOP_END)

    def test_commenting_and_uncommenting_row_with_no_step(self):
        self._exec(comment_rows([1000]))
        self._verify_number_of_test_changes(0)
        self._exec(uncomment_rows([10001]))
        self._verify_number_of_test_changes(0)

    def test_formatter(self):
        data = self._steps[self._data_row(FOR_LOOP_HEADER)]
        formatted = ListToStringFormatter(data).value
        assert formatted == "FOR | ${i} | IN | 1 | 2 | 3"


_TEST_WITH_TWO_FOR_LOOPS = ['Test With Two For Loops',
                            '  FOR  ${i}  IN  1  2',
                            '    Log  ${i}',
                            '  END',
                            '  FOR  ${j}  IN  1  2',
                            '    Log  ${j}',
                            '  END']


class ForLoopCases(TestCaseCommandTest):

    def _create_data(self):
        return _TEST_WITH_TWO_FOR_LOOPS[:]

    def test_remove_second_for_header(self):
        self._exec(delete_cells((3, 0), (3, 0)))
        self._verify_step(3, '', ['${j}', 'IN', '1', '2'])

    def test_remove_first_step_in_for_loop(self):
        print(f"Test data:")
        for el in _TEST_WITH_TWO_FOR_LOOPS:
            print(f"{el}")
        self._exec(delete_cells((1, 0), (1, 2)))
        print(f"Test After DeleteCells:")
        for el in self._ctrl.steps:
            print(f"{el.as_list()}")
        self._verify_step_unchanged('  FOR  ${i}  IN  1  2')
        self._verify_step(1, '')
        # self._verify_step_unchanged('    Log  ${i}')
        self._verify_step_unchanged('  FOR  ${j}  IN  1  2')
        self._verify_step_unchanged('    Log  ${j}')
        # self._verify_step(4, '', ['Log', '${j}'])
        self._verify_step(5, 'END')

    def test_remove_end_step_in_for_loop(self):
        self._exec(delete_cells((2, 0), (2, 1)))
        print(f"Test After DeleteCells:")
        for el in self._ctrl.steps:
            print(f"{el.as_list()}")
        self._verify_step_unchanged('  FOR  ${i}  IN  1  2')
        # self._verify_step(1, '', ['Log', '${i}'])
        self._verify_step_unchanged('    Log  ${i}')
        self._verify_step(2, '')
        self._verify_step_unchanged('  FOR  ${j}  IN  1  2')
        # self._verify_step(4, '', ['Log', '${j}'])
        self._verify_step_unchanged('    Log  ${j}')
        self._verify_step(5, 'END')
        # self._verify_step_unchanged('  END')


class SharpCommentTests(TestCaseCommandTest):  # DEBUG: on_comment_cells is called from kweditor

    def test_sharp_commenting_many_rows(self):
        self._exec(sharp_comment_rows([1, 2, 3, 4]))
        for s in self._steps:
            print(f"{s.as_list()}")
        step1 = ['# ' + self._data_step_as_list(STEP2)[1]] + self._data_step_as_list(STEP2)[2:]
        step2 = ['# ' + self._data_step_as_list(STEP_WITH_COMMENT)[1]] + self._data_step_as_list(STEP_WITH_COMMENT)[2:]
        step3 = ['# ' + self._data_step_as_list(FOR_LOOP_HEADER)[1]] + self._data_step_as_list(FOR_LOOP_HEADER)[2:]
        step4 = [''] + ['# ' + self._data_step_as_list(FOR_LOOP_STEP1)[2]] + self._data_step_as_list(FOR_LOOP_STEP1)[3:]
        self.assertEqual(self._steps[self._data_row(STEP2)].as_list(), step1)
        self.assertEqual(self._steps[self._data_row(STEP_WITH_COMMENT)].as_list(), step2)
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(), step3)
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(), step4)

    def test_sharp_uncommenting_many_rows(self):
        self._exec(sharp_comment_rows([1, 2, 3, 4]))
        for s in self._steps:
            print(f"{s.as_list()}")
        step1 = ['# ' + self._data_step_as_list(STEP2)[1]] + self._data_step_as_list(STEP2)[2:]
        step2 = ['# ' + self._data_step_as_list(STEP_WITH_COMMENT)[1]] + self._data_step_as_list(STEP_WITH_COMMENT)[2:]
        step3 = ['# ' + self._data_step_as_list(FOR_LOOP_HEADER)[1]] + self._data_step_as_list(FOR_LOOP_HEADER)[2:]
        step4 = [''] + ['# ' + self._data_step_as_list(FOR_LOOP_STEP1)[2]] + self._data_step_as_list(FOR_LOOP_STEP1)[3:]
        self.assertEqual(self._steps[self._data_row(STEP2)].as_list(), step1)
        self.assertEqual(self._steps[self._data_row(STEP_WITH_COMMENT)].as_list(), step2)
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(), step3)
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(), step4)
        self._exec(sharp_uncomment_rows([1, 2, 3, 4]))
        for s in self._steps:
            print(f"{s.as_list()}")
        self.assertEqual(self._steps[self._data_row(STEP2)].as_list(), self._data_step_as_list(STEP2)[1:])
        self.assertEqual(self._steps[self._data_row(STEP_WITH_COMMENT)].as_list(), self._data_step_as_list(STEP_WITH_COMMENT)[1:])
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(), self._data_step_as_list(FOR_LOOP_HEADER)[1:])
        self.assertEqual(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(), self._data_step_as_list(FOR_LOOP_STEP1)[1:])


class RowMovingTest(TestCaseCommandTest):

    def test_row_up(self):
        result = self._exec(MoveRowsUp([1]))
        assert result
        self._assert_step_order(STEP2, STEP1)

    def test_first_row_up_does_nothing(self):
        result = self._exec(MoveRowsUp([0]))
        assert not result
        assert self._number_of_test_changes == 0
        self._exec(Undo())
        self._exec(Redo())

    def test_moving_block_containing_first_row_up_does_nothing(self):
        self._exec(MoveRowsUp([0,1,2]))
        assert self._number_of_test_changes == 0

    def test_move_for_loop_header_up(self):
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_HEADER)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)

    def test_move_step1_in_for_loop_header_up(self):
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_STEP1)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)

    def test_move_down_step_before_for_loop_header(self):
        self._exec(MoveRowsDown([self._data_row(STEP_WITH_COMMENT)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)

    def test_move_up_step_after_for_loop(self):
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_STEP2,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END)

    def test_move_down_last_step_in_for_loop(self):
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_STEP2)]))
        print(f"DEBUG: After MoveRowsDown last step in for loop")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)

    def test_move_down_for_loop_header(self):
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER)]))
        print(f"DEBUG: After MoveRowsDown for loop header")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)

    def test_move_down_loop_end(self):
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_END)]))
        print(f"DEBUG: After MoveRowsDown for loop end")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_STEP2,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END)

    def test_move_up_for_loop_end(self):
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END)]))
        print(f"\nDEBUG: test_move_up_for_loop_end result:")
        for s in self._steps:
            print(s.as_list())
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)

    def test_move_up_and_down_step_in_for_loop(self):
        def str_step(row):
            sep = '  '
            for idx in range(1, len(row)):
                if row[idx] == '':
                    row[idx] = sep
            st = sep.join(row)
            return st
        # TODO Break this test into several
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_STEP1)]))
        # print(f"\nDEBUG: test_move_up_and_down_step_in_for_loop result:")
        for s in self._steps:
            print(s.as_list())
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END)
        print("after assert1")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row+1])
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END)
        print("after assert2")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            print("%s" % self._data[row+1])
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        # print(f"\nDEBUG: test_move_up_and_down_step_in_for_loop result:")
        for s in self._steps:
            print(s.as_list())
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END)
        print("after assert3")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row+1])
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END)
        """
        print("after assert4")
        # for row in range(0, len(self._steps)):
        #    self._data[row+1] = str_step(self._steps[row].as_list())
        #    # print("%s" % self._data[row+1])
        self._exec(MoveRowsDown([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_STEP1[2:])]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP1[2:]
                                )
        print("after assert5")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row+1])
        # for row in range(0, len(self._steps)):
        #     print("%s" % self._steps[row])   # Show types
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_HEADER[2:])]))
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                '  ' + FOR_LOOP_END,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1[2:]
                                )
        print("after assert6")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            print("%s" % self._data[row+1])
        self._exec(MoveRowsUp([self._data_row(STEP1[2:])]))
        self._exec(MoveRowsUp([self._data_row(STEP2[2:])]))
        self._exec(MoveRowsUp([self._data_row('    ' + FOR_LOOP_END)]))
        # FIXME
        self._assert_step_order(STEP2,
                                STEP1,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                '  ' + FOR_LOOP_END,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1[2:]
                                )
        print("after assert7")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row + 1])
        self._exec(MoveRowsDown([self._data_row(STEP2[2:])]))
        self._exec(MoveRowsDown([self._data_row('    ' + FOR_LOOP_END)]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER[2:])]))
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                '  ' +FOR_LOOP_END,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1[2:]
                                )
        # print("after assert8")
        # for row in range(0, len(self._steps)):
        #     self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])
        # print(f"\nDEBUG: test_move_up_and_down_step_in_for_loop FINAL result:")
        for s in self._steps:
            print(s.as_list())
        """

    def test_move_down_for_loop_header_after_end(self):
        def str_step(row):
            sep = '  '
            for idx in range(1, len(row)):
                if row[idx] == '':
                    row[idx] = sep
            st = sep.join(row)
            return st
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER)]))
        # print("DEBUG: after move loop 1")
        # or row in range(0, len(self._steps)):
        #    self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop 1 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER[2:])]))
        print("DEBUG: after move loop before END")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_STEP2[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop 2 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER[2:])]))
        # print("DEBUG: after move loop after END")
        # for row in range(0, len(self._steps)):
        #     self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_STEP2[2:],
                                FOR_LOOP_END,
                                FOR_LOOP_HEADER,
                                STEP_AFTER_FOR_LOOP)

    def test_move_down_end_after_loop_header(self):
        def str_step(row):
            sep = '  '
            for idx in range(1, len(row)):
                if row[idx] == '':
                    row[idx] = sep
            st = sep.join(row)
            return st
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER)]))
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row + 1])
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_END,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row + 1])
        # Actual test
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_END[2:])]))
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)

    def test_move_up_loop_header_after_end(self):
        def str_step(row):
            sep = '  '
            for idx in range(1, len(row)):
                if row[idx] == '':
                    row[idx] = sep
            st = sep.join(row)
            return st
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER)]))
        # print("DEBUG: after move down for")
        # for s in self._steps:
        #     print(f"{s.as_list()}")
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END)]))
        # print("DEBUG: after move for end 1")
        # for row in range(0, len(self._steps)):
        #     self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        """       
        print("DEBUG: after move loop for 1 assertion")
        # for row in range(0, len(self._steps)):
        #    self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END)]))
        print("DEBUG: after move loop for 2")
        # for row in range(0, len(self._steps)):
            # self._data[row + 1] = str_step(self._steps[row].as_list())
            #print("%s" % self._data[row + 1])
        #    print("%s" % self._steps[row].as_list())
        # FIXME
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_END,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        print("DEBUG: after move loop for 2 assertion")
        # for row in range(0, len(self._steps)):
        #     self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])
        # Actual test
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_HEADER[2:])]))
        # print("DEBUG: after move loop for test")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                '  ' + FOR_LOOP_END,
                                FOR_LOOP_STEP2,
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop for test assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        """

    def test_undo_row_up(self):
        self._exec(MoveRowsUp([1]))
        self._exec(Undo())
        self._assert_step_order(STEP1, STEP2)

    def test_moving_rows(self):
        self._exec(MoveRowsUp([1, 2]))
        self._assert_step_order(STEP2, STEP_WITH_COMMENT, STEP1)

    def test_undoing_moving_rows(self):
        self._exec(MoveRowsUp([1, 2]))
        self._exec(Undo())
        self._assert_step_order(STEP1, STEP2, STEP_WITH_COMMENT)

    def test_move_row_down(self):
        self._exec(MoveRowsDown([0]))
        print(f"DEBUG: After MoveRowsDown single 0")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._assert_step_order(STEP2, STEP1)

    def test_undo_move_row_down(self):
        self._exec(MoveRowsDown([0]))
        self._exec(Undo())
        self._assert_step_order(STEP1, STEP2)

    def test_move_rows_down(self):
        self._exec(MoveRowsDown([0,1]))
        print(f"DEBUG: After MoveRowsDown two 0 and 1")
        for s in self._steps:
            print(f"{s.as_list()}")
        self._assert_step_order(STEP_WITH_COMMENT, STEP1, STEP2)

    def _assert_step_order(self, *steps):
        for idx, step in enumerate(steps):
            row = self._steps[idx].as_list()
            # if row and row[0] != '':
            #    row = [''] + row
            assert ([''] + row ==
                         self._data_step_as_list(step))
        assert self._ctrl.dirty


if __name__ == "__main__":
    unittest.main()
