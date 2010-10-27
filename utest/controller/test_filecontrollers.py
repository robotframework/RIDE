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

    SOURCE_HTML = '/tmp/.path.with.dots/test.cases.html'
    SOURCE_TXT = SOURCE_HTML.replace('.html', '.txt')

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile())
        self.ctrl.data.source = self.SOURCE_HTML

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(self.ctrl.settings), 9)
        assert_false(self.ctrl.dirty)

    def test_has_format(self):
        assert_true(self.ctrl.has_format())

    def test_get_format(self):
        assert_equals(self.ctrl.get_format(), 'html')

    def test_source(self):
        assert_equals(self.ctrl.source, self.SOURCE_HTML)

    def test_set_format(self):
        self.ctrl.set_format('txt')
        assert_equals(self.ctrl.source, self.SOURCE_TXT)

    def test_add_test_or_kw(self):
        assert_equals(len(self.ctrl.tests), 0)
        new_test = TestCaseController(self.ctrl, TestCase(TestCaseFile(), 'New test'))
        self.ctrl.add_test_or_keyword(new_test)
        assert_equals(len(self.ctrl.tests), 1)
        assert_true(self.ctrl.tests[0]._test.parent is self.ctrl.datafile)
        assert_true(self.ctrl.dirty)

    def test_new_test(self):
        test_ctrl = self.ctrl.create_test('Foo')
        assert_equals(test_ctrl.name, 'Foo')

    def test_create_keyword(self):
        kw_ctrl = self.ctrl.create_keyword('An UK')
        assert_equals(kw_ctrl.name, 'An UK')

    def test_create_keyword_with_args(self):
        kw_ctrl = self.ctrl.create_keyword('UK', '${a1} | ${a2}')
        assert_equals(kw_ctrl.name, 'UK')
        assert_equals(kw_ctrl.data.args.value, ['${a1}', '${a2}'])


class TestDataDirectoryControllerTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = TestDataDirectoryController(TestDataDirectory())

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(self.ctrl.settings), 6)

    def test_has_format(self):
        assert_false(self.ctrl.has_format())
        self.ctrl.mark_dirty()
        assert_false(self.ctrl.has_format())
        self.ctrl.data.initfile = '/tmp/__init__.html'
        assert_true(self.ctrl.has_format())

    def test_set_format(self):
        dir = TestDataDirectory()
        dir.source = '/tmp/'
        ctrl = TestDataDirectoryController(dir)
        assert_false(ctrl.has_format())
        ctrl.set_format('txt')
        assert_true(ctrl.has_format())
        assert_equals(ctrl.source, '/tmp/__init__.txt')

    def test_adding_new_child(self):
        assert_true(self.ctrl.new_datafile(NewDatafile('path/to/data.txt',
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
