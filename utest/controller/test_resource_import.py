import os
import unittest
import datafilereader

from robotide.controller.commands import AddKeyword, ChangeCellValue,\
    CreateNewResource, SaveFile
from nose.tools import assert_equals
from robotide.controller.cellinfo import ContentType, CellType


class TestResourceImport(unittest.TestCase):

    def setUp(self):
        self.res_path = datafilereader.SIMPLE_TEST_SUITE_PATH
        self.res_name = 'new_resource_for_test_creating_and_importing_resource.txt'
        self.res_full_name = os.path.join(self.res_path, self.res_name)
        self.new_keyword_name = 'My Keywordian'
        self.ctrl = datafilereader.construct_project(datafilereader.SIMPLE_TEST_SUITE_PATH)
        self.suite = datafilereader.get_ctrl_by_name('TestSuite1', self.ctrl.datafiles)
        self.test = self.suite.tests[0]
        self.test.execute(ChangeCellValue(0,0,self.new_keyword_name))
        self.test.execute(ChangeCellValue(0,1,'value'))

    def tearDown(self):
        os.remove(self.res_full_name)
        self.ctrl.close()

    def _create_resource(self):
        self.new_resource = self.ctrl.execute(CreateNewResource(self.res_full_name))
        self.new_resource.execute(AddKeyword(self.new_keyword_name, '${moi}'))
        self.new_resource.execute(SaveFile())

    def test_number_of_resources_is_correct(self):
        original_number_of_resources = len(self.ctrl.resources)
        self._create_resource()
        assert_equals(original_number_of_resources+1, len(self.ctrl.resources))
        self._add_resource_import_to_suite()
        assert_equals(original_number_of_resources+1, len(self.ctrl.resources))

    def test_creating_and_importing_resource_file(self):
        self._create_resource()
        self._verify_unidentified_keyword()
        self.assertFalse(self.new_resource.is_used())
        import_ = self._add_resource_import_to_suite()
        self._verify_identified_keyword()
        self.assertTrue(self.new_resource.is_used())
        self._remove_resource_import_from_suite(import_)
        self._verify_unidentified_keyword()
        self.assertFalse(self.new_resource.is_used())

    def test_importing_and_creating_resource_file(self):
        self._add_resource_import_to_suite()
        self._verify_unidentified_keyword()
        self._create_resource()
        self._verify_identified_keyword()

    def test_changes_in_resource_file(self):
        self._create_resource()
        self._add_resource_import_to_suite()
        self._keyword_controller.arguments.set_value('')
        self._check_cells(ContentType.USER_KEYWORD, CellType.MUST_BE_EMPTY)

    def test_resource_import_knows_resource_after_import_has_been_removed(self):
        item_without_settings = datafilereader.get_ctrl_by_name('Inner Resource', self.ctrl.datafiles)
        self.assertEqual(list(item_without_settings.imports), [])
        self._create_resource()
        import_ = item_without_settings.imports.add_resource('/'.join(['..', self.res_name]))
        self.assertTrue(import_ is not None)
        item_without_settings.imports.delete(0)
        self.assertEqual(self.new_resource, import_.get_previous_imported_controller())

    def test_previously_imported_resource_controller_is_none_by_default(self):
        self._create_resource()
        import_controller = self._add_resource_import_to_suite()
        self.assertEqual(import_controller.get_previous_imported_controller(), None)

    @property
    def _keyword_controller(self):
        return self.ctrl.resources[-1].keywords[-1]

    def _add_resource_import_to_suite(self):
        return self.suite.imports.add_resource(self.res_name)

    def _remove_resource_import_from_suite(self, import_):
        import_.remove()

    def _verify_unidentified_keyword(self):
        self._check_cells(ContentType.STRING, CellType.UNKNOWN)

    def _verify_identified_keyword(self):
        self._check_cells(ContentType.USER_KEYWORD, CellType.MANDATORY)

    def _check_cells(self, keyword_content_type, value_cell_type):
        assert_equals(self.test.get_cell_info(0,0).content_type, keyword_content_type)
        assert_equals(self.test.get_cell_info(0,1).cell_type, value_cell_type)
