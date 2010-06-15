import unittest
from robot.utils.asserts import assert_true, assert_raises

from robotide.application.chiefcontroller import ChiefController
from robotide.namespace import Namespace

from resources import MINIMAL_SUITE_PATH, RESOURCE_PATH
from robot.errors import DataError


class _FakeObserver(object):

    def notify(self):
        pass

    def finished(self):
        self.finished = True


class TestDataLoading(unittest.TestCase):

    def setUp(self):
        self.ctrl = ChiefController(Namespace())
        self.load_observer = _FakeObserver()

    def test_loading_suite(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)

    def test_loading_resource(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])

    def test_loading_invalid_data(self):
        assert_raises(DataError, self._load, 'invalid')

    def _load(self, path):
        self.ctrl.load_data(self.load_observer, path)
        assert_true(self.load_observer.finished)


if __name__ == "__main__":
    unittest.main()
