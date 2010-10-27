import unittest
from robot.parsing import TestCase
from robot.parsing.model import TestCaseFile, TestDataDirectory
from robot.utils.asserts import (assert_equals, assert_true, assert_false)

from robotide.controller.filecontrollers import TestCaseFileController, TestDataDirectoryController
from robotide.controller.settingcontrollers import *
from robotide.controller.tablecontrollers import _WithListOperations
from robotide.controller.tablecontrollers import *
from robotide.controller import NewDatafile

from resources import SUITEPATH


class TestCaseFileControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = self._file_ctrl()
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(ctrl.settings), 9)
        assert_false(ctrl.dirty)

    def test_has_format(self):
        ctrl = self._file_ctrl()
        assert_true(ctrl.has_format())
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_true(ctrl.has_format())

    def test_get_format(self):
        ctrl = self._file_ctrl()
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.get_format(), 'html')

    def test_set_format(self):
        ctrl = self._file_ctrl()
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.html')
        ctrl.set_format('txt')
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.txt')

    def test_add_test_or_kw(self):
        ctrl = self._file_ctrl()
        assert_equals(len(ctrl.tests), 0)
        new_test = TestCaseController(ctrl, TestCase(TestCaseFile(), 'New test'))
        ctrl.add_test_or_keyword(new_test)
        assert_equals(len(ctrl.tests), 1)
        assert_true(ctrl.tests[0]._test.parent is ctrl.datafile)
        assert_true(ctrl.dirty)

    def test_new_test(self):
        test_ctrl = self._file_ctrl().create_test('Foo')
        assert_equals(test_ctrl.name, 'Foo')

    def test_create_keyword(self):
        kw_ctrl = self._file_ctrl().create_keyword('An UK')
        assert_equals(kw_ctrl.name, 'An UK')

    def test_create_keyword_with_args(self):
        kw_ctrl = self._file_ctrl().create_keyword('UK', '${a1} | ${a2}')
        assert_equals(kw_ctrl.name, 'UK')
        assert_equals(kw_ctrl.data.args.value, ['${a1}', '${a2}'])

    def _file_ctrl(self):
        return TestCaseFileController(TestCaseFile())


class TestDataDirectoryControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(ctrl.settings), 6)

    def test_has_format(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        assert_false(ctrl.has_format())
        ctrl.mark_dirty()
        assert_false(ctrl.has_format())
        ctrl.data.initfile = '/tmp/__init__.html'
        assert_true(ctrl.has_format())

    def test_set_format(self):
        dir = TestDataDirectory()
        dir.source = '/tmp/'
        ctrl = TestDataDirectoryController(dir)
        assert_false(ctrl.has_format())
        ctrl.set_format('txt')
        assert_true(ctrl.has_format())
        assert_equals(ctrl.source, '/tmp/__init__.txt')

    def test_adding_new_child(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        assert_true(ctrl.new_datafile(NewDatafile('path/to/data.txt',
                                                  is_dir_type=False)))


class DatafileIteratorTest(unittest.TestCase):

    def setUp(self):
        test_data_suite = TestDataDirectory(source=SUITEPATH)
        self.directory_controller = TestDataDirectoryController(test_data_suite)

    def test_iterate_all(self):
        class Checker(object):
            def __init__(self):
                self.iteration_count = 0
                self.in_sub_dir = False
            def __call__(self, controller):
                self.iteration_count += 1
                if controller.source and controller.source.endswith('test.txt'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df in self.directory_controller.iter_datafiles()]
        assert_true(check_count_and_sub_dir.iteration_count == 5)
        assert_true(check_count_and_sub_dir.in_sub_dir)
