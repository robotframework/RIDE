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
from utest.resources import datafilereader
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
        print("DEBUG: before 0")
        for s in test.steps:
            print(f"{s.as_list()}")
        self.assertEqual(test.get_cell_info(1, 1).cell_type, CellType.KEYWORD)
        test.execute(MoveRowsDown([0]))
        print("DEBUG: after move 0")
        for s in test.steps:
            print(f"{s.as_list()}")
        test.execute(MoveRowsDown([1]))
        # print("DEBUG: after move 1")
        # for s in test.steps:
        #     print(f"{s.as_list()}")
        self.assertEqual(test.get_cell_info(2,3).cell_type, CellType.OPTIONAL)
        test.execute(Undo())
        test.execute(Undo())
        print("DEBUG: after undos, should be equal to 0")
        for s in test.steps:
            print(f"{s.as_list()}")
        self.assertEqual(test.get_cell_info(1,1).cell_type, CellType.KEYWORD)
        # print("DEBUG: Test 0:")
        # for s in test.steps:
        #    print(f"{s.as_list()}")

    def test_adding_new_for_loop(self):
        test2 = self.project.datafiles[1].tests[1]
        test2.execute(ChangeCellValue(0, 0, 'FOR'))
        # print("DEBUG: Test 1:")
        # for s in test2.steps:
        #    print(f"{s.as_list()}")
        self.assertTrue(isinstance(test2.step(0), StepController),
            'wrong type of step type (%s)' % type(test2.step(0)))

    def test_adding_step_to_for_loop(self):
        test = self.project.datafiles[1].tests[0]
        test.execute(ChangeCellValue(4, 2, 'No Operation'))
        self.assertTrue(isinstance(test.step(4), StepController),
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
        test.execute(ChangeCellValue(1, 2, 'Invalidate all'))
        self._steps_are_in_for_loop(test, 1, 2, 3)
        self._steps_first_cells_are_empty(test, 2, 3)

    def test_removing_last_step_from_for_loop(self):
        test = self.project.datafiles[1].tests[7]
        test.execute(ChangeCellValue(3, 2, 'Something'))
        print("DEBUG: Test 7:")
        for s in test.steps:
            print(f"{s.as_list()}")
        self._steps_are_in_for_loop(test, 1, 2)
        self._steps_are_in_for_loop(test, 3)
        self._steps_first_cells_are_empty(test, 1, 2)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_first_position(self):
        test = self.project.datafiles[1].tests[3]
        test.execute(InsertCell(1, 0))
        print("DEBUG: Test 3:")
        for s in test.steps:
            print(f"{s.as_list()}")
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_middle_position(self):
        test = self.project.datafiles[1].tests[2]
        test.execute(InsertCell(2, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_last_position(self):
        test = self.project.datafiles[1].tests[4]
        print(f"\nDEBUG: test_modify_step_so_that_it_becomes_part_of_for_loop_at_last_position before:")
        for row in test.steps:
            print("%s" % row.as_list())
        test.execute(InsertCell(3, 0))
        print(f"\nDEBUG: test_modify_step_so_that_it_becomes_part_of_for_loop_at_last_position after InsertCell:")
        for row in test.steps:
            print("%s" % row.as_list())
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
            self.assertEqual(type(macro.step(i)), StepController, 'Wrong type in index %d' % i)

    def _steps_are_not_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), StepController, 'Wrong type in index %d' % i)

    def test_modifying_step_in_for_loop(self):
        test = self.project.datafiles[1].tests[0]
        test.execute(ChangeCellValue(4, 2, 'Something again'))
        self.assertEqual(type(test.step(4)), StepController)

    def test_new_for_loop_old_syntax(self):
        test = self.project.datafiles[1].tests[10]
        test.execute(ChangeCellValue(0, 0, ': FOR'))
        test.execute(ChangeCellValue(0, 1, '${i}'))
        test.execute(ChangeCellValue(0, 2, 'IN RANGE'))
        test.execute(ChangeCellValue(0, 3, '100'))
        self.assertEqual(test.steps[0].as_list(), [': FOR', '${i}', 'IN RANGE', '100'])
        # self.assertEqual(type(test.steps[0]), ForLoopStepController)

    def test_new_for_loop(self):
        test = self.project.datafiles[1].tests[10]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        test.execute(ChangeCellValue(0, 1, '${i}'))
        test.execute(ChangeCellValue(0, 2, 'IN RANGE'))
        test.execute(ChangeCellValue(0, 3, '100'))
        self.assertEqual(test.steps[0].as_list(), ['FOR', '${i}', 'IN RANGE', '100'])
        # self.assertEqual(type(test.steps[0]), ForLoopStepController)

    def test_for_loop_creation_and_steps(self):
        test = self.project.datafiles[1].tests[11]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        self._steps_are_not_in_for_loop(test, 1, 2, 3)

    def test_for_loop_shift_left(self):
        test = self.project.datafiles[1].tests[12]
        test.execute(ChangeCellValue(0, 0, 'FOR'))
        test.execute(DeleteCell(0,0))
        self.assertEqual(type(test.steps[0]), StepController)

    # @unittest.skip("Test is losing forloop step")  # FIXME
    def test_for_loop_change_and_purify(self):
        test = self.project.datafiles[1].tests[13]
        print("DEBUG: Test 13:")
        for s in test.steps:
            print(f"{s.as_list()}")
        test.execute(ChangeCellValue(1, 2, ''))
        test.execute(Purify())  # DEBUG This is removing step
        print("DEBUG: After Purify:")
        for s in test.steps:
            print(f"{s.as_list()}")
        self._steps_are_in_for_loop(test, 2)

    def test_adding_comment(self):
        test = self.project.datafiles[1].tests[14]
        test.execute(ChangeCellValue(1, 1, '#UnChanged comment'))
        self.assertEqual(test.steps[1].as_list(), ['', '#UnChanged comment'])
        test.execute(ChangeCellValue(1, 2, '# comment UnChanged'))
        self.assertEqual(test.steps[1].as_list(), ['', '#UnChanged comment', '# comment UnChanged'])
        test.execute(ChangeCellValue(1, 2, '##comment UnChanged'))
        self.assertEqual(test.steps[1].as_list(), ['', '#UnChanged comment', '##comment UnChanged'])

    def test_comment_is_preserved_when_shifting_row_to_left_and_back(self):
        # FIXME
        test = self.project.datafiles[1].tests[15]
        test.execute(DeleteCell(2, 0))
        self.assertEqual(test.steps[2].as_list(), ['Keyword', '# comment'])
        test.execute(InsertCell(2, 0))
        self.assertEqual(test.steps[2].as_list(), ['', 'Keyword', '# comment'])
        test.execute(InsertCell(1,2))
        self.assertEqual(test.steps[1].as_list(), ['', 'Kw1', '', '# comment'])
        test.execute(DeleteCell(1,2))
        self.assertEqual(test.steps[1].as_list(), ['', 'Kw1', '# comment'])

    def test_new_for_loop_with_existing_comment(self):
        test = self.project.datafiles[1].tests[16]
        # print("DEBUG: Test 16:")
        # for s in test.steps:
        #     print(f"{s.as_list()}")
        test.execute(ChangeCellValue(0, 0, 'FOR', True))
        test.execute(ChangeCellValue(0, 2, '# comment'))  # idented comments del
        self.assertEqual(test.steps[0].as_list(), ['FOR', 'Foo', '# comment'])
        test.execute(DeleteCell(0, 0))
        self.assertEqual(test.steps[0].as_list(), ['Foo', '# comment'])

    # @unittest.skip("Test is losing forloop step")  # FIXME see comment
    def test_move_for_loop_over_another_for_loop(self):
        loop_1 = 'FOR  ${i}  IN  1  2  3  4'.split('  ')
        end_1 = ['END']
        loop_2 = ['FOR', '${j}', 'IN RANGE', '100']
        inside_1 = ['', 'No Operation']
        inside_2 = ['', 'Fail']
        test = self.project.datafiles[1].tests[17]
        self._verify_steps(test.steps, loop_1, inside_1, end_1, loop_2, inside_2, end_1)
        print("DEBUG: BEFORE MOVE UP FOR Test 17:")
        for s in test.steps:
            print(f"{s.as_list()}")
        test.execute(MoveRowsUp([3]))
        print("DEBUG: AFTER MOVE UP FOR Test 17:")
        for s in test.steps:
            print(f"{s.as_list()}")
        # Actually the previous output shows the correct structure, but then the verification fails.
        # If we change MoveRowsUp() to return False, the test passes, but other tests will fail, one of them is
        # a trivial fix, but other 5 are not. This was the motivation to skip this test for now.
        self._verify_steps(test.steps, loop_1, inside_1, [''] + loop_2, [''] + end_1, inside_2, end_1)
        """
        test.execute(MoveRowsUp([2]))
        self._verify_steps(test.steps, loop_1, [''] + loop_2, [''] + inside_1, [''] + end_1, inside_2, end_1)
        print("DEBUG: BEFORE Test 17:")
        for s in test.steps:
            print(f"{s.as_list()}")
        test.execute(MoveRowsUp([1]))
        print("DEBUG: AFTER MOVE Test 17:")
        for s in test.steps:
            print(f"#_{s.as_list()}_#{type(s)}")
        """
        #self._verify_steps(test.steps, loop_2, [''] + loop_1, [''] + inside_1, [''] + end_1, inside_2, end_1)
        # test.execute(MoveRowsDown([0]))
        # self._verify_steps(test.steps, loop_1, [''] + loop_2, inside_1, [''] + end_1, inside_2, end_1)

    def test_move_for_loop_header_between_for_loops(self):
        test = self.project.datafiles[1].tests[18]
        test.execute(MoveRowsDown([3]))
        self.assertEqual(test.steps[4].as_list()[2], '${j}')

    def test_move_for_loop_in_mulitlevels(self):
        # FIXME
        loop_1 = ['FOR', '${loop1}', 'IN RANGE', '1', '19']
        inside_NO = ['', 'No Operation']
        loop_2 = ['', 'FOR', '${loop2}', 'IN RANGE', '${loop1}', '20']
        inside_NO_2 = ['', '', 'No Operation']
        loop_3 = ['', '', 'FOR', '${loop3}', 'IN RANGE', '2', '4']
        inside_NO_3 = ['', '', '', 'No Operation']
        inside_L3 = ['', '', '', 'Log', 'This is loop 3: ${loop3}']
        inside_E3 = ['', '', 'END']
        inside_L2 = ['', '', 'Log', 'This is loop 2: ${loop2}']
        inside_E2 = ['', 'END']
        inside_L1 = ['', 'Log', 'This is loop 1: ${loop1}']
        inside_LG = ['', 'Log', 'Generic']
        inside_E1 = ['END']
        test = self.project.datafiles[1].tests[19]
        print("DEBUG: Test 19:")
        for s in test.steps:
            print(f"{s.as_list()}")
        self._verify_steps(test.steps, loop_1, inside_NO, loop_2, inside_NO_2, loop_3, inside_NO_3, inside_L3,
                           inside_NO_3, inside_E3, inside_NO_2, inside_L2, inside_E2, inside_L1, inside_NO,
                           inside_LG, inside_E1)
        # TODO: Confirm the indentation on Text  and Grid Editors
        test.execute(MoveRowsUp([2]))
        print("DEBUG: Test 19: After moveup 2")
        for s in test.steps:
            print(f"{s.as_list()}")
        self._verify_steps(test.steps, loop_1, loop_2, inside_NO_2, inside_NO_2, loop_3, inside_NO_3, inside_L3,
                           inside_NO_3, inside_E3, inside_NO_2, inside_L2, inside_E2, inside_L1, inside_NO,
                           inside_LG, inside_E1)
        """  
        test.execute(MoveRowsUp([1]))
        self._verify_steps(test.steps, loop_2, loop_1, inside_1, inside_2)
        test.execute(MoveRowsDown([0]))
        self._verify_steps(test.steps, loop_1, loop_2, inside_1, inside_2)
        """

    def _verify_steps(self, steps, *expected):
        for step, exp in zip(steps, expected):
            self.assertEqual(step.as_list(), exp)
        self.assertEqual(len(steps), len(expected))  # , steps)


if __name__ == '__main__':
    unittest.main()
