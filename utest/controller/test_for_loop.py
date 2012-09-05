import unittest
import datafilereader
from robotide.controller.cellinfo import CellType
from robotide.controller.commands import MoveRowsDown, Undo, ChangeCellValue, InsertCell, DeleteCell
from robotide.controller.stepcontrollers import ForLoopStepController, IntendedStepController, StepController


class TestForLoop(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chief = datafilereader.construct_chief_controller(datafilereader.FOR_LOOP_PATH)

    def test_for_loop_move(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(MoveRowsDown([0]))
        test.execute(MoveRowsDown([1]))
        self.assertEqual(test.get_cell_info(1,1).cell_type, CellType.ASSIGN)
        test.execute(Undo())
        test.execute(Undo())
        self.assertEqual(test.get_cell_info(1,1).cell_type, CellType.MANDATORY)

    def test_adding_new_for_loop(self):
        test2 = self.chief.datafiles[1].tests[1]
        test2.execute(ChangeCellValue(0, 0, ':FOR'))
        self.assertTrue(isinstance(test2.step(0), ForLoopStepController),
            'wrong type of step type (%s)' % type(test2.step(0)))

    def test_adding_step_to_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(ChangeCellValue(4, 1, 'No Operation'))
        self.assertTrue(isinstance(test.step(4), IntendedStepController),
            'wrong type of step type (%s)' % type(test.step(4)))

    def test_removing_step_in_middle_from_for_loop(self):
        test = self.chief.datafiles[1].tests[5]
        test.execute(ChangeCellValue(2, 0, 'Something'))
        self._steps_are_in_for_loop(test, 1)
        self._steps_are_not_in_for_loop(test, 2, 3)
        self._steps_first_cells_are_empty(test, 1, 3)

    def _steps_first_cells_are_empty(self, macro, *steps):
        for i in steps:
            self.assertEqual(macro.step(i).get_value(0), '')

    def test_removing_first_step_from_for_loop(self):
        test = self.chief.datafiles[1].tests[6]
        test.execute(ChangeCellValue(1, 0, 'Invalidate all'))
        self._steps_are_not_in_for_loop(test, 1, 2, 3)
        self._steps_first_cells_are_empty(test, 2, 3)

    def test_removing_last_step_from_for_loop(self):
        test = self.chief.datafiles[1].tests[7]
        test.execute(ChangeCellValue(3, 0, 'Something'))
        self._steps_are_in_for_loop(test, 1, 2)
        self._steps_are_not_in_for_loop(test, 3)
        self._steps_first_cells_are_empty(test, 1, 2)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_first_position(self):
        test = self.chief.datafiles[1].tests[3]
        test.execute(InsertCell(1, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_middle_position(self):
        test = self.chief.datafiles[1].tests[2]
        test.execute(InsertCell(2, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_step_so_that_it_becomes_part_of_for_loop_at_last_position(self):
        test = self.chief.datafiles[1].tests[4]
        test.execute(InsertCell(3, 0))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_modify_last_step_so_that_it_should_be_empty_and_not_part_of_for_loop(self):
        test = self.chief.datafiles[1].tests[8]
        test.execute(ChangeCellValue(2, 0, ''))
        self._steps_are_not_in_for_loop(test, 2)

    def test_empty_normal_step_first_cell(self):
        test = self.chief.datafiles[1].tests[9]
        test.execute(ChangeCellValue(0, 0, ''))
        self._steps_are_not_in_for_loop(test, 0)

    def _steps_are_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), IntendedStepController, 'Wrong type in index %d' % i)

    def _steps_are_not_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), StepController, 'Wrong type in index %d' % i)

    def test_modifying_step_in_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(ChangeCellValue(3, 1, 'Something again'))
        self.assertEqual(type(test.step(3)), IntendedStepController)

    def test_new_for_loop(self):
        test = self.chief.datafiles[1].tests[10]
        test.execute(ChangeCellValue(0, 0, ': FOR'))
        test.execute(ChangeCellValue(0, 1, '${i}'))
        test.execute(ChangeCellValue(0, 2, 'IN RANGE'))
        test.execute(ChangeCellValue(0, 3, '100'))
        self.assertEqual(test.steps[0].as_list(), [':FOR', '${i}', 'IN RANGE', '100'])
        self.assertEqual(type(test.steps[0]), ForLoopStepController)

    def test_for_loop_creation_and_steps(self):
        test = self.chief.datafiles[1].tests[11]
        test.execute(ChangeCellValue(0, 0, ': FOR'))
        self._steps_are_in_for_loop(test, 1, 2, 3)

    def test_for_loop_shift_left(self):
        test = self.chief.datafiles[1].tests[12]
        test.execute(ChangeCellValue(0, 0, ': FOR'))
        test.execute(DeleteCell(0,0))
        self.assertEqual(type(test.steps[0]), StepController)

if __name__ == '__main__':
    unittest.main()
