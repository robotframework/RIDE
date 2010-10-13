from robot.parsing.model import TestCaseFile
from robot.parsing.populators import FromFilePopulator
from robotide.controller.filecontroller import TestCaseFileController
from robotide.controller.tablecontrollers import TestCaseController, \
    TestCaseTableController
import unittest
from robot.utils.asserts import assert_equals


data = '''Test With one Step
  Step 1
'''

def create():
    tcf = TestCaseFile()
    tcf.directory = '/path/to'
    pop = FromFilePopulator(tcf)
    pop.start_table(['Test cases'])
    lines = data.splitlines()
    for row in [ [cell for cell in line.split('  ')] for line in lines]:
        pop.add(row)
    pop.eof()
    return tcf


def testcase_controller():
    tcf = create()
    tctablectrl = TestCaseTableController(TestCaseFileController(tcf),
                                          tcf.testcase_table)
    return TestCaseController(tctablectrl, tcf.testcase_table.tests[0])



class TestCaseEditingTest(unittest.TestCase):

    def test_changing_one_cell(self):
        ctrl = testcase_controller()
        ctrl.add_test_changed_listener(self._test_changed)
        ctrl.execute(CellValueChanged(0 , 0, 'Changed Step'))
        assert_equals(self._steps[0].keyword, 'Changed Step')

    def _test_changed(self, new_test):
        self._steps = new_test.steps


class CellValueChanged(object):
    def __init__(self, row, col, value):
        self._row = row
        self._col = col
        self._value = value

    def execute(self, context):
        step = context.steps[self._row]
        step.change(self._col, self._value)
        context.notify_changed()


if __name__ == "__main__":
    unittest.main()
