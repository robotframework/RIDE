import unittest
from robot.utils.asserts import assert_true, assert_equals, assert_none

from robotide.controller import ChiefController
from robotide.namespace import Namespace

from resources import MINIMAL_SUITE_PATH, RESOURCE_PATH, MessageRecordingLoadObserver



class TestDataLoading(unittest.TestCase):

    def setUp(self):
        self.load_observer = MessageRecordingLoadObserver()
        self.ctrl = ChiefController(Namespace())

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

if __name__ == "__main__":
    unittest.main()
