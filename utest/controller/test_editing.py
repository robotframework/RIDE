import unittest

from robot.parsing.model import TestCaseFile
from robot.parsing.populators import FromFilePopulator
from robot.utils.asserts import assert_equals

from robotide.controller.filecontroller import TestCaseFileController
from robotide.controller.tablecontrollers import TestCaseController, \
    TestCaseTableController
from robotide.controller.commands import RowAdd, Purify, CellValueChanged,\
    RowDelete


data = '''Test With two Steps
  Step 1
  Step 2
  Foo  # this is a comment
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

    def setUp(self):
        self._steps = None
        self._ctrl = testcase_controller()
        self._ctrl.add_test_changed_listener(self._test_changed)
        self._orig_number_of_steps = len(self._ctrl.steps)

    def test_changing_one_cell(self):
        self._exec(CellValueChanged(0, 0, 'Changed Step'))
        assert_equals(self._steps[0].keyword, 'Changed Step')

    def test_changing_cell_value_after_last_column_adds_empty_columns(self):
        self._exec(CellValueChanged(0, 2, 'Hello'))
        assert_equals(self._steps[0].args, ['', 'Hello'])

    def test_changing_cell_value_after_last_row_adds_empty_rows(self):
        self._exec(CellValueChanged(10, 0, 'Hello'))
        assert_equals(self._steps[10].keyword, 'Hello')

    def test_deleting_row(self):
        self._exec(RowDelete(0))
        assert_equals(len(self._steps), self._orig_number_of_steps-1)
    
    def test_adding_row_last(self):
        self._exec(RowAdd())
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[self._orig_number_of_steps].as_list(), [])
    
    def test_adding_row_first(self):
        self._exec(RowAdd(0))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[0].as_list(), [])
    
    def test_adding_row_middle(self):
        self._exec(RowAdd(1))
        assert_equals(len(self._steps), self._orig_number_of_steps+1)
        assert_equals(self._steps[1].as_list(), [])

    def test_purify_removes_empty_rows(self):
        self._exec(RowAdd())
        self._exec(RowAdd(1))
        self._exec(RowAdd(2))
        assert_equals(len(self._steps), self._orig_number_of_steps+3)
        self._exec(Purify())
        assert_equals(len(self._steps), self._orig_number_of_steps)

    def test_purify_removes_rows_with_no_data(self):
        self._exec(CellValueChanged(0,0, ''))
        self._exec(Purify())
        assert_equals(len(self._steps), self._orig_number_of_steps-1)

    def test_can_add_values_to_empty_row(self):
        self._exec(RowAdd())
        self._exec(CellValueChanged(0, 2, 'HELLO'))
        assert_equals(self._steps[0].args, ['', 'HELLO']) 

    def test_only_comment_is_left(self):
        self._exec(CellValueChanged(2, 0, ''))
        self._exec(Purify())
        assert_equals(self._steps[2].as_list(), ['# this is a comment'])

    def _exec(self, command):
        self._ctrl.execute(command)

    def _test_changed(self, new_test):
        self._steps = new_test.steps

if __name__ == "__main__":
    unittest.main()