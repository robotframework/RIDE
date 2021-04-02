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
import unittest
from nose.tools import assert_true, assert_false, assert_equal
from robotide.controller.tags import DefaultTag
from robotide.controller.ctrlcommands import *

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from base_command_test import TestCaseCommandTest
# from .controller_creator import *
from controller_creator import *


class UnmodifyingCommandsTest(unittest.TestCase):

    def test_unmodifying(self):
        self.assertFalse(FindOccurrences.modifying)


class FileHandlingCommandsTest(TestCaseCommandTest):

    def test_file_saving(self):
        self._file_saved = False
        self._exec(SaveFile())
        assert_true(self._file_saved)
        assert_false(self._ctrl.datafile_controller.dirty)

    def test_file_saving_purifies(self):
        self._add_empty_step_to_macro()
        other_name = self._ctrl.name + 'foo'
        self._copy_macro_as(other_name)
        self._exec(SaveFile())
        assert_equal(len(self._ctrl.steps), self._orig_number_of_steps+1)
        other = self._get_macro_by_name(other_name)
        assert_equal(len(other.steps), self._orig_number_of_steps+1)

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
        assert_true(self._ctrl.name in macro_names)
        assert_true(new_name in macro_names)
        assert_equal(len(macro_names), original_macro_number+1)
        assert_equal(len(self._get_macro_by_name(new_name).steps),
                      len(self._ctrl.steps))

    def test_copy_does_not_change_original(self):
        new_name = self._ctrl.name + '2'
        self._exec(CopyMacroAs(new_name))
        copy = self._get_copy(new_name)
        copy.execute(ChangeCellValue(0, 0, 'Changed Step'))
        assert_equal(self._ctrl.steps[0].keyword, STEP1_KEYWORD)
        assert_equal(copy.steps[0].keyword, 'Changed Step')

    def _get_copy(self,name):
        copies = [m for m in self._get_macros() if m.name == name]
        assert_equal(len(copies), 1)
        return copies[0]

    def test_copy_macro_inherits_default_tag(self):
        suite = self._ctrl.datafile_controller
        tag_name = 'konsukiepre'
        suite.default_tags.add(DefaultTag(tag_name))
        assert_true(any(True for tag in self._ctrl.tags if tag.name == tag_name))
        new_name = self._ctrl.name + '3'
        self._exec(CopyMacroAs(new_name))
        assert_true(any(True for tag in self._get_copy(new_name).tags if tag.name == tag_name))


class TestCaseEditingTest(TestCaseCommandTest):

    def test_changing_one_cell(self):
        self._exec(ChangeCellValue(0, 0, 'Changed Step'))
        assert_equal(self._steps[0].keyword, 'Changed Step')

    def test_changing_first_cell_in_for_loop_step(self):
        step_index = self._data_row(FOR_LOOP_STEP1)
        value = 'Foo'
        self._exec(ChangeCellValue(step_index, 0, value))
        assert_equal(self._steps[step_index].as_list()[0], value)

    def test_empty_second_cell_in_for_loop_step(self):
        step_index = self._data_row(FOR_LOOP_STEP1)
        value = ''
        self._exec(ChangeCellValue(step_index, 1, value))
        assert_equal(self._steps[step_index].as_list()[1], value)

    def test_undo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[0]
        changed_cell_value = 'Changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value))
        assert_equal(self._steps[0].keyword, changed_cell_value)
        self._exec(Undo())
        assert_equal(self._steps[0].keyword, original_cell_value)
        self._exec(Redo())
        assert_equal(self._steps[0].keyword, changed_cell_value)

    def test_undo_when_nothing_to_undo(self):
        self._exec(Undo())
        assert_equal(self._number_of_test_changes, 0)

    def test_redo_when_nothing_to_redo(self):
        self._exec(Redo())
        assert_equal(self._number_of_test_changes, 0)

    def test_undo_undo_redo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[0]
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Again changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        assert_equal(self._steps[0].keyword, changed_cell_value_1)
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        assert_equal(self._steps[0].keyword, changed_cell_value_2)
        self._exec(Undo())
        assert_equal(self._steps[0].keyword, changed_cell_value_1)
        self._exec(Undo())
        assert_equal(self._steps[0].keyword, original_cell_value)
        self._exec(Redo())
        assert_equal(self._steps[0].keyword, changed_cell_value_1)
        self._exec(Redo())
        assert_equal(self._steps[0].keyword, changed_cell_value_2)

    def test_redo_does_nothing_after_state_changing_command_that_is_not_undo(self):
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Changed Step again'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        self._exec(Undo())
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        self._exec(Redo())
        assert_equal(self._steps[0].keyword, changed_cell_value_2)

    def test_changing_cell_value_after_last_column_adds_empty_columns(self):
        self._exec(ChangeCellValue(0, 2, 'Hello'))
        assert_equal(self._steps[0].args, ['arg', 'Hello'])

    def test_changing_cell_value_after_last_row_adds_empty_rows(self):
        self._exec(ChangeCellValue(len(self._data)+5, 0, 'Hello'))
        assert_equal(self._steps[len(self._data)+5].keyword, 'Hello')

    def test_changing_for_loop_header_value(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 0, 'Keyword'))
        assert_equal(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      ['Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[1:])
        self._verify_step_unchanged(FOR_LOOP_STEP1)
        assert_equal(len(self._steps), self._orig_number_of_steps)

    def test_changing_for_loop_header_argument(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 1, 'Keyword'))
        assert_equal(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      ['FOR', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[2:])
        self._verify_step_unchanged(FOR_LOOP_STEP1)
        assert_equal(len(self._steps), self._orig_number_of_steps)

    def test_changing_for_loop_header_in_clause(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 2, 'Keyword'))
        assert_equal(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      ['FOR', '${i}', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[3:])
        assert_equal(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                      self._data_step_as_list(FOR_LOOP_STEP1))
        assert_equal(len(self._steps), self._orig_number_of_steps)

    def test_deleting_row(self):
        self._exec(DeleteRow(0))
        self._verify_step_number_change(-1)
        self._verify_row_does_not_exist(STEP1)

    def test_undoing_row_delete(self):
        self._exec(DeleteRow(0))
        self._exec(Undo())
        assert_equal(len(self._steps), self._orig_number_of_steps)
        self._verify_step(0, 'Step 1', ['arg'])

    def test_delete_row_inside_of_for_loop(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_STEP1)))
        assert_equal(len(self._steps), self._orig_number_of_steps-1)
        self._verify_row_does_not_exist(FOR_LOOP_STEP1)

    def test_delete_for_loop_header_row(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_HEADER)))
        assert_equal(len(self._steps), self._orig_number_of_steps-1)
        self._verify_row_does_not_exist(FOR_LOOP_HEADER)

    def test_adding_row_last(self):
        self._exec(AddRow(-1))
        assert_equal(len(self._steps), self._orig_number_of_steps+1)
        assert_equal(self._steps[self._orig_number_of_steps].as_list(), [])

    def test_adding_row_first(self):
        self._exec(AddRow(0))
        assert_equal(len(self._steps), self._orig_number_of_steps+1)
        assert_equal(self._steps[0].as_list(), [])

    def test_adding_row_middle(self):
        self._exec(AddRow(1))
        assert_equal(len(self._steps), self._orig_number_of_steps+1)
        assert_equal(self._steps[1].as_list(), [])

    def test_adding_row_in_for_loop_body(self):
        row_in_for_loop = self._data_row(FOR_LOOP_STEP2)
        self._exec(AddRow(row_in_for_loop))
        assert_equal(len(self._steps), self._orig_number_of_steps+1)
        assert_equal(self._steps[row_in_for_loop].as_list(), [''])

    def test_inserting_cell_when_for_loop_is_last(self):
        row_after_for_loop = self._data_row(STEP_AFTER_FOR_LOOP)
        self._exec(DeleteRow(row_after_for_loop))
        self._exec(DeleteRow(row_after_for_loop))
        assert_equal(self._steps[-1].as_list(), ['END'])
        self._exec(InsertCell(0,0))
        self._verify_step(0, '', ['Step 1', 'arg'])

    def test_add_multiple_rows(self):
        self._exec(AddRows([1,2]))
        self._verify_step_number_change(2)
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step_is_empty(1)
        self._verify_step_is_empty(2)
        self._verify_step(3, 'Step 2', ['a1', 'a2', 'a3'])

    def test_undo_multiple_rows_add(self):
        self._exec(AddRows([3,2,1,4,5,6,9,8,7,10]))
        self._exec(Undo())
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step(1, 'Step 2', ['a1', 'a2', 'a3'])

    def test_purify_removes_empty_rows(self):
        self._exec(AddRow(-1))
        self._exec(AddRow(1))
        self._exec(AddRow(2))
        assert_equal(len(self._steps), self._orig_number_of_steps+3)
        self._exec(Purify())
        assert_equal(len(self._steps), self._orig_number_of_steps)

    def test_purify_can_be_undone(self):
        self._exec(AddRow(1))
        self._exec(AddRow(2))
        assert_equal(len(self._steps), self._orig_number_of_steps+2)
        self._exec(Purify())
        assert_equal(len(self._steps), self._orig_number_of_steps)
        self._exec(Undo())
        assert_equal(len(self._steps), self._orig_number_of_steps+2)

    def test_purify_removes_rows_with_no_data(self):
        self._exec(ChangeCellValue(0,0, ''))
        self._exec(ChangeCellValue(0,1, ''))
        self._exec(Purify())
        assert_equal(len(self._steps), self._orig_number_of_steps-1)

    def test_can_add_values_to_empty_row(self):
        self._exec(AddRow(-1))
        self._exec(ChangeCellValue(0, 3, 'HELLO'))
        assert_equal(self._steps[0].args, ['arg', '', 'HELLO'])

    def test_only_comment_is_left(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 0, ''))
        self._exec(Purify())
        assert_equal(self._steps[index].as_list(), ['# this is a comment'])

    def test_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 1, '# new comment'))
        self._verify_step(index, 'Foo', [], '# new comment')

    def test_cell_value_after_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 2, 'something'))
        assert_equal(self._steps[index].as_list(), ['Foo', '# this is a comment', 'something'])

    def test_change_keyword_value_in_indented_step(self):
        index = self._data_row(FOR_LOOP_STEP1)
        self._exec(ChangeCellValue(index, 1, 'Blog'))
        assert_equal(self._steps[index].keyword, 'Blog')
        assert_equal(len(self._steps), self._orig_number_of_steps)

    def test_delete_multiple_rows(self):
        self._exec(DeleteRows([2,0]))
        assert_equal(len(self._steps), self._orig_number_of_steps-2)
        self._verify_row_does_not_exist(STEP1)
        self._verify_row_does_not_exist(STEP_WITH_COMMENT)
        self._verify_number_of_test_changes(1)

    def test_deleting_rows_below_existing_steps_should_do_nothing(self):
        self._exec(DeleteRows([1000, 960]))
        self._verify_number_of_test_changes(0)

    def test_inserting_rows_below_existing_steps_should_do_nothing(self):
        self._exec(AddRows([1001, 1002]))
        self._verify_number_of_test_changes(0)

    def test_clear_area(self):
        self._exec(ClearArea((0,1), (1,2)))
        self._verify_step(0, 'Step 1')
        self._verify_step(1, 'Step 2', ['', '', 'a3'])

    def test_paste_area(self):
        self._exec(PasteArea((0, 0), [['Changed Step 1', '', ''],
                                      ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2', 'a3'])

    def test_paste_area_different_length_rows(self):
        self._exec(PasteArea((0, 0), [['Changed Step 1', '', '', '', '\t'],
            ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2', 'a3'])

    def test_insert_area_inserts_cells_before_selected_cell(self):
        self._exec(InsertArea((0, 0), [['Changed Step 1', '', ''],
                                      ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2'])
        self._verify_step(2, 'Step 1', ['arg'])

    def test_insert_area_inserts_cells_before_selected_cell_different_length_rows(self):
        self._exec(InsertArea((0, 0), [['Changed Step 1', '', '', '\t'],
            ['Changed Step 2', '', 'ca2']]))
        self._verify_step(0, 'Changed Step 1')
        self._verify_step(1, 'Changed Step 2', ['', 'ca2'])
        self._verify_step(2, 'Step 1', ['arg'])

    def test_insert_cell(self):
        self._exec(InsertCells((0,1), (0,1)))
        self._verify_step(0, 'Step 1', ['', 'arg'])

    def test_inserting_cells_outside_step(self):
        self._exec(InsertCells((0,10), (0,10)))
        self._verify_step(0, 'Step 1', ['arg'])

    def test_insert_cell_before_comment(self):
        self._exec(InsertCells((2,1), (2,1)))
        self._verify_step(2, 'Foo', [''], exp_comment='# this is a comment')

    def test_inserting_many_cells(self):
        self._exec(InsertCells((0,1), (1,2)))
        self._verify_step(0, 'Step 1', ['', '', 'arg'])
        self._verify_step(1, 'Step 2', ['', '', 'a1', 'a2', 'a3'])

    def test_delete_many_cells(self):
        self._exec(DeleteCells((0,1), (1,2)))
        self._verify_step(0, 'Step 1', [])
        self._verify_step(1, 'Step 2', ['a3'])

    def test_delete_cells_in_for_loop_and_undo(self):
        start_row = self._data_row(FOR_LOOP_STEP1)
        end_row = self._data_row(FOR_LOOP_STEP2)
        self._exec(DeleteCells((start_row, 1), (end_row, 10)))
        assert_equal(self._steps[start_row].as_list(), [''])
        assert_equal(self._steps[end_row].as_list(), [''])
        self._exec(Undo())
        self._verify_steps_unchanged(FOR_LOOP_STEP1, FOR_LOOP_STEP2)

    def test_commenting(self):
        self._exec(CommentRows([0]))
        self._verify_step(0, 'Comment', ['Step 1', 'arg'])

    def test_commenting_many_rows(self):
        self._exec(CommentRows([1,2,3,4]))
        for row_data in [STEP2, STEP_WITH_COMMENT, FOR_LOOP_HEADER, FOR_LOOP_STEP1]:
            assert_equal(self._steps[self._data_row(row_data)].as_list(),
                          ['Comment'] + self._data_step_as_list(row_data))

    def test_commenting_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        self._exec(CommentRows([row]))
        assert_equal(self._steps[row].as_list(),
                      ['', 'Comment'] + self._data_step_as_list(FOR_LOOP_STEP1)[1:])

    def test_commenting_for_loop_end(self):
        row = self._data_row(FOR_LOOP_END)
        self._exec(CommentRows([row]))
        assert_equal(self._steps[row].as_list(),
                      ['Comment'] + self._data_step_as_list(FOR_LOOP_END)[:])

    def test_uncommenting_single_row(self):
        self._exec(CommentRows([0]))
        self._exec(UncommentRows([0]))
        assert_equal(self._steps[0].as_list(), self._data_step_as_list(STEP1))

    def test_uncommenting_rows(self):
        self._exec(CommentRows([1,2,3,4,6]))
        self._exec(UncommentRows([1,2,3,4,6]))
        self._verify_steps_unchanged(STEP2, STEP_WITH_COMMENT, FOR_LOOP_HEADER, FOR_LOOP_STEP1, FOR_LOOP_END)

    def test_uncommenting_commented_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        self._exec(CommentRows([row]))
        self._exec(UncommentRows([row]))
        self._verify_step_unchanged(FOR_LOOP_STEP1)

    def test_uncommenting_does_nothing_if_not_commented(self):
        self._exec(UncommentRows([1,2,3,4,6]))
        self._verify_steps_unchanged(STEP2, STEP_WITH_COMMENT, FOR_LOOP_HEADER, FOR_LOOP_STEP1, FOR_LOOP_END)

    def test_commenting_and_uncommenting_row_with_no_step(self):
        self._exec(CommentRows([1000]))
        self._verify_number_of_test_changes(0)
        self._exec(UncommentRows([10001]))
        self._verify_number_of_test_changes(0)


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
        self._exec(DeleteCells((3,0), (3,0)))
        self._verify_step(3, '${j}', ['IN', '1', '2'])

    def test_remove_first_step_in_for_loop(self):
        self._exec(DeleteCells((1,1), (1,2)))
        self._verify_step_unchanged('  FOR  ${i}  IN  1  2')
        self._verify_step(1, '')
        self._verify_step_unchanged('  FOR  ${j}  IN  1  2')
        self._verify_step_unchanged('    Log  ${j}')
        self._verify_step_unchanged('  END')

    def test_remove_end_step_in_for_loop(self):
        self._exec(DeleteCells((2,0), (2,0)))
        self._verify_step_unchanged('  FOR  ${i}  IN  1  2')
        self._verify_step_unchanged('    Log  ${i}')
        self._verify_step_unchanged('    Log  ${j}')
        self._verify_step_unchanged('  FOR  ${j}  IN  1  2')


class RowMovingTest(TestCaseCommandTest):

    def test_row_up(self):
        result = self._exec(MoveRowsUp([1]))
        assert_true(result)
        self._assert_step_order(STEP2, STEP1)

    def test_first_row_up_does_nothing(self):
        result = self._exec(MoveRowsUp([0]))
        assert_true(not result)
        assert_equal(self._number_of_test_changes, 0)
        self._exec(Undo())
        self._exec(Redo())

    def test_moving_block_containing_first_row_up_does_nothing(self):
        self._exec(MoveRowsUp([0,1,2]))
        assert_equal(self._number_of_test_changes, 0)

    def test_move_for_loop_header_up(self):
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_HEADER)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                FOR_LOOP_HEADER,
                                '  '+STEP_WITH_COMMENT,
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
                                '  '+STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP)

    def test_move_up_step_after_for_loop(self):
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
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
        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_STEP1)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END)
        # print("after assert1")
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
        # print("after assert2")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row+1])

        self._exec(MoveRowsUp([self._data_row(STEP_AFTER_FOR_LOOP)]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP2,
                                FOR_LOOP_STEP1,
                                FOR_LOOP_END)
        # print("after assert3")
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
        # print("after assert4")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
            # print("%s" % self._data[row+1])

        self._exec(MoveRowsDown([self._data_row(STEP_AFTER_FOR_LOOP[2:])]))
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
        # print("after assert5")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row+1])
        # for row in range(0, len(self._steps)):
        #     print("%s" % self._steps[row])   # Show types

        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_HEADER[2:])]))
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        self._assert_step_order(STEP1,
                                STEP2,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                FOR_LOOP_STEP1[2:]
                                )
        # print("after assert6")
        for row in range(0, len(self._steps)):
            self._data[row+1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row+1])

        self._exec(MoveRowsUp([self._data_row(STEP1[2:])]))
        self._exec(MoveRowsUp([self._data_row(STEP2[2:])]))
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        self._assert_step_order(STEP2,
                                STEP1,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_WITH_COMMENT,
                                FOR_LOOP_END,
                                STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_STEP2[2:],
                                FOR_LOOP_STEP1[2:]
                                )
        # print("after assert7")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])

        self._exec(MoveRowsDown([self._data_row(STEP2[2:])]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_END[2:])]))
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER[2:])]))
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_HEADER,
                                '  ' + STEP_AFTER_FOR_LOOP,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                FOR_LOOP_STEP1[2:]
                                )
        # print("after assert8")
        # for row in range(0, len(self._steps)):
        #     self._data[row + 1] = str_step(self._steps[row].as_list())
        #     print("%s" % self._data[row + 1])

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
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
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
        #print("DEBUG: after move loop before END")
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
        # print("DEBUG: after move loop end 1")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop end 1 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        # print("DEBUG: after move loop end 2")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_END,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop end 2 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

        # Actual test
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_END[2:])]))
        # print("DEBUG: after move loop end test")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop end test assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

    def test_move_up_loop_header_after_end(self):
        def str_step(row):
            sep = '  '
            for idx in range(1, len(row)):
                if row[idx] == '':
                    row[idx] = sep
            st = sep.join(row)
            return st
        self._exec(MoveRowsDown([self._data_row(FOR_LOOP_HEADER)]))
        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END)]))
        # print("DEBUG: after move for end 1")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_HEADER,
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop for 1 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

        self._exec(MoveRowsUp([self._data_row(FOR_LOOP_END[2:])]))
        # print("DEBUG: after move loop for 2")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])
        self._assert_step_order(STEP1,
                                STEP2,
                                STEP_WITH_COMMENT,
                                FOR_LOOP_STEP1[2:],
                                FOR_LOOP_END,
                                FOR_LOOP_HEADER,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop for 2 assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

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
                                FOR_LOOP_END,
                                FOR_LOOP_STEP2[2:],
                                STEP_AFTER_FOR_LOOP)
        # print("DEBUG: after move loop for test assertion")
        for row in range(0, len(self._steps)):
            self._data[row + 1] = str_step(self._steps[row].as_list())
        #    print("%s" % self._data[row + 1])

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
        self._assert_step_order(STEP2, STEP1)

    def test_undo_move_row_down(self):
        self._exec(MoveRowsDown([0]))
        self._exec(Undo())
        self._assert_step_order(STEP1, STEP2)

    def test_move_rows_down(self):
        self._exec(MoveRowsDown([0,1]))
        self._assert_step_order(STEP_WITH_COMMENT, STEP1, STEP2)

    def _assert_step_order(self, *steps):
        for idx, step in enumerate(steps):
            assert_equal(self._steps[idx].as_list(),
                         self._data_step_as_list(step))
        assert_true(self._ctrl.dirty)


if __name__ == "__main__":
    unittest.main()
