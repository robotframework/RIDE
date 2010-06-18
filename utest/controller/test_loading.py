import unittest
from robot.utils.asserts import assert_true, assert_raises, assert_raises_with_msg

from robotide.controller import ChiefController
from robotide.namespace import Namespace

from resources import MINIMAL_SUITE_PATH, RESOURCE_PATH, FakeLoadObserver
from robot.errors import DataError


class TestDataLoading(unittest.TestCase):

    def setUp(self):
        self.ctrl = ChiefController(Namespace())
        self.load_observer = FakeLoadObserver()

    def test_loading_suite(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)

    def test_loading_resource(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])

    def test_loading_invalid_data(self):
        assert_raises(DataError, self._load, 'invalid')

    def _load(self, path):
        self.ctrl.load_data(path, self.load_observer)
        assert_true(self.load_observer.finished)

    def test_loading_invalid_datafile(self):
        assert_raises_with_msg(DataError, 'Invalid data file: invalid.',
                               self.ctrl.load_datafile, 
                               'invalid', FakeLoadObserver())

    def test_loading_invalid_resource(self):
        assert_raises_with_msg(DataError, 'Invalid resource file: invalid.',
                               self.ctrl.load_resource, 'invalid')


if __name__ == "__main__":
    unittest.main()
