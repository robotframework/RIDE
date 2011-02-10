import unittest
from robot.parsing.model import TestCaseFile
from robot.parsing.populators import FromFilePopulator
from robot.utils.asserts import assert_equals

from robotide.publish import PUBLISHER
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.publish.messages import RideItemStepsChanged

TEST_NAME = 'Test With two Steps'
STEP1_KEYWORD = 'Step 1'
STEP1 = '  '+STEP1_KEYWORD+'  arg'
STEP2 = '  Step 2  a1  a2  a3'
STEP_WITH_COMMENT = '  Foo  # this is a comment'
FOR_LOOP_HEADER = '  : FOR  ${i}  IN  1  2  3'
FOR_LOOP_STEP1 = '    Log  ${i}'
FOR_LOOP_STEP2 = '    No Operation'
STEP_AFTER_FOR_LOOP = '  Step bar'

_base_data = [TEST_NAME,
        STEP1,
        STEP2,
        STEP_WITH_COMMENT,
        FOR_LOOP_HEADER,
        FOR_LOOP_STEP1,
        FOR_LOOP_STEP2,
        STEP_AFTER_FOR_LOOP,
        '  ${variable}=  some value'
]

class _FakeChief(object):

    def update_namespace(self):
        pass

    def register_for_namespace_updates(self, listener):
        pass

    def unregister_namespace_updates(self, listener):
        pass

def create(data):
    tcf = TestCaseFile()
    tcf.directory = '/path/to'
    pop = FromFilePopulator(tcf)
    pop.start_table(['Test cases'])
    for row in [ [cell for cell in line.split('  ')] for line in data]:
        pop.add(row)
    pop.eof()
    return tcf


def testcase_controller(chief=None, data=None):
    if data is None:
        data = _base_data[:]
    tcf = create(data)
    tcf_controller = TestCaseFileController(tcf, chief)
    tctablectrl = tcf_controller.tests
    return tctablectrl[0]


class TestCaseCommandTest(unittest.TestCase, _FakeChief):

    def setUp(self):
        self._steps = None
        self._data = self._create_data()
        self._ctrl = testcase_controller(self, data=self._data)
        PUBLISHER.subscribe(self._test_changed, RideItemStepsChanged)
        self._orig_number_of_steps = len(self._ctrl.steps)
        self._number_of_test_changes = 0

    def _create_data(self):
        return _base_data[:]

    def serialize_controller(self, controller):
        self._file_saved = (controller == self._ctrl.datafile_controller)

    def tearDown(self):
        PUBLISHER.unsubscribe(self._test_changed, RideItemStepsChanged)

    def _get_macros(self):
        return [m for m in self._ctrl._parent]

    def _get_macro_by_name(self, name):
        return [m for m in self._get_macros() if m.name == name][0]

    def _data_row(self, line):
        return self._data.index(line)-1

    def _data_step_as_list(self, step_data):
        return step_data.split('  ')[1:]

    def _exec(self, command):
        return self._ctrl.execute(command)

    def _test_changed(self, data):
        self._number_of_test_changes += 1
        self._steps = data.item.steps

    def _verify_step_unchanged(self, step_data):
        row = self._data_row(step_data)
        assert_equals(self._steps[row].as_list(), self._data_step_as_list(step_data))

    def _verify_steps_unchanged(self, *steps):
        for step in steps:
            self._verify_step_unchanged(step)

    def _verify_number_of_test_changes(self, expected):
        assert_equals(self._number_of_test_changes, expected)

    def _verify_row_does_not_exist(self, line):
        for step in self._steps:
            if step.as_list() == self._data_step_as_list(line):
                raise AssertionError('Row "%s" exists' % line)

    def _verify_step_is_empty(self, index):
        assert_equals(self._steps[index].as_list(), [])

    def _verify_step(self, index, exp_name, exp_args=[], exp_comment=None):
        exp = [exp_name] + exp_args
        if exp_comment:
            exp += [exp_comment]
        assert_equals(self._steps[index].as_list(), exp)

    def _verify_step_number_change(self, change):
        assert_equals(len(self._steps), self._orig_number_of_steps + change)
