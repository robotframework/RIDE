#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import unittest

import pytest

from utest.resources import datafilereader
from robotide.controller.ctrlcommands import ChangeCellValue, delete_rows, AddKeyword, Undo, paste_area
from robotide.controller.cellinfo import CellType, ContentType, CellInfo, CellContent, CellPosition

SET_VARIABLE = 'Set Variable'
LIB_PY = 'libi.py'


class TestCellInfoErrors(unittest.TestCase):

    def test_empty_mandatory_is_error(self):
        cell = CellInfo(CellContent(ContentType.EMPTY, '', ''),
                        CellPosition(CellType.MANDATORY, None))
        assert cell.has_error()
        assert cell.argument_missing()

    def test_none_empty_mandatory_is_not_error(self):
        cell = CellInfo(CellContent(ContentType.LIBRARY_KEYWORD, '', ''),
                        CellPosition(CellType.MANDATORY, None))
        assert not cell.has_error()
        assert not cell.argument_missing()

    def test_commented_mandatory_is_error(self):
        cell = CellInfo(CellContent(ContentType.COMMENTED, '', ''),
                        CellPosition(CellType.MANDATORY, None))
        assert cell.has_error()
        assert cell.argument_missing()

    def test_none_empty_mandatory_empty_is_error(self):
        cell = CellInfo(CellContent(ContentType.STRING, '', ''),
                        CellPosition(CellType.MUST_BE_EMPTY, None))
        assert cell.has_error()
        assert cell.too_many_arguments()

    def test_empty_mandatory_empty_is_not_error(self):
        cell = CellInfo(CellContent(ContentType.EMPTY, '', ''),
                        CellPosition(CellType.MUST_BE_EMPTY, None))
        assert not cell.has_error()
        assert not cell.too_many_arguments()

    def test_optional_has_no_error(self):
        assert not CellInfo(CellContent(ContentType.EMPTY, '', ''),
                            CellPosition(CellType.OPTIONAL, None)).has_error()
        assert not CellInfo(CellContent(ContentType.STRING, '', ''),
                            CellPosition(CellType.OPTIONAL, None)).has_error()


class TestCellInfo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project_ctrl = datafilereader.construct_project(datafilereader.ARGUMENTS_PATH)
        cls.testsuite = datafilereader.get_ctrl_by_name('Suite', cls.project_ctrl.datafiles)
        cls.test = cls.testsuite.tests[0]

        def keyword(name):
            return [kw for kw in cls.testsuite.keywords if kw.name == name][0]

        cls.keyword1 = keyword('KW1')
        cls.keyword2 = keyword('KW2')
        cls.keyword3 = keyword('KW3')
        cls.keyword4 = keyword('KW4')
        cls.keyword5 = keyword('KW5')

    @classmethod
    def tearDownClass(cls):
        cls.project_ctrl.close()

    def tearDown(self):
        self.test.execute(delete_rows([i for i in range(len(self.test.steps))]))

    def test_no_cell_info_if_no_data(self):
        print("DEBUG: test_no_cell_info_if_no_data:")
        for s in self.test.steps:
            print(f"{s.as_list()}")
        assert self.test.get_cell_info(1, 0) is None
        assert self.test.get_cell_info(1, 1) is None
        assert self.test.get_cell_info(1, 2) is None
        assert self.test.get_cell_info(1, 3) is None

    def test_keyword_with_mandatory_and_optional_arguments(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 1, CellType.MANDATORY)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.MUST_BE_EMPTY)

    def test_keyword_with_optional_and_list_arguments(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword4.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 1, CellType.OPTIONAL)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.OPTIONAL)
        self._verify_string_change(0, 4, CellType.OPTIONAL)

    def test_celltype_is_not_unknown_if_list_var_given(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '@{vars}'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.OPTIONAL)
        self._verify_cell_info(0, 3, ContentType.EMPTY, CellType.MUST_BE_EMPTY)

    def test_celltype_is_not_unknown_if_dict_var_given(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '&{vars}'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.OPTIONAL)
        self._verify_cell_info(0, 3, ContentType.EMPTY, CellType.MUST_BE_EMPTY)

    def test_list_variables_item_in_keyword_args(self):
        self.test.execute(paste_area((0, 0), [[self.keyword5.name, '@{LIST_VARIABLE}[0]']]))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.VARIABLE, CellType.MANDATORY)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.MANDATORY)

    def test_dict_variables_item_in_keyword_args(self):
        self.test.execute(paste_area((0, 0), [[self.keyword5.name, '&{DICT_VARIABLE}[foo]']]))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.VARIABLE, CellType.MANDATORY)
        self._verify_cell_info(0, 2, ContentType.EMPTY, CellType.MANDATORY)

    def test_variable_is_known_when_defining_it(self):
        self.test.execute(ChangeCellValue(0, 0, '${var}='))
        self.test.execute(ChangeCellValue(0, 1, SET_VARIABLE))
        self.test.execute(ChangeCellValue(0, 2, '${var1}'))
        self._verify_cell_info(0, 0, ContentType.VARIABLE, CellType.ASSIGN)
        self._verify_cell_info(0, 2, ContentType.UNKNOWN_VARIABLE, CellType.OPTIONAL)

    def test_known_extended_variable_syntax(self):
        self.test.execute(ChangeCellValue(0, 0, '${var}='))
        self.test.execute(ChangeCellValue(0, 1, SET_VARIABLE))
        self.test.execute(ChangeCellValue(0, 2, 'something'))
        self.test.execute(ChangeCellValue(1, 0, 'log'))
        self.test.execute(ChangeCellValue(1, 2, '${var.lower()}'))
        self.test.execute(ChangeCellValue(2, 0, 'log'))
        self.test.execute(ChangeCellValue(2, 2, '${var+"moi"}'))
        self.test.execute(ChangeCellValue(3, 0, 'log'))
        self.test.execute(ChangeCellValue(3, 2, '${var[1:]}'))
        self._verify_cell_info(1, 2, ContentType.VARIABLE, CellType.OPTIONAL)
        self._verify_cell_info(2, 2, ContentType.VARIABLE, CellType.OPTIONAL)
        self._verify_cell_info(3, 2, ContentType.VARIABLE, CellType.OPTIONAL)

    def test_empty_column_before_string_is_string(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 2, 'something'))
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.MANDATORY)

    def test_comment(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword1.name))
        self.test.execute(ChangeCellValue(0, 1, '# I have something to say'))
        self.test.execute(ChangeCellValue(0, 2, 'to you my friend'))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 2, ContentType.COMMENTED, CellType.OPTIONAL)

    def test_comment_keyword(self):
        self.test.execute(ChangeCellValue(0, 0, 'I have nothing to say'))
        self.test.execute(ChangeCellValue(0, 1, 'to the void of darkness'))
        self.test.step(0).comment()
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 2, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 3, ContentType.COMMENTED, CellType.OPTIONAL)
        """
        print(f"DEBUG: Test AFTER test_comment_keyword")
        for k in self.test.steps:
            print(f"value: {k.as_list()}")
        """

    def test_keyword_with_varargs(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword2.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 1, CellType.OPTIONAL)
        self._verify_string_change(0, 2, CellType.OPTIONAL)
        self._verify_string_change(0, 3, CellType.OPTIONAL)

    def test_comment_keyword_with_varargs(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword2.name))
        """
        print(f"DEBUG: Test BEFORE test_comment_keyword_with_varargs")
        for k in self.test.steps:
            print(f"value: {k.as_list()}")
        """
        self.test.step(0).comment()
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 2, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 3, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 4, ContentType.COMMENTED, CellType.OPTIONAL)
        self._verify_cell_info(0, 5, ContentType.COMMENTED, CellType.OPTIONAL)
        """
        print(f"DEBUG: Test AFTER test_comment_keyword")
        for k in self.test.steps:
            print(f"value: {k.as_list()}")
        """

    def test_variable_setting(self):
        self.test.execute(ChangeCellValue(0, 0, '${my cool var}='))
        self._verify_cell_info(0, 0, ContentType.VARIABLE, CellType.ASSIGN)
        self.test.execute(ChangeCellValue(0, 1, SET_VARIABLE))
        self._verify_cell_info(0, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_string_change(0, 2, CellType.OPTIONAL)

    def test_variable_defined_by_var(self):
        self.test.execute(ChangeCellValue(0, 0, 'VAR'))
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self.test.execute(ChangeCellValue(0, 1, '${my cool var}'))
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.OPTIONAL)
        self.test.execute(ChangeCellValue(0, 2, 'my cool var value'))
        self._verify_cell_info(0, 2, ContentType.STRING, CellType.OPTIONAL)

    def test_keyword_without_args(self):
        self.test.execute(ChangeCellValue(0, 0, self.keyword3.name))
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.EMPTY, CellType.MUST_BE_EMPTY)

    @pytest.mark.order(1)
    def test_lower_case_for_is_not_keyword(self):
        forlooped_case = self.keyword3
        forlooped_case.execute(ChangeCellValue(0, 0, 'for'))
        # DEBUG changed FOR to BlockKeywordLibrary
        # for st in range(0, 6):
        #     print(f"\n{forlooped_case.get_cell_info(0, st).cell_type} content: "
        #           f"{forlooped_case.get_cell_info(0, st).content_type} ")
        # print(f"kw_name:{forlooped_case.name}")
        # for k in forlooped_case.steps:
        #     print(f"value: {k.as_list()}")
        # print(f"\nDEBUG: cellinfo test_for_loop_in_header: {forlooped_case.get_cell_info(0, 0).cell_type}")
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN, forlooped_case)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.UNKNOWN, forlooped_case)
        self._verify_cell_info(0, 2, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)  # IN is like kw
        self._verify_cell_info(0, 3, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 4, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 5, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)

    def test_lower_case_log_is_keyword(self):
        log_case = self.keyword3
        log_case.execute(ChangeCellValue(0, 0, 'log'))
        # DEBUG changed FOR to BlockKeywordLibrary
        # for st in range(0, 6):
        #     print(f"\n{log_case.get_cell_info(0, st).cell_type} content: "
        #           f"{log_case.get_cell_info(0, st).content_type} ")
        # print(f"kw_name:{log_case.name}")
        # for k in log_case.steps:
        #     print(f"value: {k.as_list()}")
        # print(f"\nDEBUG: cellinfo test_for_loop_in_header: {log_case.get_cell_info(0, 0).cell_type}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, log_case)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, log_case)

    def test_title_case_log_is_keyword(self):
        log_case = self.keyword3
        log_case.execute(ChangeCellValue(0, 0, 'Log'))
        # DEBUG changed FOR to BlockKeywordLibrary
        # for st in range(0, 6):
        #     print(f"\n{log_case.get_cell_info(0, st).cell_type} content: "
        #           f"{log_case.get_cell_info(0, st).content_type} ")
        # print(f"kw_name:{log_case.name}")
        # for k in log_case.steps:
        #    print(f"value: {k.as_list()}")
        # print(f"\nDEBUG: cellinfo test_for_loop_in_header: {log_case.get_cell_info(0, 0).cell_type}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, log_case)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, log_case)

    def test_upper_case_log_is_keyword(self):
        log_case = self.keyword3
        log_case.execute(ChangeCellValue(0, 0, 'LOG'))
        # DEBUG changed FOR to BlockKeywordLibrary
        # for st in range(0, 6):
        #     print(f"\n{log_case.get_cell_info(0, st).cell_type} content: "
        #           f"{log_case.get_cell_info(0, st).content_type} ")
        # print(f"kw_name:{log_case.name}")
        # for k in log_case.steps:
        #     print(f"value: {k.as_list()}")
        # print(f"\nDEBUG: cellinfo test_for_loop_in_header: {log_case.get_cell_info(0, 0).cell_type}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, log_case)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, log_case)

    def test_for_loop_in_header(self):
        forlooped_case = self.keyword3
        # DEBUG changed FOR to BlockKeywordLibrary
        # for st in range(0, 6):
        #    print(f"\n{forlooped_case.get_cell_info(0, st).cell_type} content: "
        #          f"{forlooped_case.get_cell_info(0, st).content_type} ")
        # print(f"kw_name:{forlooped_case.name}")
        # for k in forlooped_case.steps:
        #    print(f"value: {k.as_list()}")
        # print(f"\nDEBUG: cellinfo test_for_loop_in_header: {forlooped_case.get_cell_info(0, 0).cell_type}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(0, 2, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)  # IN is like kw
        self._verify_cell_info(0, 3, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 4, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(0, 5, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)

    def test_steps_in_for_loop(self):
        forlooped_case = self.keyword3
        print(f"kw_name:{forlooped_case.name}")
        for k in forlooped_case.steps:
            print(f"value: {k.as_list()}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(1, 0, ContentType.STRING, CellType.UNKNOWN, forlooped_case)
        self._verify_cell_info(1, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(1, 2, ContentType.STRING, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(2, 0, ContentType.STRING, CellType.UNKNOWN, forlooped_case)
        self._verify_cell_info(2, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(3, 0, ContentType.STRING, CellType.UNKNOWN, forlooped_case)
        self._verify_cell_info(3, 1, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(3, 2, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(4, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(4, 1, ContentType.EMPTY, CellType.MUST_BE_EMPTY, forlooped_case)

    def test_for_loop_in_range_header(self):
        forlooped_case = self.keyword3
        in_range_header_index = 5
        # self._verify_cell_info(in_range_header_index, 0, ContentType.STRING, CellType.MANDATORY, forlooped_case)
        # Because FOR and END now have documentation
        self._verify_cell_info(in_range_header_index, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(in_range_header_index, 1, ContentType.UNKNOWN_VARIABLE, CellType.MANDATORY, forlooped_case)
        self._verify_cell_info(in_range_header_index, 2, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, forlooped_case)
        self._verify_cell_info(in_range_header_index, 3, ContentType.STRING, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(in_range_header_index, 4, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(in_range_header_index, 5, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)
        self._verify_cell_info(in_range_header_index, 6, ContentType.EMPTY, CellType.OPTIONAL, forlooped_case)

    def test_library_import_add_and_remove(self):
        self.test.execute(paste_area((0, 0), [['Get File', 'reaktor.robot']]))
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.UNKNOWN)
        self.testsuite.imports.add_library('OperatingSystem', [], '')
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.MANDATORY)
        self.testsuite.imports.delete(-1)
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.UNKNOWN)

    def test_library_import_with_name_and_arguments(self):
        self.test.execute(ChangeCellValue(0, 0, 'alias.Onething'))
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self.testsuite.imports.add_library(LIB_PY, 'a | b', 'alias')
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)

    def test_library_import_with_name_and_one_argument(self):
        self.test.execute(ChangeCellValue(0, 0, 'alias2.Onething'))
        print("DEBUG: test_library_import_with_name_and_one_argument:")
        for s in self.test.steps:
            print(f"{s.as_list()}")
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self.testsuite.imports.add_library(LIB_PY, '1', 'alias2')
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)

    def test_library_import_with_name(self):
        self.test.execute(ChangeCellValue(0, 0, 'alias3.Onething'))
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self.testsuite.imports.add_library(LIB_PY, [], 'alias3')
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)

    def test_library_import_modify(self):
        self.test.execute(paste_area((0, 0), [['Get File', 'reaktor.robot']]))
        lib = self.testsuite.imports.add_library('WrongOperatingSystem', [], '')
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.UNKNOWN)
        lib.set_value('OperatingSystem', [], '')
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.MANDATORY)
        self.testsuite.imports.delete(-1)
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self._verify_cell_info(0, 1, ContentType.STRING, CellType.UNKNOWN)

    def test_create_and_remove_keyword(self):
        kw_name = 'Super Keyword'
        self.test.execute(ChangeCellValue(0, 0, kw_name))
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self.test.execute(AddKeyword(kw_name, '${argh}'))
        print("\nDEBUG: test_variable_setting:")
        for s in self.test.steps:
            print(f"{s.as_list()}\n")
        self._verify_cell_info(0, 0, ContentType.USER_KEYWORD, CellType.KEYWORD)
        self._verify_cell_info(0, 1, ContentType.EMPTY, CellType.MANDATORY)
        self.test.execute(Undo())
        self._verify_cell_info(0, 0, ContentType.STRING, CellType.UNKNOWN)
        self._verify_cell_info(0, 1, ContentType.EMPTY, CellType.UNKNOWN)

    def _verify_string_change(self, row, col, celltype):
        self._verify_cell_info(row, col, ContentType.EMPTY, celltype)
        self.test.execute(ChangeCellValue(row, col, 'diipadaapa'))
        self._verify_cell_info(row, col, ContentType.STRING, celltype)

    def _verify_cell_info(self, row, col, contenttype, celltype, macro=None):
        if macro is None:
            macro = self.test
        cell_info = macro.get_cell_info(row, col)
        print(f"DEBUG:test_cellinfo type cell_type{cell_info.cell_type} content_type{cell_info.content_type}")
        assert cell_info.cell_type == celltype
        assert cell_info.content_type == contenttype



class TestEmbeddedCellInfo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project_ctrl = datafilereader.construct_project(datafilereader.EMBEDDED_PROJECT)
        # print(f"DEBUG: TestEmbeddedCellInfo setUpClass project_ctrl: {cls.project_ctrl.display_name}"
        #       f" {cls.project_ctrl.datafiles}")
        cls.testsuite = cls.project_ctrl.datafiles[0]
        cls.test1 = cls.testsuite.tests[0]
        cls.test2 = cls.testsuite.tests[1]

    @classmethod
    def tearDownClass(cls):
        cls.project_ctrl.close()

    def test_var_and_kw(self):
        # print("DEBUG: test_var_and_kw:")
        # for s in self.test1.steps:
        #     print(f"{s.as_list()}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, self.test1)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.OPTIONAL, self.test1)
        self._verify_cell_info(0, 2, ContentType.STRING, CellType.OPTIONAL, self.test1)
        self._verify_cell_info(1, 0, ContentType.USER_KEYWORD, CellType.KEYWORD, self.test1)
        self._verify_cell_info(2, 0, ContentType.USER_KEYWORD, CellType.KEYWORD, self.test1)
        # This was at TearDown
        self.test1.execute(delete_rows([i for i in range(len(self.test1.steps))]))

    def test_var_and_kw_prefix_resource(self):
        # print("DEBUG: test_var_and_kw:")
        # for s in self.test2.steps:
        #     print(f"{s.as_list()}")
        self._verify_cell_info(0, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, self.test2)
        self._verify_cell_info(0, 1, ContentType.UNKNOWN_VARIABLE, CellType.OPTIONAL, self.test2)
        self._verify_cell_info(0, 2, ContentType.STRING, CellType.OPTIONAL, self.test2)
        self._verify_cell_info(1, 0, ContentType.USER_KEYWORD, CellType.KEYWORD, self.test2)
        self._verify_cell_info(2, 0, ContentType.LIBRARY_KEYWORD, CellType.KEYWORD, self.test2)
        self._verify_cell_info(2, 1, ContentType.UNKNOWN_VARIABLE, CellType.OPTIONAL, self.test2)
        self._verify_cell_info(2, 2, ContentType.STRING, CellType.OPTIONAL, self.test2)
        self._verify_cell_info(3, 0, ContentType.USER_KEYWORD, CellType.KEYWORD, self.test2)
        self._verify_cell_info(3, 1, ContentType.VARIABLE, CellType.MANDATORY, self.test2)
        # This was at TearDown
        self.test2.execute(delete_rows([i for i in range(len(self.test2.steps))]))

    @staticmethod
    def _verify_cell_info(row, col, contenttype, celltype, macro=None):
        cell_info = macro.get_cell_info(row, col)
        # print(f"DEBUG:test_cellinfo type cell_type{cell_info.cell_type} content_type{cell_info.content_type}")
        assert cell_info.cell_type == celltype
        assert cell_info.content_type == contenttype


if __name__ == "__main__":
    unittest.main()
