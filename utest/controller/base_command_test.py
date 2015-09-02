import unittest
import os
from nose.tools import assert_equals

from robotide.publish import PUBLISHER
from robotide.publish.messages import RideItemStepsChanged
from controller.controller_creator import (
    _FakeProject, testcase_controller, BASE_DATA)


class TestCaseCommandTest(unittest.TestCase, _FakeProject):

    resource_file_controller_factory = None

    def setUp(self):
        self._steps = None
        self._data = self._create_data()
        self._ctrl = testcase_controller(self, data=self._data)
        PUBLISHER.subscribe(self._test_changed, RideItemStepsChanged)
        self._orig_number_of_steps = len(self._ctrl.steps)
        self._number_of_test_changes = 0

    def tearDown(self):
        if os.path.exists('path'):
            os.removedirs('path')

    def _create_data(self):
        return BASE_DATA[:]

    def save(self, controller):
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
