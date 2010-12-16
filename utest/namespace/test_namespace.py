import sys
import unittest

from robot.parsing.settings import Resource
from robot.parsing.model import VariableTable, TestDataDirectory
from robot.utils import normalizing
from robot.utils.asserts import assert_true, assert_false, assert_not_none, \
    assert_equals, fail, assert_none
from robotide.namespace.namespace import _VariableStash
from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import DataController
from datafilereader import *
from robotide.spec.iteminfo import ArgumentInfo

RESOURCES_DIR = 'resources'

sys.path.append(os.path.join(os.path.dirname(__file__), '..', RESOURCES_DIR,
                             'robotdata', 'libs'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', RESOURCES_DIR,
                             'robotdata', 'put_into_python_path'))

OS_LIB = 'OperatingSystem'
COLLECTIONS_LIB = 'Collections'
STRING_LIB = 'String'
RES_NAME_VARIABLE = '${resname}'
LIB_NAME_VARIABLE = '${libname}'
UNRESOLVABLE_VARIABLE = '${unresolvable}'
UNKNOWN_VARIABLE = '${this var does not exist}'
EXTENSION_VAR = '${extension}'
EXTENSION = 'txt'
INVALID_FILE_PATH = '/this/is/invalid.py'
EXISTING_USER_KEYWORD = 'Should be in keywords Uk'

def _build_test_case_file():
    tcf = TestCaseFile()
    tcf.directory = '/tmp/'
    _add_settings_table(tcf)
    _add_variable_table(tcf)
    _add_keyword_table(tcf)
    return tcf

def _add_settings_table(tcf):
    tcf.setting_table.add_library(OS_LIB)
    tcf.setting_table.add_resource(RESOURCE_PATH)
    tcf.setting_table.add_resource(RESOURCE_LIB_PATH)
    tcf.setting_table.add_resource(RES_NAME_VARIABLE)
    tcf.setting_table.add_library(LIB_NAME_VARIABLE)
    tcf.setting_table.add_library(LIB_NAME_VARIABLE)
    tcf.setting_table.add_library(UNRESOLVABLE_VARIABLE)
    tcf.setting_table.add_library(LIBRARY_WITH_SPACES_IN_PATH)
    tcf.setting_table.add_resource(RESOURCE_WITH_VARIABLE_IN_PATH)
    tcf.setting_table.add_variables(INVALID_FILE_PATH)

def _add_variable_table(tcf):
    tcf.variable_table.add(LIB_NAME_VARIABLE, COLLECTIONS_LIB)
    tcf.variable_table.add(RES_NAME_VARIABLE, RESOURCE_WITH_VARS)
    tcf.variable_table.add(EXTENSION_VAR, EXTENSION)
    tcf.variable_table.add(UNRESOLVABLE_VARIABLE, UNKNOWN_VARIABLE)

def _add_keyword_table(tcf):
    uk_table = tcf.keyword_table
    uk_table.add(EXISTING_USER_KEYWORD)
    uk_table.keywords[0].args.value = ['${keyword argument}', '${keyword argument with default} = default']


class ParentMock(object):
    source = '/tmp/example/parentmock'
    directory = '/tmp/exmaple'


class _DataFileTest(unittest.TestCase):
    tcf = _build_test_case_file()
    tcf_ctrl = DataController(tcf, None)
    kw = tcf_ctrl.keywords[0]
    ns = Namespace()


class TestKeywordSuggestions(_DataFileTest):

    def test_getting_suggestions_for_empty_datafile(self):
        start = 'shOulD'
        sugs = self.ns.get_suggestions_for(self.kw, start)
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.name.lower().startswith(start.lower()))

    def test_getting_suggestions_in_order(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'sHoUlD')
        assert_true(len(sugs) > 2)
        assert_equals(sugs, sorted(sugs))

    def test_user_keywords(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'sHoUlD')
        assert_true(EXISTING_USER_KEYWORD in [s.name for s in sugs])

    def test_imported_lib_keywords(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'create file')
        self._assert_import_kws(sugs, OS_LIB)

    def test_lib_from_resource_file(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'generate random')
        self._assert_import_kws(sugs, STRING_LIB)

    def test_lib_import_from_var(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Copy List')
        self._assert_import_kws(sugs, COLLECTIONS_LIB)

    def test_lib_import_with_spaces(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'space')
        self._assert_import_kws(sugs, 'spacelib')

    def test_resource_file_keywords(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Resource Uk')
        self._assert_import_kws(sugs, RESOURCES_HTML)

    def test_keywords_normalization(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Reso   Urceuk')
        self._assert_import_kws(sugs, RESOURCES_HTML)

    def test_uk_from_resource_files_resource_file(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'UK From Text Resource')
        self._assert_import_kws(sugs, 'resource.txt')

    def test_resource_file_from_variable(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'UK From Variable Resource')
        self._assert_import_kws(sugs, 'resource_with_variables.txt')

    def test_resource_file_from_resource_file_with_variable(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'UK From Resource from Resource with Variable')
        self._assert_import_kws(sugs, 'resource_from_resource_with_variable.txt')

    def test_library_from_resourcefile_variable(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Execute Manual')
        self._assert_import_kws(sugs, 'Dialogs')

    def test_xml_library(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0], 'Attributeless Keyword')
        self._assert_import_kws(sugs, 'LibSpecLibrary')

    def test_xml_library_is_library_keyword(self):
        everything_tcf = TestCaseFile(source=TESTCASEFILE_WITH_EVERYTHING)
        assert_true(self.ns.is_library_keyword(everything_tcf, 'Attributeless Keyword'))

    def test_variable_path_separator(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0], 'foo')
        self._assert_import_kws(sugs, 'even_more_resources.txt')

    def test_keywords_only_once_per_source(self):
        sugs = self.ns.get_suggestions_for(self.kw, '')
        kw_set = []
        for kw in sugs:
            if self._not_variable(kw):
                key = 'kw: %s %s' % (kw.name, kw.source)
                assert_false(key in kw_set, key)
                kw_set.append(key)

    def _not_variable(self, item):
        return not (item.name.startswith('$') or item.name.startswith('@'))

    def test_global_variable_list_suggestions(self):
        global_var_names = [name for name in _VariableStash.global_variables]
        for name in global_var_names:
            assert_true(name in [sug.name for sug in self.ns.get_suggestions_for(self.kw, name)])

    def test_resource_with_variable_in_path(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Resu UK')
        self._assert_import_kws(sugs, 'resu.txt')

    def test_variable_suggestion(self):
        scalar_vars = self.ns.get_suggestions_for(self.kw, '$')
        assert_true(len(scalar_vars) > 0)
        assert_true(len(self.ns.get_suggestions_for(self.kw, '${')) == len(scalar_vars))
        list_vars = self.ns.get_suggestions_for(self.kw, '@')
        assert_true(len(list_vars) > 0)
        assert_true(len(self.ns.get_suggestions_for(self.kw, '@{')) == len(list_vars))
        sug = self.ns.get_suggestions_for(self.kw, '${lib')
        assert_true(sug[0].name == LIB_NAME_VARIABLE)

    def test_vars_from_file(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
                                           '${var_from_file')
        assert_true(len(sugs) > 0)

    def _get_controller(self, source):
        return DataController(TestCaseFile(source=source), None)

    def test_library_arguments_are_resolved(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
                                           'Get ')
        assert_true(len(sugs) > 0)
        for item in sugs:
            if item.name == 'Get Mandatory':
                return
        fail('Get mandatory not found')

    def test_vars_from_path_resource_file(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
                                           '${Path RESOURCE var')
        assert_true(len(sugs) > 0)

    def test_variable_file_arguments_are_resolved(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
                                           '${dyn ')
        assert_true(len(sugs) > 0)

    def test_variable_file_variables_are_available_in_resource_imports(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(TESTCASEFILE_WITH_RESOURCES_WITH_VARIABLES_FROM_VARIABLE_FILE).tests[0],
                                           'from resource with variable in pa')
        self._assert_import_kws(sugs, 'res.txt')

    def test_vars_from_keyword_arguments(self):
        sugs = self.ns.get_suggestions_for(self.kw, '${keyword argu')
        assert_equals(len(sugs), 2)
        sugs = self.ns.get_suggestions_for(self.kw, '${keyword argument with defau')
        assert_equals(len(sugs), 1)
        self._check_source(self.kw, '${keyword argument with defau', ArgumentInfo.SOURCE)

    def test_keyword_arguments_are_suggested_first(self):
        sugs = self.ns.get_suggestions_for(self.kw, '')
        self._assert_import_kws(sugs[:2], ArgumentInfo.SOURCE)

    def test_suggestions_for_datafile(self):
        sugs = self.ns.get_suggestions_for(self.tcf_ctrl, 'Execute Manual')
        self._assert_import_kws(sugs, 'Dialogs')
        sugs = self.ns.get_suggestions_for(self.tcf_ctrl, '${libna')
        assert_true(len(sugs) == 1)

    def test_variable_sources(self):
        everything_tcf = self._get_controller(TESTCASEFILE_WITH_EVERYTHING)
        self._check_source(everything_tcf, '${arg}', 'everything.html')
        self._check_source(everything_tcf, '@{list}', 'everything.html')
        self._check_source(everything_tcf, '${dynamic var}', 'dynamic_varz.py')
        self._check_source(everything_tcf, '${OPERATING SYSTEM}', 'another_resource.html')

    def _check_source(self, controller, name, source):
        sugs = self.ns.get_suggestions_for(controller, name)
        assert_equals(len(sugs), 1)
        assert_equals(sugs[0].source, source)

    def _assert_import_kws(self, sugs, source):
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.source.endswith(source),
                        '%s does not end with %s' % (s.source, source))


class TestKeywordSearch(_DataFileTest):

    def test_is_library_keyword(self):
        assert_true(self.ns.is_library_keyword(self.tcf, 'Should Be Equal'))
        assert_false(self.ns.is_library_keyword(self.tcf, 'kameli'))
        assert_false(self.ns.is_library_keyword(self.tcf, 'UK From Resource from Resource with Variable'))
        assert_true(self.ns.is_library_keyword(self.tcf, 'Builtin.Should Be Equal'))

    def test_find_default_keywords(self):
        all_kws = self.ns.get_all_keywords([])
        assert_not_none(all_kws)
        self.assert_in_keywords(all_kws, 'Should Be Equal')

    def test_find_suite_keywords(self):
        everything_tcf = TestCaseFile(source=TESTCASEFILE_WITH_EVERYTHING)
        all_kws = self.ns.get_all_keywords([self.tcf, everything_tcf])
        self.assert_in_keywords(all_kws, 'Should be in keywords Uk',
                                         'Copy List',
                                         'Uk From Variable Resource')
        self.assert_in_keywords(all_kws, 'My Test Setup',
                                         'My Suite Teardown')

    def test_resource_kws_only_once(self):
        directory = TestDataDirectory(source=OCCURRENCES_PATH)
        all_kws = self.ns.get_all_keywords(directory.children)
        self._check_resource_keyword_only_once(all_kws)

    def test_resource_kws_only_once_through_chief_controller(self):
        chief = construct_chief_controller(OCCURRENCES_PATH)
        all_kws = chief.get_all_keywords()
        self._check_resource_keyword_only_once(all_kws)

    def _check_resource_keyword_only_once(self, all_kws):
        results = [(kw.name, kw.source) for kw in all_kws if kw.name == "Only From Resource"]
        assert_equals(len(results), 1)
        assert_equals(results[0], (u'Only From Resource', u'testdata_resource.txt'))

    def test_find_user_keyword_name_normalized(self):
        assert_not_none(self.ns.find_user_keyword(self.tcf, 'UK Fromresource from rESOURCE with variaBLE'))
        assert_none(self.ns.find_user_keyword(self.tcf, 'Copy List'))

    def test_is_user_keyword(self):
        assert_true(self.ns.is_user_keyword(self.tcf, 'UKFromResource from ResourcewithVariable'))
        assert_false(self.ns.is_user_keyword(self.tcf, 'hevoinen'))
        assert_false(self.ns.is_user_keyword(self.tcf, 'Should Be Equal'))

    def test_is_user_keyword_in_resource_file(self):
        everything_tcf = TestCaseFile(source=TESTCASEFILE_WITH_EVERYTHING)
        assert_not_none(self.ns.find_user_keyword(everything_tcf, 'Duplicate UK'))
        assert_true(self.ns.is_user_keyword(everything_tcf, 'Duplicate UK'))
        assert_not_none(self.ns.find_user_keyword(everything_tcf, 'Another Resource UK'))
        assert_true(self.ns.is_user_keyword(everything_tcf, 'Another Resource UK'))

    def test_given_when_then_and_aliases(self):
        assert_not_none(self.ns.find_user_keyword(self.tcf, '  Given   UK Fromresource from rESOURCE with variaBLE'))
        assert_not_none(self.ns.find_user_keyword(self.tcf, 'when  UK Fromresource from rESOURCE with variaBLE'))
        assert_not_none(self.ns.find_user_keyword(self.tcf, '  then UK Fromresource from rESOURCE with variaBLE'))
        assert_not_none(self.ns.find_user_keyword(self.tcf, 'AND UK Fromresource from rESOURCE with variaBLE'))
        assert_none(self.ns.find_user_keyword(self.tcf, 'given and UK Fromresource from rESOURCE with variaBLE'))

    def assert_in_keywords(self, keywords, *kw_names):
        for kw_name in kw_names:
            if not self._in_keywords(keywords, kw_name):
                fail(kw_name)

    def _in_keywords(self, keywords, kw_name):
        return any([kw_name.lower() == kw.name.lower() for kw in keywords])


class TestVariableStash(unittest.TestCase):

    def test_variable_resolving(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock())
        var_table.add('${var1}', 'foo')
        var_table.add('${var2}', 'bar')
        vars.set_from_variable_table(var_table)
        result = vars.replace_variables('hoo${var1}hii${var2}huu')
        assert_equals('hoofoohiibarhuu',result)

    def test_variable_resolving_with_unresolvable_value(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock())
        var_table.add('${var1}', '${unresolvable variable}')
        var_table.add('${var2}', 'bar')
        vars.set_from_variable_table(var_table)
        assert_true('${var1}' in [v.name for v in vars])
        assert_true('${var2}' in [v.name for v in vars])

    def test_has_default_values(self):
        vars = _VariableStash()
        assert_true('${SPACE}' in [v.name for v in vars])
        assert_true('${PREV_TEST_MESSAGE}' in [v.name for v in vars])

    def test_global_variable_trues_value_is_replaced_with_true(self):
        assert_equals(_VariableStash().replace_variables('${True}'), True)

    def test_global_variable_falses_value_is_replaced_with_false(self):
        assert_equals(_VariableStash().replace_variables('${False}'), False)

    def test_global_variable_nones_value_is_replaced_with_none(self):
        assert_equals(_VariableStash().replace_variables('${None}'), None)

    def test_global_variable_nulls_value_is_replaced_with_none(self):
        assert_equals(_VariableStash().replace_variables('${null}'), None)

class TestResourceGetter(_DataFileTest):

    def test_resource_getter(self):
        resources = self.ns.get_resources(self.tcf)
        assert_equals(len(resources),8)
        paths = []
        for res in resources:
            normalized = normalizing.normpath(res.source)
            assert_false(normalized in paths)
            paths.append(normalized)


class TestResourceCache(_DataFileTest):

    def setUp(self):
        self.res_cache = self.ns.res_cache

    def test_file_read_only_once(self):
        imp = Resource(None, RESOURCE_PATH)
        first = self.res_cache.get_resource(imp.directory, imp.name)
        second = self.res_cache.get_resource(imp.directory, imp.name)
        assert_true(first is second)

    def test_file_with_absolute_path(self):
        imp = Resource(ParentMock(), RESOURCE_PATH)
        assert_true(self.res_cache.get_resource(imp.directory, imp.name))

    def test_file_with_invalid_path(self):
        imp = Resource(ParentMock(), '${kumikameli}')
        assert_none(self.res_cache.get_resource(imp.directory, imp.name))


if __name__ == "__main__":
    unittest.main()
