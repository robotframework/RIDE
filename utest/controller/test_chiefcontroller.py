import unittest
from robot.utils.asserts import assert_true, assert_equals

from robotide.controller import ChiefController
from robotide.namespace import Namespace

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
        ctrl.data.children[0].new_test('newnessness')
        assert_equals(len(ctrl._get_all_dirty_controllers()), 1)
        ctrl.data.set_format('html')
        assert_equals(len(ctrl._get_all_dirty_controllers()), 2)


if __name__ == "__main__":
    unittest.main()
