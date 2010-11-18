import unittest

from robot.utils.asserts import assert_true, assert_false, assert_equals
from base_command_test import TestCaseCommandTest, STEP1, STEP1_KEYWORD, \
     FOR_LOOP_HEADER, FOR_LOOP_STEP1, FOR_LOOP_STEP2, STEP_WITH_COMMENT, STEP2, data

from robotide.controller.commands import SaveFile, ChangeCellValue, CopyMacroAs, \
     Undo, Redo, DeleteRow, AddRow, AddRows, MoveRowUp, CommentRows, Purify, \
     UncommentRows, PasteArea, InsertCells, DeleteRows, DeleteCells, ClearArea, \
     MoveRowsUp, MoveRowDown, MoveRowsDown


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
        assert_equals(len(self._ctrl.steps), self._orig_number_of_steps+1)
        other = self._get_macro_by_name(other_name)
        assert_equals(len(other.steps), self._orig_number_of_steps+1)

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
        assert_equals(len(macro_names), original_macro_number+1)
        assert_equals(len(self._get_macro_by_name(new_name).steps), len(self._ctrl.steps))

    def test_copy_does_not_change_original(self):
        new_name = self._ctrl.name + '2'
        self._exec(CopyMacroAs(new_name))
        copies = [m for m in self._get_macros() if m.name == new_name]
        assert_equals(len(copies), 1)
        copy = copies[0]
        copy.execute(ChangeCellValue(0, 0, 'Changed Step'))
        assert_equals(self._ctrl.steps[0].keyword, STEP1_KEYWORD)
        assert_equals(copy.steps[0].keyword, 'Changed Step')


class TestCaseEditingTest(TestCaseCommandTest):

    def test_changing_one_cell(self):
        self._exec(ChangeCellValue(0, 0, 'Changed Step'))
        assert_equals(self._steps[0].keyword, 'Changed Step')

    def test_changing_one_cell_with_unicode(self):
        odd_string = '\xc3\xa4'
        assert_false(isinstance(odd_string, unicode))
        self._exec(ChangeCellValue(0, 0, odd_string))
        assert_equals(self._steps[0].keyword, unicode(odd_string, 'UTF-8'))
        assert_true(isinstance(self._steps[0].keyword, unicode))

    def test_undo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[0]
        changed_cell_value = 'Changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value))
        assert_equals(self._steps[0].keyword, changed_cell_value)
        self._exec(Undo())
        assert_equals(self._steps[0].keyword, original_cell_value)
        self._exec(Redo())
        assert_equals(self._steps[0].keyword, changed_cell_value)

    def test_undo_when_nothing_to_undo(self):
        self._exec(Undo())
        assert_equals(self._number_of_test_changes, 0)

    def test_redo_when_nothing_to_redo(self):
        self._exec(Redo())
        assert_equals(self._number_of_test_changes, 0)

    def test_undo_undo_redo_redo(self):
        original_cell_value = self._data_step_as_list(STEP1)[0]
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Again changed Step'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        assert_equals(self._steps[0].keyword, changed_cell_value_1)
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        assert_equals(self._steps[0].keyword, changed_cell_value_2)
        self._exec(Undo())
        assert_equals(self._steps[0].keyword, changed_cell_value_1)
        self._exec(Undo())
        assert_equals(self._steps[0].keyword, original_cell_value)
        self._exec(Redo())
        assert_equals(self._steps[0].keyword, changed_cell_value_1)
        self._exec(Redo())
        assert_equals(self._steps[0].keyword, changed_cell_value_2)

    def test_redo_does_nothing_after_state_changing_command_that_is_not_undo(self):
        changed_cell_value_1 = 'Changed Step'
        changed_cell_value_2 = 'Changed Step again'
        self._exec(ChangeCellValue(0, 0, changed_cell_value_1))
        self._exec(Undo())
        self._exec(ChangeCellValue(0, 0, changed_cell_value_2))
        self._exec(Redo())
        assert_equals(self._steps[0].keyword, changed_cell_value_2)

    def test_changing_cell_value_after_last_column_adds_empty_columns(self):
        self._exec(ChangeCellValue(0, 2, 'Hello'))
        assert_equals(self._steps[0].args, ['arg', 'Hello'])

    def test_changing_cell_value_after_last_row_adds_empty_rows(self):
        self._exec(ChangeCellValue(len(data)+5, 0, 'Hello'))
        assert_equals(self._steps[len(data)+5].keyword, 'Hello')

    def test_changing_for_loop_header_value(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 0, 'Keyword'))
        assert_equals(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      ['Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[1:])
        assert_equals(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                      self._data_step_as_list(FOR_LOOP_STEP1))
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_changing_for_loop_header_argument(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 1, 'Keyword'))
        assert_equals(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      [': FOR', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[2:])
        assert_equals(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                      self._data_step_as_list(FOR_LOOP_STEP1))
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_changing_for_loop_header_in_clause(self):
        self._exec(ChangeCellValue(self._data_row(FOR_LOOP_HEADER), 2, 'Keyword'))
        assert_equals(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      [': FOR', '${i}', 'Keyword'] + self._data_step_as_list(FOR_LOOP_HEADER)[3:])
        assert_equals(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                      self._data_step_as_list(FOR_LOOP_STEP1))
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_deleting_row(self):
        self._exec(DeleteRow(0))
        self._verify_step_number_change(-1)
        self._verify_row_does_not_exist(STEP1)

    def test_undoing_row_delete(self):
        self._exec(DeleteRow(0))
        self._exec(Undo())
        assert_equals(len(self._steps), self._orig_number_of_steps)
        self._verify_step(0, 'Step 1', ['arg'])

    def test_delete_row_inside_of_for_loop(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_STEP1)))
        assert_equals(len(self._steps), self._orig_number_of_steps-1)
        self._verify_row_does_not_exist(FOR_LOOP_STEP1)

    def test_delete_for_loop_header_row(self):
        self._exec(DeleteRow(self._data_row(FOR_LOOP_HEADER)))
        assert_equals(len(self._steps), self._orig_number_of_steps-1)
        self._verify_row_does_not_exist(FOR_LOOP_HEADER)

    def test_adding_row_last(self):
        self._exec(AddRow(-1))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[self._orig_number_of_steps].as_list(), [])

    def test_adding_row_first(self):
        self._exec(AddRow(0))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[0].as_list(), [])

    def test_adding_row_middle(self):
        self._exec(AddRow(1))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[1].as_list(), [])

    def test_adding_row_in_for_loop_body(self):
        row_in_for_loop = self._data_row(FOR_LOOP_STEP2)
        self._exec(AddRow(row_in_for_loop))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[row_in_for_loop].as_list(), [''])

    def test_add_multiple_rows(self):
        self._exec(AddRows([3,2,1,4,5,6,9,8,7,10]))
        assert_equals(len(self._steps), self._orig_number_of_steps+10)
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step(11, 'Step 2', ['a1', 'a2', 'a3'])

    def test_undo_multiple_rows_add(self):
        self._exec(AddRows([3,2,1,4,5,6,9,8,7,10]))
        self._exec(Undo())
        self._verify_step(0, 'Step 1', ['arg'])
        self._verify_step(1, 'Step 2', ['a1', 'a2', 'a3'])

    def test_purify_removes_empty_rows(self):
        self._exec(AddRow(-1))
        self._exec(AddRow(1))
        self._exec(AddRow(2))
        assert_equals(len(self._steps), self._orig_number_of_steps+3)
        self._exec(Purify())
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_purify_removes_rows_with_no_data(self):
        self._exec(ChangeCellValue(0,0, ''))
        self._exec(ChangeCellValue(0,1, ''))
        self._exec(Purify())
        assert_equals(len(self._steps), self._orig_number_of_steps-1)

    def test_can_add_values_to_empty_row(self):
        self._exec(AddRow(-1))
        self._exec(ChangeCellValue(0, 3, 'HELLO'))
        assert_equals(self._steps[0].args, ['arg', '', 'HELLO'])

    def test_only_comment_is_left(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 0, ''))
        self._exec(Purify())
        assert_equals(self._steps[index].as_list(), ['# this is a comment'])

    def test_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 1, '# new comment'))
        self._verify_step(index, 'Foo', [], '# new comment')

    def test_cell_value_after_comment_is_changed(self):
        index = self._data_row(STEP_WITH_COMMENT)
        self._exec(ChangeCellValue(index, 2, 'something'))
        assert_equals(self._steps[index].as_list(), ['Foo', '# this is a comment', 'something'])

    def test_change_keyword_value_in_indented_step(self):
        index = self._data_row(FOR_LOOP_STEP1)
        self._exec(ChangeCellValue(index, 1, 'Blog'))
        assert_equals(self._steps[index].keyword, 'Blog')
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_delete_multiple_rows(self):
        self._exec(DeleteRows([2,0]))
        assert_equals(len(self._steps), self._orig_number_of_steps-2)
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

    def test_commenting(self):
        self._exec(CommentRows([0]))
        self._verify_step(0, 'Comment', ['Step 1', 'arg'])

    def test_commenting_many_rows(self):
        self._exec(CommentRows([1,2,3,4]))
        assert_equals(self._steps[self._data_row(STEP2)].as_list(),
                      ['Comment'] + self._data_step_as_list(STEP2))
        assert_equals(self._steps[self._data_row(STEP_WITH_COMMENT)].as_list(),
                      ['Comment'] + self._data_step_as_list(STEP_WITH_COMMENT))
        assert_equals(self._steps[self._data_row(FOR_LOOP_HEADER)].as_list(),
                      ['Comment'] + self._data_step_as_list(FOR_LOOP_HEADER))
        assert_equals(self._steps[self._data_row(FOR_LOOP_STEP1)].as_list(),
                      ['Comment'] + self._data_step_as_list(FOR_LOOP_STEP1))

    def test_commenting_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        self._exec(CommentRows([row]))
        assert_equals(self._steps[row].as_list(),
                      ['', 'Comment'] + self._data_step_as_list(FOR_LOOP_STEP1)[1:])

    def test_uncommenting_single_row(self):
        self._exec(CommentRows([0]))
        self._exec(UncommentRows([0]))
        assert_equals(self._steps[0].as_list(), self._data_step_as_list(STEP1))

    def test_uncommenting_rows(self):
        self._exec(CommentRows([1,2,3,4]))
        self._exec(UncommentRows([1,2,3,4]))
        assert_equals(self._steps[1].as_list(), self._data_step_as_list(STEP2))
        assert_equals(self._steps[2].as_list(), self._data_step_as_list(STEP_WITH_COMMENT))
        assert_equals(self._steps[3].as_list(), self._data_step_as_list(FOR_LOOP_HEADER))
        assert_equals(self._steps[4].as_list(), self._data_step_as_list(FOR_LOOP_STEP1))

    def test_uncommenting_commented_step_in_for_loop(self):
        row = self._data_row(FOR_LOOP_STEP1)
        self._exec(CommentRows([row]))
        self._exec(UncommentRows([row]))
        assert_equals(self._steps[row].as_list(), self._data_step_as_list(FOR_LOOP_STEP1))

    def test_uncommenting_does_nothing_if_not_commented(self):
        self._exec(UncommentRows([1,2,3,4]))
        assert_equals(self._steps[1].as_list(), self._data_step_as_list(STEP2))
        assert_equals(self._steps[2].as_list(), self._data_step_as_list(STEP_WITH_COMMENT))
        assert_equals(self._steps[3].as_list(), self._data_step_as_list(FOR_LOOP_HEADER))
        assert_equals(self._steps[4].as_list(), self._data_step_as_list(FOR_LOOP_STEP1))

    def test_commenting_and_uncommenting_row_with_no_step(self):
        self._exec(CommentRows([1000]))
        self._verify_number_of_test_changes(0)
        self._exec(UncommentRows([10001]))
        self._verify_number_of_test_changes(0)


class RowMovingTest(TestCaseCommandTest):

    def test_row_up(self):
        self._exec(MoveRowUp(1))
        self._assert_step_order(STEP2, STEP1)

    def test_first_row_up_does_nothing(self):
        self._exec(MoveRowUp(0))
        self._assert_step_order(STEP1)

    def test_undo_row_up(self):
        self._exec(MoveRowUp(1))
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
        self._exec(MoveRowDown(0))
        self._assert_step_order(STEP2, STEP1)

    def test_undo_move_row_down(self):
        self._exec(MoveRowDown(0))
        self._exec(Undo())
        self._assert_step_order(STEP1, STEP2)

    def test_move_rows_down(self):
        self._exec(MoveRowsDown([0,1]))
        self._assert_step_order(STEP_WITH_COMMENT, STEP1, STEP2)

    def _assert_step_order(self, *steps):
        for idx, step in enumerate(steps):
            assert_equals(self._steps[idx].as_list(),
                          self._data_step_as_list(step))


if __name__ == "__main__":
    unittest.main()
