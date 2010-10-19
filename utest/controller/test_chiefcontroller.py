import unittest
from robot.utils.asserts import assert_true, assert_equals, assert_none


from robotide.controller import ChiefController
from robotide.namespace import Namespace
from robotide.controller.filecontroller import TestCaseFileController, \
    TestDataDirectoryController
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideOpenSuite, RideOpenResource

from resources import (COMPLEX_SUITE_PATH, MINIMAL_SUITE_PATH, RESOURCE_PATH,
                       MessageRecordingLoadObserver, SUITEPATH)


class NoneData(object):
    path = None

class PublisherListener(object):

    def __init__(self, topic):
        PUBLISHER.subscribe(self._listener, topic, self)
        self._topic = topic
        self.data = NoneData()
        self.count = 0

    def _listener(self, data):
        self.data = data
        self.count += 1

    def unsuscribe(self):
        PUBLISHER.unsubscribe(self._listener, self._topic, self)

class ChiefControllerTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = ChiefController(Namespace())
        self.load_observer = MessageRecordingLoadObserver()
        self.suite_listener = PublisherListener(RideOpenSuite)
        self.resource_listener = PublisherListener(RideOpenResource)

    def tearDown(self):
        self.suite_listener.unsuscribe()
        self.resource_listener.unsuscribe()

    def test_loading_suite_at_startup(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)
        self._test_listeners(MINIMAL_SUITE_PATH, None)

    def _test_listeners(self, suite_path, resource_path):
        assert_equals(self.suite_listener.data.path, suite_path)
        assert_equals(self.suite_listener.count, 1 if suite_path else 0)
        assert_equals(self.resource_listener.data.path, resource_path)
        assert_equals(self.resource_listener.count, 1 if resource_path else 0)

    def test_loading_resource_at_startup(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])
        self._test_listeners(None, RESOURCE_PATH)

    def test_loading_invalid_data_at_startup(self):
        msg = "Given file 'invalid' is not a valid Robot Framework test case or resource file."
        self.ctrl.load_data('invalid', self.load_observer)
        assert_true(self.load_observer.finished)
        assert_equals(self.load_observer.message, msg)
        self._test_listeners(None, None)

    def _load(self, path):
        self.ctrl.load_data(path, self.load_observer)
        assert_true(self.load_observer.notified)
        assert_true(self.load_observer.finished)

    def test_loading_datafile(self):
        data = self.ctrl.load_datafile(MINIMAL_SUITE_PATH, self.load_observer)
        assert_true(self.load_observer.finished)
        assert_true(data is not None)
        self._test_listeners(MINIMAL_SUITE_PATH, None)

    def test_loading_resource_file(self):
        resource = self.ctrl.load_resource(RESOURCE_PATH, self.load_observer)
        assert_true(self.load_observer.finished)
        assert_true(resource is not None)
        self._test_listeners(None, RESOURCE_PATH)

    def test_loading_invalid_datafile(self):
        self.ctrl.load_datafile('invalid', self.load_observer)
        assert_equals(self.load_observer.message, "Invalid data file 'invalid'.")
        self._test_listeners(None, None)

    def test_loading_invalid_resource(self):
        assert_none(self.ctrl.load_resource('invalid', self.load_observer))
        assert_equals(self.load_observer.message, "Invalid resource file 'invalid'.")
        self._test_listeners(None, None)

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
