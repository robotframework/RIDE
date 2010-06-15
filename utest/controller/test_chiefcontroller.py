import unittest
from robot.utils.asserts import assert_true

from robotide.controller import ChiefController
from robotide.namespace import Namespace

from resources import COMPLEX_SUITE_PATH, FakeLoadObserver


class ChiefControllerTest(unittest.TestCase):

    def test_dirtyness(self):
        ctrl = ChiefController(Namespace())
        ctrl.load_data(FakeLoadObserver(), COMPLEX_SUITE_PATH)
        assert_true(not ctrl.is_dirty())
        ctrl.data.new_test('newnessness')
        assert_true(ctrl.is_dirty())


if __name__ == "__main__":
    unittest.main()
