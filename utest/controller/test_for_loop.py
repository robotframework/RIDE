import unittest
import datafilereader
from robotide.controller.cellinfo import CellType
from robotide.controller.commands import MoveRowsDown, Undo, ChangeCellValue
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
        test2.execute(Undo())

    def test_adding_step_to_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(ChangeCellValue(4, 1, 'No Operation'))
        self.assertTrue(isinstance(test.step(4), IntendedStepController),
            'wrong type of step type (%s)' % type(test.step(4)))

    def test_removing_steps_from_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        self._steps_are_in_for_loop(test, 3, 4, 5)
        test.execute(ChangeCellValue(4, 0, 'Something'))
        self._steps_are_in_for_loop(test, 3)
        self._steps_are_not_in_for_loop(test, 4, 5)
        test.execute(Undo())
        self._steps_are_in_for_loop(test, 3, 4, 5)

    def test_removing_first_step_from_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(ChangeCellValue(3, 0, 'Invalidate all'))
        self._steps_are_not_in_for_loop(test, 3, 4, 5)
        test.execute(Undo())
        self._steps_are_in_for_loop(test, 3, 4, 5)

    def _steps_are_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), IntendedStepController)

    def _steps_are_not_in_for_loop(self, macro, *steps):
        for i in steps:
            self.assertEqual(type(macro.step(i)), StepController)

    def test_modifying_step_in_for_loop(self):
        test = self.chief.datafiles[1].tests[0]
        test.execute(ChangeCellValue(3, 1, 'Something again'))
        self.assertEqual(type(test.step(3)), IntendedStepController)


if __name__ == '__main__':
    unittest.main()
