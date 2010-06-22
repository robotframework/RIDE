import unittest
import StringIO
from robot.utils.asserts import assert_true, assert_raises_with_msg, assert_equals

from robotide.controller import ChiefController
from robotide.namespace import Namespace

from resources import MINIMAL_SUITE_PATH, RESOURCE_PATH, FakeLoadObserver
from robot.errors import DataError


class RecordingLogger(object):
    def __init__(self):
        self._log = StringIO.StringIO()
    def error(self, msg):
        self._log.write(msg)
    @property
    def message(self):
        return self._log.getvalue()


class TestDataLoading(unittest.TestCase):

    def setUp(self):
        self.logger = RecordingLogger()
        self.ctrl = ChiefController(Namespace(), self.logger)
        self.load_observer = FakeLoadObserver()

    def test_loading_suite(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)

    def test_loading_resource(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])

    def test_loading_invalid_data(self):
        msg = "Given file 'invalid' is not a valid Robot Framework test case or resource file."
        self._load('invalid')
        assert_equals(self.logger.message, msg)

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
