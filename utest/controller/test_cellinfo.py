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

    def test_optional_has_no_error(self):
        assert_false(CellInfo(ContentType.EMPTY, CellType.OPTIONAL).has_error())
        assert_false(CellInfo(ContentType.STRING, CellType.OPTIONAL).has_error())


class TestCellInfo(unittest.TestCase):

    def setUp(self):
        ctrl = datafilereader.construct_chief_controller(datafilereader.ARGUMENTS_PATH)
        self.testsuite = datafilereader.get_ctrl_by_name('Suite', ctrl.datafiles)
        self.test = self.testsuite.tests[0]
        self.keyword1 = [kw for kw in self.testsuite.keywords if kw.name == 'KW1'][0]
        self.keyword2 = [kw for kw in self.testsuite.keywords if kw.name == 'KW2'][0]

    def test_no_cell_info_if_no_data(self):
        assert_none(self.test.get_cell_info(0, 0))
        assert_none(self.test.get_cell_info(0, 1))
        assert_none(self.test.get_cell_info(0, 2))
        assert_none(self.test.get_cell_info(0, 3))

    def test_keyword_with_mandatory_and_optional_arguments(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.MANDATORY)
        self._verify_string_change(0, 1, CellType.MANDATORY)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.MANDATORY_EMPTY)

    def test_celltype_is_unknown_if_list_var_given(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '@{vars}'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.MANDATORY)
        self._verify_cell_info(0, 1, ContentType.VARIABLE, CellType.UNKNOWN)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.UNKNOWN)
        self._verify_cell_info(0, 3, ContentType.EMPTY, CellType.UNKNOWN)

    def test_keyword_with_varargs(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword2.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.MANDATORY)
        self._verify_string_change(0, 1, CellType.OPTIONAL)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.OPTIONAL)

    def _verify_string_change(self, row, col, celltype):
        self._verify_cell_info(row, col, ContentType.EMPTY, celltype)
        self.test.execute(ChangeCellValue(row, col, 'diipadaapa'))
        self._verify_cell_info(row, col, ContentType.STRING, celltype)

    def _verify_cell_info(self, row, col, contenttype, celltype):
        cell_info = self.test.get_cell_info(row, col)
        assert_equals(cell_info.cell_type, celltype)
        assert_equals(cell_info.content_type, contenttype)