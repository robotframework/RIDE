import os
import unittest

from robot.parsing.model import TestDataDirectory, ResourceFile
from robot.utils.asserts import assert_true, assert_equals, assert_none

from robotide.controller import ChiefController
from robotide.namespace import Namespace
from robotide.controller.filecontrollers import TestCaseFileController, \
    TestDataDirectoryController, ResourceFileController
from robotide.publish.messages import RideOpenSuite, RideOpenResource

from resources import (COMPLEX_SUITE_PATH, MINIMAL_SUITE_PATH, RESOURCE_PATH,
                       MessageRecordingLoadObserver, SUITEPATH,
                       DATAPATH, RELATIVE_PATH_TO_RESOURCE_FILE,
                       RESOURCE_PATH2, RESOURCE_PATH3, RESOURCE_PATH_TXT)
from resources.mocks import PublisherListener
import datafilereader


ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS = [RESOURCE_PATH, RESOURCE_PATH2, RESOURCE_PATH3, RESOURCE_PATH_TXT]


class ChiefControllerTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = ChiefController(Namespace())
        self.load_observer = MessageRecordingLoadObserver()
        self.suite_listener = PublisherListener(RideOpenSuite)
        self.resource_listener = PublisherListener(RideOpenResource)

    def tearDown(self):
        self.suite_listener.unsubscribe()
        self.resource_listener.unsubscribe()

    def test_loading_suite_at_startup(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)
        self._test_listeners([MINIMAL_SUITE_PATH], [])

    def _test_listeners(self, suite_paths, resource_paths):
        assert_equals(self._get_paths(self.suite_listener.data), suite_paths)
        assert_equals(self._get_paths(self.resource_listener.data), resource_paths)

    def _get_paths(self, data):
            return [item.path for item in data]

    def test_loading_resource_at_startup(self):
        self._load(RESOURCE_PATH)
        assert_true(self.ctrl.resources != [])
        self._test_listeners([], ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS)

    def test_loading_invalid_data_at_startup(self):
        msg = "Given file 'invalid' is not a valid Robot Framework test case or resource file."
        self.ctrl.load_data('invalid', self.load_observer)
        assert_true(self.load_observer.finished)
        assert_equals(self.load_observer.message, msg)
        self._test_listeners([], [])

    def _load(self, path):
        self.ctrl.load_data(path, self.load_observer)
        assert_true(self.load_observer.notified)
        assert_true(self.load_observer.finished)

    def test_loading_datafile(self):
        data = self.ctrl.load_datafile(MINIMAL_SUITE_PATH, self.load_observer)
        assert_true(self.load_observer.finished)
        assert_true(data is not None)
        self._test_listeners([MINIMAL_SUITE_PATH], [])

    def test_loading_resource_file(self):
        resource = self.ctrl.load_resource(RESOURCE_PATH, self.load_observer)
        assert_true(self.load_observer.finished)
        assert_true(resource is not None)
        self._test_listeners([], ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS)

    def test_loading_invalid_datafile(self):
        self.ctrl.load_datafile('invalid', self.load_observer)
        assert_equals(self.load_observer.message, "Invalid data file 'invalid'.")
        self._test_listeners([], [])

    def test_loading_invalid_resource(self):
        assert_none(self.ctrl.load_resource('invalid', self.load_observer))
        assert_equals(self.load_observer.message, "Invalid resource file 'invalid'.")
        self._test_listeners([], [])

    def test_dirtyness(self):
        self.ctrl.load_data(COMPLEX_SUITE_PATH, MessageRecordingLoadObserver())
        assert_true(not self.ctrl.is_dirty())
        self.ctrl.data.create_test('newnessness')
        assert_true(self.ctrl.is_dirty())

    def test_load_dirty_controllers(self):
        self.ctrl.load_data(SUITEPATH, MessageRecordingLoadObserver())
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 0)
        tcf = self._find_suite_by_type(self.ctrl.data.children, TestCaseFileController)
        tcf.create_test('newnessness')
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 1)
        self.ctrl.data.set_format('html')
        assert_equals(len(self.ctrl._get_all_dirty_controllers()), 2)
        sub_dir = self._find_suite_by_type(self.ctrl.data.children, TestDataDirectoryController)
        sub_dir_tcf = self._find_suite_by_type(sub_dir.children, TestCaseFileController)
        sub_dir_tcf.create_test('newnessness')
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

    def test_datafiles_property_with_resource_file_only(self):
        resource = self.ctrl.load_resource(RESOURCE_PATH, self.load_observer)
        assert_equals(self.ctrl.datafiles[0], resource)

    def test_get_all_keywords_with_resource_file_only(self):
        chief = datafilereader.construct_chief_controller(RESOURCE_PATH)
        all_kws = chief.get_all_keywords()
        res_kws = [kw for kw in all_kws if kw.name == 'Resource UK']
        assert_equals(len(res_kws), 1)

    def test_resource_import_modified(self):
        self.ctrl.resource_import_modified(RELATIVE_PATH_TO_RESOURCE_FILE, DATAPATH)
        self._test_listeners([], ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS)


class TestResolvingResourceDirectories(unittest.TestCase):

    def setUp(self):
        self.chief = ChiefController(Namespace())

    def test_resource_file_outside_of_topsuite_is_an_external_resource(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/suite'))
        self._set_resources('/foo/resource.txt')
        assert_equals(self.chief.external_resources, self.chief.resources)

    def test_resource_file_in_own_directory_is_added_to_top_suite(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/foo'))
        self._set_resources('/foo/bar/quux.txt')
        self._assert_resource_dir_was_created_as_child_of(self.chief.data)
        self._assert_resource_dir_contains_resources()
        assert_true(len(self.chief.external_resources)==  0)

    def test_two_resource_in_same_directory_get_same_parent(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/foo'))
        self._set_resources('/foo/bar/quux.txt', '/foo/bar/zap.txt')
        self._assert_resource_dir_was_created_as_child_of(self.chief.data)
        self._assert_resource_dir_contains_resources()

    def test_two_nested_resources_in_same_directory_get_same_parent(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/suite'))
        self._set_resources('/suite/foo/bar/quux.txt', '/suite/foo/bar/zap.txt')
        assert_equals(self.chief.data.children[0].children[0].children,
                      self.chief.resources)

    def test_resource_directory_gets_nearest_possible_parent(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/tmp'))
        self.chief.data.add_child(TestDataDirectoryController(self._data_directory('/tmp/some')))
        self._set_resources('/tmp/some/resoruces/res.txt')
        assert_equals(len(self.chief.data.children), 1)
        assert_equals(len(self.chief.data.children[0].children), 1)
        assert_equals(self.chief.data.children[0].children[0].children, [self.chief.resources[0]])

    def test_nested_resource_directories(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/tmp'))
        self._set_resources('/tmp/resoruces/res.txt', '/tmp/resoruces/more/res.txt')
        assert_equals(len(self.chief.data.children), 1)
        assert_equals(len(self.chief.data.children[0].children), 2)
        assert_equals(self.chief.data.children[0].children[1].children, [self.chief.resources[1]])

    def test_resource_in_nested_directory(self):
        self.chief._controller = TestDataDirectoryController(self._data_directory('/tmp'))
        self._set_resources('/tmp/res/ources/res.txt')
        assert_equals(len(self.chief.data.children), 1)
        assert_equals(len(self.chief.data.children[0].children), 1)
        assert_equals(self.chief.data.children[0].children[0].children, [self.chief.resources[0]])
        assert_true(len(self.chief.external_resources)==  0)

    def _data_directory(self, path):
        data = TestDataDirectory()
        data.source = data.directory = os.path.normpath(path)
        return data

    def _set_resources(self, *paths):
        for p in paths:
            resource = ResourceFileController(ResourceFile(os.path.normpath(p)))
            self.chief._insert_into_suite_structure(resource)

    def _assert_resource_dir_was_created_as_child_of(self, ctrl):
        assert_equals(len(ctrl.children), 1)

    def _assert_resource_dir_contains_resources(self):
        assert_equals(self.chief.data.children[0].children, self.chief.resources)


if __name__ == "__main__":
    unittest.main()
