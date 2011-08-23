import unittest
import datafilereader
from robotide.controller.commands import MoveRowsDown


class TestForLoop(unittest.TestCase):

    def test_for_loop_move(self):
        chief = datafilereader.construct_chief_controller(datafilereader.FOR_LOOP_PATH)
        test = chief.datafiles[1].tests[0]
        test.execute(MoveRowsDown([0]))
        test.execute(MoveRowsDown([1]))
        test.get_cell_info(1,1)

if __name__ == '__main__':
    unittest.main()
