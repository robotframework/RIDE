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
import os
import sys

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

import unittest
import datafilereader
from robotide.controller.cellinfo import CellType
from robotide.controller.ctrlcommands import MoveRowsDown, Undo, ChangeCellValue, InsertCell, DeleteCell, Purify, MoveRowsUp
from robotide.controller.stepcontrollers import ForLoopStepController, IntendedStepController, StepController


class TestForLoop(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = datafilereader.construct_project(datafilereader.FOR_LOOP_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def test_for_loop_move_with_undo_preserves_correct_celltype(self):
        test = self.project.datafiles[1].tests[0]
        test.execute(MoveRowsDown([0]))
        test.execute(MoveRowsDown([1]))
        self.assertEqual(test.get_cell_info(1,1).cell_type, CellType.ASSIGN)
        test.execute(Undo())
        test.execute(Undo())
        self.assertEqual(test.get_cell_info(1,1).cell_type, CellType.KEYWORD)

    def test_adding_new_for_loop(self):
        test2 = self.project.datafiles[1].tests[1]
        test2.execute(ChangeCellValue(0, 0, 'FOR'))
        self.assertTrue(isinstance(test2.step(0), ForLoopStepController),
            'wrong type of step type (%s)' % type(test2.step(0)))

    def test_adding_step_to_for_loop(self):
        test = self.project.datafiles[1].tests[0]
        test.execute(ChangeCellValue(4, 1, 'No Operation'))
        self.assertTrue(isinstance(test.step(4), IntendedStepController),
            'wrong type of step type (%s)' % type(test.step(4)))

    def test_removing_step_in_middle_from_for_loop(self):
        test = self.project.datafiles[1].tests[5]
        test.execute(ChangeCellValue(2, 0, 'Something'))
        self._steps_are_in_for_loop(test, 1)
        self._steps_are_not_in_for_loop(test, 2, 3)
        self._steps_first_cells_are_empty(test, 1, 3)

    def _steps_first_cells_are_empty(self, macro, *steps):
        for i in steps:
            self.assertEqual(macro.step(i).get_value(0), '')

    def test_removing_first_step_from_for_loop(self):
        test = self.project.datafiles[1].tests[6]
        test.execute(ChangeCellValue(1, 0, 'Invalidate all'))
        self._steps_are_not_in_for_loop(test, 1, 2, 3)
        self._steps_first_cells_are_empty(test, 2, 3)

    def test_removing_last_step_from_for_loop(self):
        test = self.project.datafiles[1].tests[7]
        test.execute(ChangeCellValue(3, 0, 'Something'))
        self._steps_are_in_for_loop(test, 1, 2)
        self._steps_are_not_in_for_loop(test, 3)
        self._steps_first_cells_are_empty(test, 1, 2)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_first_position(self):
        test = self.project.datafiles[1].tests[3]
        test.execute(InsertCell(1, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_middle_position(self):
        test = self.project.datafiles[1].tests[2]
        test.execute(InsertCell(2, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_last_position(self):
        test = self.project.datafiles[1].tests[4]
        test.execute(InsertCell(3, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_last_step_so_that_it_should_be_empty_and_not_part_of_for_loop(self):
        test = self.project.datafiles[1].tests[8]
        test.execute(ChangeCellValue(2, 0, ''))
        self._steps_are_not_in_for_loop(test, 2)

    def test_empty_normal_step_first_cell(self):
        test = self.project.datafiles[1].tests[9]
        test.execute(ChangeCellValue(0, 0, ''))
        self._steps_are_not_in_for_loop(test, 0)

    def _steps_are_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), IntendedStepController, 'Wrong type in index %d' % i)

    def _steps_are_not_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), StepController, 'Wrong type in index %d' % i)

    def test_modifying_step_in_for_loop(self):
        test = self.project.datafiles[1].tests[0]
        test.execute(ChangeCellValue(3, 1, 'Something again'))
        self.assertEqual(type(test.step(3)), IntendedStepController)

    def test_new_for_loop_old_syntax(self):
        test = self.project.datafiles[1].tests[10]
        test.execute(ChangeCellValue(0, 0, ': FOR'))
        test.execute(ChangeCellValue(0, 1, '${i}'))
        test.execute(ChangeCellValue(0, 2, 'IN RANGE'))
        test.execute(ChangeCellValue(0, 3, '100'))
        self.assertEqual(test.steps[0].as_list(), ['FOR', '${i}', 'IN RANGE', '100'])
        self.assertEqual(type(test.steps[0]), ForLoopStepController)

    def test_new_for_loop(self):
        test = self.project.datafiles[1].tests[10]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        test.execute(ChangeCellValue(0, 1, '${i}'))
        test.execute(ChangeCellValue(0, 2, 'IN RANGE'))
        test.execute(ChangeCellValue(0, 3, '100'))
        self.assertEqual(test.steps[0].as_list(), ['FOR', '${i}', 'IN RANGE', '100'])
        self.assertEqual(type(test.steps[0]), ForLoopStepController)

    def test_for_loop_creation_and_steps(self):
        test = self.project.datafiles[1].tests[11]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_for_loop_shift_left(self):
        test = self.project.datafiles[1].tests[12]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        test.execute(DeleteCell(0,0))
        self.assertEqual(type(test.steps[0]), StepController)

    def test_for_loop_change_and_purify(self):
        test = self.project.datafiles[1].tests[13]
        test.execute(ChangeCellValue(1, 2, ''))
        test.execute(Purify())
        self._steps_are_in_for_loop(test, 2)

    def test_adding_comment(self):
        test = self.project.datafiles[1].tests[14]
        test.execute(ChangeCellValue(1, 2, '#UnChanged comment'))
        self.assertEqual(test.steps[1].as_list(), ['', 'No Operation', '#UnChanged comment'])
        test.execute(ChangeCellValue(1, 2, '# comment UnChanged'))
        self.assertEqual(test.steps[1].as_list(), ['', 'No Operation', '# comment UnChanged'])
        test.execute(ChangeCellValue(1, 2, '##comment UnChanged'))
        self.assertEqual(test.steps[1].as_list(), ['', 'No Operation', '##comment UnChanged'])

    def test_comment_is_preserved_when_shifting_row_to_left_and_back(self):
        test = self.project.datafiles[1].tests[15]
        test.execute(DeleteCell(2,0))
        self.assertEqual(test.steps[2].as_list(), ['Keyword', '# comment'])
        test.execute(InsertCell(2,0))
        self.assertEqual(test.steps[2].as_list(), ['', 'Keyword', '# comment'])
        test.execute(DeleteCell(1,0))
        self.assertEqual(test.steps[1].as_list(), ['Kw1', '# comment'])
        test.execute(InsertCell(1,0))
        self.assertEqual(test.steps[1].as_list(), ['', 'Kw1', '# comment'])

    def test_new_for_loop_with_existing_comment(self):
        test = self.project.datafiles[1].tests[16]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        test.execute(ChangeCellValue(0, 2, '# comment'))  #idented comments del
        self.assertEqual(test.steps[0].as_list(), ['FOR', '', '# comment'])
        test.execute(DeleteCell(0, 0))
        self.assertEqual(test.steps[0].as_list(), ['', '# comment'])

    def test_move_for_loop_over_another_for_loop(self):
        loop_1 = 'FOR  ${i}  IN  1  2  3  4'.split('  ')
        loop_2 = ['FOR', '${j}', 'IN RANGE', '100']
        inside_1 = ['', 'No Operation']
        inside_2 = ['', 'Fail']
        test = self.project.datafiles[1].tests[17]
        self._verify_steps(test.steps, loop_1, inside_1, loop_2, inside_2)
        test.execute(MoveRowsUp([2]))
        self._verify_steps(test.steps, loop_1, loop_2, inside_1, inside_2)
        test.execute(MoveRowsUp([1]))
        self._verify_steps(test.steps, loop_2, loop_1, inside_1, inside_2)
        test.execute(MoveRowsDown([0]))
        self._verify_steps(test.steps, loop_1, loop_2, inside_1, inside_2)

    def test_move_for_loop_header_between_for_loops(self):
        test = self.project.datafiles[1].tests[18]
        test.execute(MoveRowsDown([3]))
        self.assertEqual(test.steps[4].as_list()[1], '${j}')

    def _verify_steps(self, steps, *expected):
        for step, exp in zip(steps, expected):
            self.assertEqual(step.as_list(), exp)
        self.assertEqual(len(steps), len(expected), steps)

if __name__ == '__main__':
    unittest.main()
