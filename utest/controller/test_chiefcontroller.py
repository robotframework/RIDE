import unittest
from robot.utils.asserts import assert_true, assert_equals

from robotide.controller import ChiefController
from robotide.namespace import Namespace
from robotide.controller.filecontroller import TestCaseFileController,\
    TestDataDirectoryController

from resources import COMPLEX_SUITE_PATH, FakeLoadObserver, SUITEPATH


class ChiefControllerTest(unittest.TestCase):

    def test_dirtyness(self):
        ctrl = ChiefController(Namespace())
        ctrl.load_data(FakeLoadObserver(), COMPLEX_SUITE_PATH)
        assert_true(not ctrl.is_dirty())
        ctrl.data.new_test('newnessness')
        assert_true(ctrl.is_dirty())

    def test_load_dirty_controllers(self):
        ctrl = ChiefController(Namespace())
        ctrl.load_data(FakeLoadObserver(), SUITEPATH)
        assert_equals(len(ctrl._get_all_dirty_controllers()), 0)
        tcf = self._find_suite_by_type(ctrl.data.children, TestCaseFileController)
        tcf.new_test('newnessness')
        assert_equals(len(ctrl._get_all_dirty_controllers()), 1)
        ctrl.data.set_format('html')
        assert_equals(len(ctrl._get_all_dirty_controllers()), 2)
        sub_dir = self._find_suite_by_type(ctrl.data.children, TestDataDirectoryController)
        sub_dir_tcf = self._find_suite_by_type(sub_dir.children, TestCaseFileController)
        sub_dir_tcf.new_test('newnessness')
        assert_equals(len(ctrl._get_all_dirty_controllers()), 3)


    def _find_suite_by_type(self, suites, type):
        for child in suites:
            if isinstance(child, type):
                return child
        return None


if __name__ == "__main__":
    unittest.main()
