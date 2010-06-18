import unittest
import os
import tempfile
from robot.utils.asserts import (assert_true, assert_false, assert_equals,
                                 assert_not_equal)
from robot.parsing.model import TestCaseFile, TestDataDirectory, ResourceFile

from robotide.controller.filecontroller import (TestCaseFileController,
                                                TestDataDirectoryController,
                                                ResourceFileController)
from robotide.controller import ChiefController

DIRPATH = os.path.join(tempfile.gettempdir(), 'ride_controller_utest_dir')
if not os.path.exists(DIRPATH):
    os.mkdir(DIRPATH)
FILEPATH = os.path.join(DIRPATH, 'tests.txt')
RESOURCEPATH = os.path.join(DIRPATH, 'resource.txt')
INITPATH = os.path.join(DIRPATH, '__init__.txt')


class TestModifiedOnDiskWithFileSuite(unittest.TestCase):

    def setUp(self):
        open(FILEPATH, 'w').write('*Test Cases*\nRide Unit Test  No Operation\n')

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
                                      ChiefController(None))
        os.utime(FILEPATH, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())
        ctrl.save()
        assert_false(ctrl.has_been_modified_on_disk())


class TestModifiedOnDiskWithDirectorySuite(unittest.TestCase):

    def setUp(self):
        open(FILEPATH, 'w').write('*Test Cases*\nRide Unit Test  No Operation\n')
        open(INITPATH, 'w').write('*Settings*\nDocumentation  Ride unit testing file\n')

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


class TestModifiedOnDiskWithresource(unittest.TestCase):

    def setUp(self):
        open(RESOURCEPATH, 'w').write('*Keywords*\nUnit Test Keyword  No Operation\n')

    def test_reload_with_resource(self):
        ctrl = ResourceFileController(ResourceFile(source=RESOURCEPATH))
        assert_equals(len(ctrl.keywords), 1)
        open(RESOURCEPATH, 'a').write('Ninjaed Keyword  Log  I am taking over!\n')
        ctrl.reload()
        assert_equals(len(ctrl.keywords), 2)
        assert_equals(ctrl.keywords[-1].name, 'Ninjaed Keyword')


if __name__ == "__main__":
    unittest.main()
