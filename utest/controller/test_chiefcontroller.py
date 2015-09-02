import os
from os.path import join as j
import unittest
from nose.tools import assert_true, assert_equals, assert_is_none

from robotide.robotapi import TestDataDirectory, TestCaseFile, ResourceFile
from robotide.controller import Project
from robotide.namespace import Namespace
from robotide.controller.filecontrollers import TestCaseFileController, \
    TestDataDirectoryController, ResourceFileController
from robotide.publish.messages import RideOpenSuite, RideOpenResource
from robotide.spec.librarymanager import LibraryManager

from resources import (COMPLEX_SUITE_PATH, MINIMAL_SUITE_PATH, RESOURCE_PATH,
                       MessageRecordingLoadObserver, SUITEPATH,
                       DATAPATH, RELATIVE_PATH_TO_RESOURCE_FILE,
                       RESOURCE_PATH2, RESOURCE_PATH3, RESOURCE_PATH_TXT,
                       EXTERNAL_RES_UNSORTED_PATH, FakeSettings)
from resources.mocks import PublisherListener
import datafilereader


ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS = [RESOURCE_PATH, RESOURCE_PATH2, RESOURCE_PATH3, RESOURCE_PATH_TXT]


def _library_manager():
    library_manager = LibraryManager(':memory:')
    library_manager.create_database()
    return library_manager

class ProjectTest(unittest.TestCase):

    def setUp(self):
        self._library_manager = _library_manager()
        self.ctrl = Project(Namespace(FakeSettings()), FakeSettings(), self._library_manager)
        self.load_observer = MessageRecordingLoadObserver()
        self.suite_listener = PublisherListener(RideOpenSuite)
        self.resource_listener = PublisherListener(RideOpenResource)

    def tearDown(self):
        self.suite_listener.unsubscribe()
        self.resource_listener.unsubscribe()
        self.ctrl.close()
        self._library_manager.stop()

    def test_loading_suite_at_startup(self):
        self._load(MINIMAL_SUITE_PATH)
        assert_true(self.ctrl._controller is not None)
        self._test_listeners([MINIMAL_SUITE_PATH], [])

    def _test_listeners(self, suite_paths, resource_paths):
        self.assertEqual(self._get_paths(self.suite_listener.data), suite_paths)
        self.assertEqual(self._get_paths(self.resource_listener.data), resource_paths)

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

    def test_reloading(self):
        self.ctrl.new_file_project(MINIMAL_SUITE_PATH)
        files1 = self.ctrl.datafiles
        self.ctrl.new_file_project(MINIMAL_SUITE_PATH)
        files2 = self.ctrl.datafiles
        assert_true(files1 != files2)

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
        assert_is_none(self.ctrl.load_resource('invalid', self.load_observer))
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
        self.ctrl.data.mark_dirty()
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

    def test_load_data_with_external_resources_all_externals_are_used(self):
        are_used = []
        def handle(message):
            are_used.append(message.datafile.is_used())
        self.resource_listener.outer_listener = handle
        self._load(EXTERNAL_RES_UNSORTED_PATH)
        assert_true(self.ctrl.resources != [])
        res_path = os.path.join(os.path.split(EXTERNAL_RES_UNSORTED_PATH)[0], 'external_resources')
        abc_path = os.path.join(res_path, 'subdirectory2', 'subsubdirectory', 'Abc.txt')
        bar_path = os.path.join(res_path, 'subdirectory2', 'bar.txt')
        foo_path = os.path.join(res_path, 'subdirectory', 'Foo.txt')
        hello_path = os.path.join(res_path, 'subdirectory2', 'subsubdirectory', 'hello.txt')
        resource_path = os.path.join(res_path, 'subdirectory2', 'Resource.txt')
        self.assertEqual(are_used, [True for _ in range(5)])
        self._test_listeners([EXTERNAL_RES_UNSORTED_PATH], [abc_path, bar_path, foo_path, hello_path, resource_path])

    def test_sort_external_resources(self):
        self.ctrl.load_data(EXTERNAL_RES_UNSORTED_PATH, MessageRecordingLoadObserver())
        assert_equals([res.name for res in self.ctrl.external_resources], ["Abc", "Bar", "Foo", "Hello", "Resource"])

    def test_datafiles_property_with_resource_file_only(self):
        resource = self.ctrl.load_resource(RESOURCE_PATH, self.load_observer)
        assert_equals(self.ctrl.datafiles[0], resource)

    def test_get_all_keywords_with_resource_file_only(self):
        project = datafilereader.construct_project(RESOURCE_PATH)
        all_kws = project.get_all_keywords()
        project.close()
        res_kws = [kw for kw in all_kws if kw.name == 'Resource UK']
        assert_equals(len(res_kws), 1)

    def test_resource_import_modified(self):
        self.ctrl.resource_import_modified(RELATIVE_PATH_TO_RESOURCE_FILE, DATAPATH)
        self._test_listeners([], ALL_RESOURCE_PATH_RELATED_RESOURCE_IMPORTS)


def _data_directory(path):
    data = TestDataDirectory()
    data.source = data.directory = os.path.normpath(path)
    return data

def _testcasefile(path):
    data = TestCaseFile()
    data.source = os.path.normpath(path)
    return data


class TestResolvingResourceDirectories(unittest.TestCase):

    def setUp(self):
        self.project = Project(Namespace(FakeSettings()), FakeSettings(), _library_manager())

    def tearDown(self):
        self.project.close()

    def test_resource_file_outside_of_topsuite_is_an_external_resource(self):
        self._set_data_directory_controller('suite')
        self._set_resources(j('foo','resource.txt'))
        assert_equals(self.project.external_resources, self.project.resources)

    def _set_data_directory_controller(self, dir):
        self.project._controller = TestDataDirectoryController(_data_directory(dir))

    def test_resource_file_in_own_directory_is_added_to_top_suite(self):
        self._set_data_directory_controller('foo')
        self._set_resources(j('foo','bar','quux.txt'))
        self._assert_resource_dir_was_created_as_child_of(self.project.data)
        self._assert_resource_dir_contains_resources()
        assert_true(len(self.project.external_resources)==  0)

    def test_two_resource_in_same_directory_get_same_parent(self):
        self._set_data_directory_controller('foo')
        self._set_resources(j('foo','bar','quux.txt'), j('foo','bar','zap.txt'))
        self._assert_resource_dir_was_created_as_child_of(self.project.data)
        self._assert_resource_dir_contains_resources()

    def test_two_nested_resources_in_same_directory_get_same_parent(self):
        self._set_data_directory_controller('suite')
        self._set_resources(j('suite','foo','bar','quux.txt'), j('suite','foo','bar','zap.txt'))
        assert_equals(self.project.data.children[0].children[0].children,
                      self.project.resources)

    def test_resource_directory_gets_nearest_possible_parent(self):
        self._set_data_directory_controller('tmp')
        self.project.data.add_child(TestDataDirectoryController(_data_directory(j('tmp','some'))))
        self._set_resources(j('tmp','some','resoruces','res.txt'))
        assert_equals(len(self.project.data.children), 1)
        assert_equals(len(self.project.data.children[0].children), 1)
        assert_equals(self.project.data.children[0].children[0].children, [self.project.resources[0]])

    def test_nested_resource_directories(self):
        self._set_data_directory_controller('tmp')
        self._set_resources(j('tmp','resoruces','res.txt'), j('tmp','resoruces','more','res.txt'))
        assert_equals(len(self.project.data.children), 1)
        assert_equals(len(self.project.data.children[0].children), 2)
        assert_equals(self.project.data.children[0].children[1].children, [self.project.resources[1]])

    def test_resource_in_nested_directory(self):
        self._set_data_directory_controller('tmp')
        self._set_resources(j('tmp','res','ources','res.txt'))
        assert_equals(len(self.project.data.children), 1)
        assert_equals(len(self.project.data.children[0].children), 1)
        assert_equals(self.project.data.children[0].children[0].children, [self.project.resources[0]])
        assert_true(len(self.project.external_resources)==  0)

    def _set_resources(self, *paths):
        for p in paths:
            resource = ResourceFileController(ResourceFile(os.path.normpath(p)))
            self.project.resources.append(resource)
            self.project.insert_into_suite_structure(resource)

    def _assert_resource_dir_was_created_as_child_of(self, ctrl):
        assert_equals(len(ctrl.children), 1)

    def _assert_resource_dir_contains_resources(self):
        assert_equals(self.project.data.children[0].children, self.project.resources)


class TestFindingControllers(unittest.TestCase):

    def setUp(self):
        self.project = Project(Namespace(FakeSettings()), FakeSettings(), _library_manager())

    def tearDown(self):
        self.project.close()

    def test_finding_root_directory_controller(self):
        self.project._controller = TestDataDirectoryController(_data_directory('Root'))
        result = self.project.find_controller_by_longname('Root')
        assert_equals(result, self.project._controller)

    def test_finding_subdirectory_controller(self):
        directory_controller = TestDataDirectoryController(_data_directory('Root'))
        subdirectory_controller = TestDataDirectoryController(_data_directory('Sub.suite'))
        directory_controller.add_child(subdirectory_controller)
        self.project._controller = directory_controller
        result = self.project.find_controller_by_longname('Root.Sub.suite')
        assert_equals(result, subdirectory_controller)

    def test_finding_testcase_controller(self):
        suite_controller = TestCaseFileController(_testcasefile('Suite.txt'))
        test = suite_controller.create_test('Test 1')
        self.project._controller = suite_controller
        result = self.project.find_controller_by_longname('Suite.Test 1', 'Test 1')
        assert_equals(result, test)

    def test_finding_correct_testcase_when_two_with_same_name(self):
        test1, test2 = self._create_suite_structure_with_two_tests_with_same_name()
        result1 = self.project.find_controller_by_longname('Ro.ot.'+test1.longname, test1.display_name)
        assert_equals(result1, test1)
        result2 = self.project.find_controller_by_longname('Ro.ot.'+test2.longname, test2.display_name)
        assert_equals(result2, test2)

    def test_finding_correct_testcase_when_two_files_with_same_name_start(self):
        directory_controller = TestDataDirectoryController(_data_directory('t'))
        suite1_controller = TestCaseFileController(_testcasefile('test.txt'))
        test1 = suite1_controller.create_test('A')
        suite2_controller = TestCaseFileController(_testcasefile('test2.txt'))
        test2 = suite2_controller.create_test('A')
        directory_controller.add_child(suite1_controller)
        directory_controller.add_child(suite2_controller)
        self.project._controller = directory_controller
        result1 = self.project.find_controller_by_longname('T.'+test1.longname, test1.display_name)
        assert_equals(result1, test1)
        result2 = self.project.find_controller_by_longname('T.'+test2.longname, test2.display_name)
        assert_equals(result2, test2)

    def _create_suite_structure_with_two_tests_with_same_name(self):
        directory_controller = TestDataDirectoryController(_data_directory('Ro.ot'))
        suite1_controller = TestCaseFileController(_testcasefile('Suite.1.txt'))
        test1 = suite1_controller.create_test('Te.st')
        suite2_controller = TestCaseFileController(_testcasefile('Suite.2.txt'))
        test2 = suite2_controller.create_test('Te.st')
        directory_controller.add_child(suite1_controller)
        directory_controller.add_child(suite2_controller)
        self.project._controller = directory_controller
        return test1, test2

if __name__ == "__main__":
    unittest.main()
