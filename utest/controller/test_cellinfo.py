import unittest
import datafilereader
from robotide.controller.commands import ChangeCellValue
from robot.utils.asserts import assert_equals, assert_true, assert_false,\
    assert_none
from robotide.controller.cellinfo import CellType, ContentType, CellInfo

class TestCellInfoErrors(unittest.TestCase):

    def test_empty_mandatory_is_error(self):
        assert_true(CellInfo(ContentType.EMPTY, CellType.MANDATORY).has_error())

    def test_none_empty_mandatory_is_not_error(self):
        assert_false(CellInfo(ContentType.LIBRARY_KEYWORD, CellType.MANDATORY).has_error())

    def test_commented_mandatory_is_error(self):
        assert_true(CellInfo(ContentType.COMMENTED, CellType.MANDATORY).has_error())

    def test_none_empty_mandatory_empty_is_error(self):
        assert_true(CellInfo(ContentType.STRING, CellType.MANDATORY_EMPTY).has_error())

    def test_empty_mandatory_empty_is_not_error(self):
        assert_false(CellInfo(ContentType.EMPTY, CellType.MANDATORY_EMPTY).has_error())


class TestCellInfo(unittest.TestCase):

    def setUp(self):
        ctrl = datafilereader.construct_chief_controller(datafilereader.ARGUMENTS_PATH)
        self.testsuite = datafilereader.get_ctrl_by_name('Suite', ctrl.datafiles)
        self.test = self.testsuite.tests[0]
        self.keyword = self.testsuite.keywords[0]

    def test_writing_row(self):
        assert_none(self.test.get_cell_info(0, 0))
        assert_none(self.test.get_cell_info(0, 1))
        assert_none(self.test.get_cell_info(0, 2))
        assert_none(self.test.get_cell_info(0, 3))
        self.test.execute(ChangeCellValue(0, 0, self.keyword.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.MANDATORY)
        self._verify_string_change(0, 1, CellType.MANDATORY)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.MANDATORY_EMPTY)

    def _verify_string_change(self, row, col, celltype):
        self._verify_cell_info(row, col, ContentType.EMPTY, celltype)
        self.test.execute(ChangeCellValue(row, col, 'diipadaapa'))
        self._verify_cell_info(row, col, ContentType.STRING, celltype)

    def _verify_cell_info(self, row, col, contenttype, celltype):
        cell_info = self.test.get_cell_info(row, col)
        assert_equals(cell_info.cell_type, celltype)
        assert_equals(cell_info.content_type, contenttype)