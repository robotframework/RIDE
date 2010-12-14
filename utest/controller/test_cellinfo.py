import unittest
import datafilereader
from robotide.controller.commands import ChangeCellValue
from robot.utils.asserts import assert_equals, assert_true, assert_false,\
    assert_none
from robotide.controller.cellinfo import CellType, ContentType, CellInfo

class TestCellInfoErrors(unittest.TestCase):

    def test_empty_mandatory_is_error(self):
        assert_true(CellInfo(ContentType.EMPTY, CellType.MANDATORY, '').has_error())

    def test_none_empty_mandatory_is_not_error(self):
        assert_false(CellInfo(ContentType.LIBRARY_KEYWORD, CellType.MANDATORY, '').has_error())

    def test_commented_mandatory_is_error(self):
        assert_true(CellInfo(ContentType.COMMENTED, CellType.MANDATORY, '').has_error())

    def test_none_empty_mandatory_empty_is_error(self):
        assert_true(CellInfo(ContentType.STRING, CellType.MANDATORY_EMPTY, '').has_error())

    def test_empty_mandatory_empty_is_not_error(self):
        assert_false(CellInfo(ContentType.EMPTY, CellType.MANDATORY_EMPTY, '').has_error())

    def test_optional_has_no_error(self):
        assert_false(CellInfo(ContentType.EMPTY, CellType.OPTIONAL, '').has_error())
        assert_false(CellInfo(ContentType.STRING, CellType.OPTIONAL, '').has_error())


class TestCellInfo(unittest.TestCase):

    def setUp(self):
        ctrl = datafilereader.construct_chief_controller(datafilereader.ARGUMENTS_PATH)
        self.testsuite = datafilereader.get_ctrl_by_name('Suite', ctrl.datafiles)
        self.test = self.testsuite.tests[0]
        self.keyword1 = [kw for kw in self.testsuite.keywords if kw.name == 'KW1'][0]
        self.keyword2 = [kw for kw in self.testsuite.keywords if kw.name == 'KW2'][0]
        self.keyword3 = [kw for kw in self.testsuite.keywords if kw.name == 'KW3'][0]

    def test_no_cell_info_if_no_data(self):
        assert_none(self.test.get_cell_info(0, 0))
        assert_none(self.test.get_cell_info(0, 1))
        assert_none(self.test.get_cell_info(0, 2))
        assert_none(self.test.get_cell_info(0, 3))

    def test_keyword_with_mandatory_and_optional_arguments(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 1, CellType.MANDATORY)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.MANDATORY_EMPTY)

    def test_celltype_is_unknown_if_list_var_given(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '@{vars}'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.VARIABLE, CellType.UNKNOWN)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.UNKNOWN)
        self._verify_cell_info(0, 3, ContentType.EMPTY, CellType.UNKNOWN)

    def test_empty_column_before_string_is_string(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 2, 'something'))
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.MANDATORY)

    def test_comment(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '# I have something to say'))
        self.test.execute(ChangeCellValue(0, 2, 'to you my friend'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.COMMENTED, CellType.MANDATORY)
        self._verify_cell_info(0, 2, ContentType.COMMENTED, CellType.OPTIONAL)

    def test_comment_keyword(self):
        self.test.execute(ChangeCellValue(0, 0, 'I have nothing to say'))
        self.test.execute(ChangeCellValue(0, 1, 'to the void of darkness'))
        self.test.step(0).comment()
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 2, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 3, ContentType.COMMENTED, CellType.OPTIONAL)

    def test_keyword_with_varargs(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword2.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 1, CellType.OPTIONAL)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.OPTIONAL)

    def test_variable_setting(self):
        self.test.execute(ChangeCellValue(0, 0, '${my cool var}='))
        self._verify_cell_info(0, 0, ContentType.VARIABLE, CellType.MANDATORY)
        self.test.execute(ChangeCellValue(0, 1, 'Set Variable'))
        self._verify_cell_info(0, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 2, CellType.OPTIONAL)

    def test_keyword_without_args(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword3.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.EMPTY, CellType.MANDATORY_EMPTY)

    def test_for_loop_header(self):
        forlooped_case = self.keyword3
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(0, 1, ContentType.VARIABLE, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(0, 2, ContentType.STRING, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(0, 3, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 4, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 5, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)

    def test_step_in_for_loop(self):
        forlooped_case = self.keyword3
        self._verify_cell_info(1, 0, ContentType.EMPTY, CellType.MANDATORY_EMPTY, forlooped_case)
        self._verify_cell_info(1, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)

    def _verify_string_change(self, row, col, celltype):
        self._verify_cell_info(row, col, ContentType.EMPTY, celltype)
        self.test.execute(ChangeCellValue(row, col, 'diipadaapa'))
        self._verify_cell_info(row, col, ContentType.STRING, celltype)

    def _verify_cell_info(self, row, col, contenttype, celltype, macro=None):
        if macro == None:
            macro = self.test
        cell_info = macro.get_cell_info(row, col)
        assert_equals(cell_info.cell_type, celltype)
        assert_equals(cell_info.content_type, contenttype)


class TestSelectionMatcher(unittest.TestCase):

    def test_empty_cell_should_not_match(self):
        assert_false(self.matcher('', ''))

    def test_exact_match(self):
        assert_true(self.matcher('My Keyword', 'My Keyword'))
        assert_false(self.matcher('My Keyword', 'Keyword'))

    def test_normalized_match(self):
        assert_true(self.matcher('MyKeyword', 'My Keyword'))
        assert_true(self.matcher('mykeyword', 'My Keyword'))
        assert_true(self.matcher('my_key_word', 'My Keyword'))

    def test_variable_with_equals_sign(self):
        assert_true(self.matcher('${foo} =', '${foo}'))
        assert_true(self.matcher('${foo}=', '${foo}'))
        assert_true(self.matcher('${foo}=', '${  F O O }'))
        assert_false(self.matcher('${foo}=', '${foo2}'))

    def test_variable_inside_cell_content(self):
        assert_true(self.matcher('${foo} =', 'some  ${foo} data'))
        assert_false(self.matcher('some  ${foo} data', '${foo} ='))
        assert_false(self.matcher('${foo}=', 'some not matching ${var}'))
        assert_true(self.matcher('${foo} =', 'Jep we have ${var} and ${foo}!'))

    def matcher(self, value, cell):
        info = CellInfo(None, None, cell)
        return info.matches(value)
