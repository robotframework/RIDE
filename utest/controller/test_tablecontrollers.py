import unittest
from nose.tools import assert_equals

from robotide.robotapi import TestCaseFile, TestCaseFileSettingTable
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.tablecontrollers import ImportSettingsController


VALID_NAME = 'Valid name'


class TestCaseNameValidationTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile()).tests

    def test_valid_name(self):
        self._validate_name(VALID_NAME, True)

    def test_empty_name(self):
        self._validate_name('', False)

    def test_name_with_only_whitespace(self):
        self._validate_name('      ', False)

    def test_duplicate_name(self):
        self.ctrl.new(VALID_NAME)
        self._validate_name(VALID_NAME, False)
        self._validate_name(VALID_NAME.upper(), False)
        self._validate_name(VALID_NAME.replace(' ', '_'), False)

    def test_duplicate_name_when_previous_name_known(self):
        ctrl = self.ctrl.new(VALID_NAME)
        self._validate_name(VALID_NAME, True, ctrl)
        self._validate_name(VALID_NAME.upper(), True, ctrl)
        self._validate_name(VALID_NAME.replace(' ', '_'), True, ctrl)

    def _validate_name(self, name, expected_valid, named_ctrl=None):
        valid = not bool(self.ctrl.validate_name(name, named_ctrl).error_message)
        assert_equals(valid, expected_valid)


class TestCaseCreationTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile()).tests

    def test_whitespace_is_stripped(self):
        test = self.ctrl.new('   ' + VALID_NAME + '\t   \n')
        assert_equals(test.name, VALID_NAME)


class LibraryImportListOperationsTest(unittest.TestCase):

    def setUp(self):
        self._parent = lambda:0
        self._parent.mark_dirty = lambda:0
        self._parent.datafile_controller = self._parent
        self._parent.update_namespace = lambda:0
        self._table = TestCaseFileSettingTable(lambda:0)
        self.ctrl = ImportSettingsController(self._parent, self._table)
        self._lib1 = self.ctrl.add_library('libbi1', '', '')
        self._lib2 = self.ctrl.add_library('libbi2', '', '')
        self.assertEqual([self._lib1.name, self._lib2.name], [l.name for l in self.ctrl])

    def test_move_up(self):
        self.ctrl.move_up(1)
        self.assertEqual([self._lib2.name, self._lib1.name], [l.name for l in self.ctrl])

    def test_move_down(self):
        self.ctrl.move_down(0)
        self.assertEqual([self._lib2.name, self._lib1.name], [l.name for l in self.ctrl])
