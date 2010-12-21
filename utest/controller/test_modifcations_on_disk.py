import unittest
import os
import tempfile
from robot.utils.asserts import assert_true, assert_false, assert_equals
from robot.parsing.model import TestCaseFile, TestDataDirectory, ResourceFile

from robotide.controller.filecontrollers import (TestCaseFileController,
                                                 TestDataDirectoryController,
                                                 ResourceFileController)
from robotide.controller import ChiefController
from robotide.publish.messages import RideDataFileRemoved
from robotide.publish import PUBLISHER
import shutil
from robotide.namespace.namespace import Namespace


DIRPATH = os.path.join(tempfile.gettempdir(), 'ride_controller_utest_dir')
FILEPATH = os.path.join(DIRPATH, 'tests.txt')
RESOURCEPATH = os.path.join(DIRPATH, 'resource.txt')
INITPATH = os.path.join(DIRPATH, '__init__.txt')


def create_test_data():
    if not os.path.exists(DIRPATH):
        os.mkdir(DIRPATH)
    open(FILEPATH, 'w').write('*Test Cases*\nRide Unit Test  No Operation\n')
    open(RESOURCEPATH, 'w').write('*Keywords*\nUnit Test Keyword  No Operation\n')
    open(INITPATH, 'w').write('*Settings*\nDocumentation  Ride unit testing file\n')


def remove_test_data():
    shutil.rmtree(DIRPATH)


class _DataDependentTest(unittest.TestCase):

    def setUp(self):
        create_test_data()

    def tearDown(self):
        remove_test_data()


class TestModifiedOnDiskWithFileSuite(_DataDependentTest):

    def test_mtime(self):
        ctrl = TestCaseFileController(TestCaseFile(source=FILEPATH))
        assert_false(ctrl.has_been_modified_on_disk())
        os.utime(FILEPATH, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())

    def test_size_change(self):
        os.utime(FILEPATH, None)
        ctrl = TestCaseFileController(TestCaseFile(source=FILEPATH))
        open(FILEPATH, 'a').write('#Ninja edit\n')
        assert_true(ctrl.has_been_modified_on_disk())

    def test_reload(self):
        ctrl = TestCaseFileController(TestCaseFile(source=FILEPATH))
        assert_equals(len(ctrl.tests), 1)
        open(FILEPATH, 'a').write('Second Test  Log  Hello World!\n')
        ctrl.reload()
        assert_equals(len(ctrl.tests), 2)
        assert_equals(ctrl.tests[-1].name, 'Second Test')

    def test_overwrite(self):
        ctrl = TestCaseFileController(TestCaseFile(source=FILEPATH),
                                      ChiefController(Namespace()))
        os.utime(FILEPATH, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())
        ctrl.save()
        assert_false(ctrl.has_been_modified_on_disk())


class TestModifiedOnDiskWithDirectorySuite(_DataDependentTest):

    def test_reload_with_directory_suite(self):
        ctrl = TestDataDirectoryController(TestDataDirectory(source=DIRPATH))
        open(INITPATH, 'a').write('...  ninjaed more documentation')
        ctrl.reload()
        assert_equals(ctrl.settings[0].value,
                      'Ride unit testing file ninjaed more documentation')

    def test_mtime_with_directory_suite(self):
        ctrl = TestDataDirectoryController(TestDataDirectory(source=DIRPATH))
        assert_false(ctrl.has_been_modified_on_disk())
        os.utime(INITPATH, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())


class TestModifiedOnDiskWithresource(_DataDependentTest):

    def test_reload_with_resource(self):
        ctrl = ResourceFileController(ResourceFile(source=RESOURCEPATH))
        assert_equals(len(ctrl.keywords), 1)
        open(RESOURCEPATH, 'a').write('Ninjaed Keyword  Log  I am taking over!\n')
        ctrl.reload()
        assert_equals(len(ctrl.keywords), 2)
        assert_equals(ctrl.keywords[-1].name, 'Ninjaed Keyword')


class TestDataFileRemoval(_DataDependentTest):

    def setUp(self):
        _DataDependentTest.setUp(self)
        PUBLISHER.subscribe(self._datafile_removed, RideDataFileRemoved)

    def tearDown(self):
        _DataDependentTest.tearDown(self)
        PUBLISHER.unsubscribe(self._datafile_removed, RideDataFileRemoved)

    def _datafile_removed(self, message):
        self._removed_datafile = message.datafile

    def test_deleting_source_should_remove_it_from_model(self):
        chief = ChiefController(Namespace())
        chief.new_project(TestCaseFile(source=FILEPATH))
        os.remove(FILEPATH)
        ctrl = chief.data
        ctrl.remove()
        assert_true(chief.data is None)
        assert_true(self._removed_datafile is ctrl)

    def test_deleting_file_suite_under_dir_suite(self):
        chief = ChiefController(Namespace())
        chief.new_project(TestDataDirectory(source=DIRPATH))
        file_suite = chief.data.children[0]
        file_suite.remove()
        assert_true(len(chief.data.children) == 0, 'Child suite was not removed')

    def test_deleting_resource_file(self):
        chief = ChiefController(Namespace())
        res = chief.new_resource(RESOURCEPATH)
        res.remove()
        assert_true(len(chief.resources) == 0, 'Resource was not removed')

    def test_deleting_init_file(self):
        chief = ChiefController(Namespace())
        chief.new_project(TestDataDirectory(source=DIRPATH))
        os.remove(INITPATH)
        chief.data.remove()
        open(INITPATH, 'w').write('*Settings*\nDocumentation  Ride unit testing file\n')
        assert_true(chief.data.has_format() is False, chief.data.data.initfile)


if __name__ == "__main__":
    unittest.main()
