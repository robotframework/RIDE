import unittest
from robot.utils.asserts import assert_true, assert_equals, assert_none

from robotide.controller import ChiefController
from robotide.namespace import Namespace
from robotide.controller.filecontroller import TestCaseFileController,\
    TestDataDirectoryController

from resources import (COMPLEX_SUITE_PATH,  MINIMAL_SUITE_PATH, RESOURCE_PATH,
                       MessageRecordingLoadObserver, SUITEPATH)


class ChiefControllerTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = ChiefController(Namespace())
        self.load_observer = MessageRecordingLoadObserver()

    def test_loading_suite(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)

    def test_loading_resource(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])

    def test_loading_invalid_data(self):
        msg = "Given file 'invalid' is not a valid Robot Framework test case or resource file."
        self._load('invalid')
        assert_equals(self.load_observer.message, msg)

    def _load(self, path):
        self.ctrl.load_data(path, self.load_observer)
        assert_true(self.load_observer.finish_called)

    def test_loading_invalid_datafile(self):
        self.ctrl.load_datafile('invalid', self.load_observer)
        assert_equals(self.load_observer.message, "Invalid data file 'invalid'.")

    def test_loading_invalid_resource(self):
        assert_none(self.ctrl.load_resource('invalid', self.load_observer))
        assert_equals(self.load_observer.message, "Invalid resource file 'invalid'.")

    def test_dirtyness(self):
        self.ctrl.load_data(COMPLEX_SUITE_PATH, MessageRecordingLoadObserver())
        assert_true(not self.ctrl.is_dirty())
        self.ctrl.data.new_test('newnessness')
        assert_true(self.ctrl.is_dirty())

    def test_load_dirty_controllers(self):
        self.ctrl.load_data(SUITEPATH, MessageRecordingLoadObserver())
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 0)
        tcf = self._find_suite_by_type(self.ctrl.data.children, TestCaseFileController)
        tcf.new_test('newnessness')
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 1)
        self.ctrl.data.set_format('html')
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 2)
        sub_dir = self._find_suite_by_type(self.ctrl.data.children, TestDataDirectoryController)
        sub_dir_tcf = self._find_suite_by_type(sub_dir.children, TestCaseFileController)
        sub_dir_tcf.new_test('newnessness')
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 3)

    def _find_suite_by_type(self, suites, type):
        for child in suites:
            if isinstance(child, type):
                return child
        return None

    def test_creating_new_resource(self):
        controller = self.ctrl.new_resource('somepath')
        assert_equals(controller.name, 'Somepath')

    def test_resource_with_same_path_is_not_added_twice(self):
        self.ctrl.new_resource('somepath')
        self.ctrl.new_resource('somepath')
        assert_equals(len(self.ctrl.resources), 1)


if __name__ == "__main__":
    unittest.main()
