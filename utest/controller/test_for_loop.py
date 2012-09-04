import unittest
import datafilereader
from robotide.controller.cellinfo import CellType
from robotide.controller.commands import MoveRowsDown, Undo, ChangeCellValue
from robotide.controller.stepcontrollers import ForLoopStepController


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
        pass

    def test_removing_step_from_for_loop(self):
        pass

    def test_modifying_step_in_for_loop(self):
        pass


if __name__ == '__main__':
    unittest.main()
