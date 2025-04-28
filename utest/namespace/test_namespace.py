import sys
import unittest

import pytest

from robotide.robotapi import (
    TestCaseFile, Resource, VariableTable, TestDataDirectory)
from robotide.context import IS_WINDOWS
from robotide.namespace.namespace import _VariableStash
from robotide.controller.basecontroller import WithNamespace
from robotide.controller.filecontrollers import data_controller
from robotide.spec.iteminfo import ArgumentInfo, VariableInfo
from robotide.spec.librarymanager import LibraryManager
from robotide.utils import normpath
from utest.resources.datafilereader import *
from utest.resources.mocks import FakeSettings
from robot import version

VERSION = version.VERSION

RESOURCES_DIR = 'resources'

sys.path.append(os.path.join(os.path.dirname(__file__), '..', RESOURCES_DIR,
                             'robotdata', 'libs'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', RESOURCES_DIR,
                             'robotdata', 'put_into_python_path'))

OS_LIB = 'OperatingSystem'
COLLECTIONS_LIB = 'Collections'
STRING_LIB = 'String'
DATETIME_LIB = 'DateTime'
DATETIME_LIB_ALIAS = 'calendarhour'
RES_NAME_VARIABLE = '${resname}'
LIB_NAME_VARIABLE = '${libname}'
UNRESOLVABLE_VARIABLE = '${unresolvable}'
UNKNOWN_VARIABLE = '${this var does not exist}'
EXTENSION_VAR = '${extension}'
EXTENSION = 'robot'
INVALID_FILE_PATH = '/this/is/invalid.py'
EXISTING_USER_KEYWORD = 'Should be in keywords Uk'
COLLIDING_ARGUMENT = '${colliding argument}'
COLLIDING_CONSTANT = COLLIDING_ARGUMENT.upper()


def _build_test_case_file():
    tcf = TestCaseFile()
    tcf.source = 'tmp.robot'
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
    tcf.setting_table.add_library(UNRESOLVABLE_VARIABLE)
    tcf.setting_table.add_library(LIBRARY_WITH_SPACES_IN_PATH)
    tcf.setting_table.add_library(DATETIME_LIB, ['AS', DATETIME_LIB_ALIAS])
    tcf.setting_table.add_resource(RESOURCE_WITH_VARIABLE_IN_PATH)
    tcf.setting_table.add_variables(INVALID_FILE_PATH)


def _add_variable_table(tcf):
    tcf.variable_table.add(LIB_NAME_VARIABLE, COLLECTIONS_LIB)
    tcf.variable_table.add(RES_NAME_VARIABLE, RESOURCE_WITH_VARS)
    tcf.variable_table.add(EXTENSION_VAR, EXTENSION)
    tcf.variable_table.add(UNRESOLVABLE_VARIABLE, UNKNOWN_VARIABLE)
    tcf.variable_table.add(COLLIDING_CONSTANT, 'collision')
    tcf.variable_table.add('&{dict var}', {'key': 'value'})
    tcf.variable_table.add(u'${I <3 Unicode and \xe4iti}', u'123 \xe7')


def _add_keyword_table(tcf):
    uk_table = tcf.keyword_table
    uk_table.add(EXISTING_USER_KEYWORD)
    uk_table.keywords[0].args.value = [
        '${keyword argument}', '${colliding argument}',
        '${keyword argument with default} = default']


class ParentMock(object):
    source = '/tmp/example/parentmock'
    directory = '/tmp/example'
    report_invalid_syntax = lambda *args: None
    language = ['en']


class _DataFileTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tcf = _build_test_case_file()
        cls.tcf_ctrl = data_controller(cls.tcf, None)
        cls.kw = cls.tcf_ctrl.keywords[0]
        cls.ns = Namespace(FakeSettings())
        cls.library_manager = LibraryManager(':memory:')
        cls.library_manager.start()
        cls.library_manager.create_database()
        cls.ns.set_library_manager(cls.library_manager)

    @classmethod
    def tearDownClass(cls):
        cls.library_manager.stop()
        cls.library_manager = None


class TestKeywordSuggestions(_DataFileTest):

    def test_get_cached_lib_names(self):
        project = WithNamespace()
        project._set_namespace(self.ns)
        lib_names = project.get_all_cached_library_names()
        assert lib_names == []

    def test_getting_suggestions_for_empty_datafile(self):
        start = 'shOulD'
        # print("DEBUG: %s kw %s\n" % (start, self.kw.__doc__))
        sugs = self.ns.get_suggestions_for(self.kw, start)
        assert len(sugs) > 0
        for s in sugs:
            assert s.name.lower().startswith(start.lower())

    def test_getting_suggestions_in_order(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'sHoUlD')
        assert len(sugs) > 2
        assert sugs == sorted(sugs)

    def test_user_keywords(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'sHoUlD')
        assert EXISTING_USER_KEYWORD in [s.name for s in sugs]

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
        # remove variable suggestions
        sugs = [s for s in sugs if not isinstance(s, VariableInfo)]
        self._assert_import_kws(sugs, 'spacelib')

    def test_resource_file_keywords(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Resource Uk')
        self._assert_import_kws(sugs, RESOURCES_RESOURCE)

    def test_resource_file_keyword_with_longname(self):
        sugs = self.ns.get_suggestions_for(
            self.kw, RESOURCES_RESOURCE.replace('.resource', '') + '.Resource Uk')
        self._assert_import_kws(sugs, RESOURCES_RESOURCE)

    def test_keywords_normalization(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Reso   Urceuk')
        self._assert_import_kws(sugs, RESOURCES_RESOURCE)

    def test_uk_from_resource_files_resource_file(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'UK From Text Resource')
        self._assert_import_kws(sugs, 'resource.robot')

    def test_resource_file_from_variable(self):
        sugs = self.ns.get_suggestions_for(
            self.kw, 'UK From Variable Resource')
        self._assert_import_kws(sugs, 'resource_with_variables.robot')

    def test_resource_file_from_resource_file_with_variable(self):
        sugs = self.ns.get_suggestions_for(
            self.kw, 'UK From Resource from Resource with Variable')
        self._assert_import_kws(
            sugs, 'resource_from_resource_with_variable.robot')

    def test_library_from_resourcefile_variable(self):
        import os
        import pytest
        # DISPLAY = os.getenv('DISPLAY')
        # if not DISPLAY:
        #     pytest.skip("Skipped because of missing DISPLAY")  # Avoid failing unit tests in system without X11
        sugs = self.ns.get_suggestions_for(self.kw, 'Execute Manual')
        self._assert_import_kws(sugs, 'Dialogs')

    def test_xml_library(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(
            TESTCASEFILE_WITH_EVERYTHING).keywords[0], 'Attributeless Keyword')
        self._assert_import_kws(sugs, 'LibSpecLibrary')

    def test_xml_library_is_library_keyword(self):
        everything_tcf = TestCaseFile(
            source=TESTCASEFILE_WITH_EVERYTHING).populate()
        assert self.ns.is_library_keyword(
            everything_tcf, 'Attributeless Keyword')

    def test_variable_path_separator(self):
        sugs = self.ns.get_suggestions_for(
            self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
            'foo')
        self._assert_import_kws(sugs, 'even_more_resources.robot')

    def test_keywords_only_once_per_source(self):
        sugs = self.ns.get_suggestions_for(self.kw, '')
        kw_set = []
        for kw in sugs:
            if self._not_variable(kw):
                key = 'kw: %s %s' % (kw.name, kw.source)
                assert not key in kw_set, key
                kw_set.append(key)

    def _not_variable(self, item):
        return not (item.name.startswith('$') or item.name.startswith('@') or
                    item.name.startswith('&'))

    def test_global_variable_list_suggestions(self):
        global_vars = [name for name in _VariableStash.global_variables]
        self._test_global_variable(global_vars[0])
        self._test_global_variable(global_vars[5])
        self._test_global_variable(global_vars[-1])

    def _test_global_variable(self, variable, expected=None):
        assert (expected or variable ==
                      self.ns.get_suggestions_for(self.kw, variable)[0].name)

    def test_resource_with_variable_in_path(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'Resu UK')
        self._assert_import_kws(sugs, 'resu.robot')

    def test_scalar_variable_suggestion(self):
        scalar_vars = self.ns.get_suggestions_for(self.kw, '$')
        assert len(scalar_vars) > 0
        assert len(self.ns.get_suggestions_for(
            self.kw, '${')) == len(scalar_vars)
        sug = self.ns.get_suggestions_for(self.kw, '${lib')
        assert sug[0].name == LIB_NAME_VARIABLE

    def test_list_variable_suggestion(self):
        list_vars = self.ns.get_suggestions_for(self.kw, '@')
        assert len(list_vars) > 0
        assert len(self.ns.get_suggestions_for(self.kw, '@{')) == len(list_vars)

    def test_dict_variable_suggestion(self):
        dict_vars = self.ns.get_suggestions_for(self.kw, '&')
        assert len(dict_vars) > 0
        assert len(self.ns.get_suggestions_for(self.kw, '&{')) == len(dict_vars)

    def test_variable_suggestions_without_varwrapping(self):
        self._test_global_variable('space', '${SPACE}')
        self._test_global_variable('EMP', '${EMPTY}')

    # @pytest.mark.skipif(VERSION.startswith('7.'), reason="This test fails with Robot >= 7.0")
    def test_vars_from_file(self):
        sugs = self.ns.get_suggestions_for(
            self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
            '${var_from_file')
        assert len(sugs) > 0

    def _get_controller(self, source):
        return data_controller(TestCaseFile(source=source).populate(), None)

    def test_library_arguments_are_resolved(self):
        sugs = self.ns.get_suggestions_for(
            self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
            'Get ')
        assert len(sugs) > 0
        for item in sugs:
            if item.name == 'Get Mandatory':
                return
        raise AssertionError('Get mandatory not found')

    def test_vars_from_path_resource_file(self):
        sugs = self.ns.get_suggestions_for(
            self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
            '${Path RESOURCE var')
        assert len(sugs) > 0

    # @pytest.mark.skipif(VERSION.startswith('7.'), reason="This test fails with Robot >= 7.0")
    def test_variable_file_arguments_are_resolved(self):
        sugs = self.ns.get_suggestions_for(
            self._get_controller(TESTCASEFILE_WITH_EVERYTHING).keywords[0],
            '${dyn ')
        assert len(sugs) > 0

    # @pytest.mark.skipif(VERSION.startswith('7.'), reason="This test fails with Robot >= 7.0")
    def test_variable_file_variables_are_available_in_resource_imports(self):
        sugs = self.ns.get_suggestions_for(self._get_controller(
            TESTCASEFILE_WITH_RESOURCES_WITH_VARIABLES_FROM_VARIABLE_FILE
            ).tests[0], 'from resource with variable in pa')
        self._assert_import_kws(sugs, 'res.robot')

    def test_vars_from_keyword_arguments(self):
        sugs = self.ns.get_suggestions_for(self.kw, '${keyword argu')
        assert len(sugs) == 2
        sugs = self.ns.get_suggestions_for(
            self.kw, '${keyword argument with defau')
        assert len(sugs) == 1
        self._check_source(
            self.kw, '${keyword argument with defau', ArgumentInfo.SOURCE)

    def test_argument_is_superior_to_variable_from_variable_table(self):
        sugs = self.ns.get_suggestions_for(self.kw, COLLIDING_ARGUMENT[0:4])
        # DEBUG was getting bytes on python3
        myflag = False
        for s in sugs:
            if isinstance(s.source, str):
                myflag = (s.source == ArgumentInfo.SOURCE)
            else:
                myflag = (s.source.decode('utf-8') == ArgumentInfo.SOURCE)
            if myflag:
                break
        assert myflag
        # assert_true(any(True for s in sugs if s.source.decode('utf-8') == ArgumentInfo.SOURCE))

    # @unittest.skipIf(sys.platform.startswith("win"), "Fails on Windows")
    def test_keyword_arguments_are_suggested_first(self):
        sugs = self.ns.get_suggestions_for(self.kw, '')
        print(f"DEBUG: test_namespace.py test_keyword_arguments_are_suggested_first sugs={sugs}")
        self._assert_import_kws(sugs[:2], ArgumentInfo.SOURCE)

    def test_suggestions_for_datafile(self):
        import os
        import pytest
        import wx
        # DISPLAY = os.getenv('DISPLAY')
        # if not DISPLAY:
        #     pytest.skip("Skipped because of missing DISPLAY")  # Avoid failing unit tests in system without X11
        sugs = self.ns.get_suggestions_for(self.tcf_ctrl, 'Execute Manual')
        print(f"DEBUG: test_suggestions_for_datafile  suggestions for Dialogs {sugs}")
        self._assert_import_kws(sugs, 'Dialogs')
        sugs = self.ns.get_suggestions_for(self.tcf_ctrl, '${libna')
        assert len(sugs) == 1

    # @pytest.mark.skipif(VERSION.startswith('7.'), reason="This test fails with Robot >= 7.0")
    def test_variable_sources(self):
        everything_tcf = self._get_controller(TESTCASEFILE_WITH_EVERYTHING)
        self._check_source(everything_tcf, '${arg}', 'everything.robot')
        self._check_source(everything_tcf, '@{list}', 'everything.robot')
        # self._check_source(everything_tcf, '${dynamic var}', 'dynamic_varz.py')
        self._check_source(
            everything_tcf, '${OPERATING SYSTEM}', 'another_resource.robot')

    def test_relative_imports(self):
        relative_tcf = self._get_controller(RELATIVE_IMPORTS)
        self._check_source(relative_tcf, 'local', 'local')

    def _check_source(self, controller, name, source):
        sugs = self.ns.get_suggestions_for(controller, name)
        assert len(sugs) == 1
        # assert_equal(str(sugs[0].source), str(source))  # DEBUG was getting bytes on python3
        if isinstance(sugs[0].source, str):
            assert sugs[0].source == source
        else:
            assert sugs[0].source.decode('utf-8') == source 

    def _assert_import_kws(self, sugs, source):
        assert len(sugs) > 0
        for s in sugs:
            if isinstance(s.source, str):
                assert s.source.endswith(source), '%s does not end with %s' % (s.source, source)
            else:
                assert s.source.endswith(source.encode('utf-8')), '%s does not end with %s' % (s.source, source)
            print("DEBUG: %s TEST endswith %s" % (s.source if isinstance(s.source, str) else str(s.source, 'utf-8'), source))

    def test_reset(self):
        sugs = self.ns.get_suggestions_for(self.kw, 'generate random')
        sugs2 = self.ns.get_suggestions_for(self.kw, 'generate random')
        assert sugs[0] is sugs2[0]
        self.ns.reset_resource_and_library_cache()
        sugs3 = self.ns.get_suggestions_for(self.kw, 'generate random')
        assert not sugs[0] is sugs3[0]


class TestKeywordSearch(_DataFileTest):

    def test_is_library_keyword(self):
        assert self.ns.is_library_keyword(self.tcf, 'Should Be Equal')
        assert not self.ns.is_library_keyword(self.tcf, 'kameli')
        assert not self.ns.is_library_keyword(
            self.tcf, 'UK From Resource from Resource with Variable')

    def test_is_library_keyword_longname(self):
        assert self.ns.is_library_keyword(self.tcf, 'Builtin.Should Be Equal')

    @pytest.mark.skip("Investigate why fails  with Python 3.13")
    def test_is_library_keyword_longname_with_alias(self):
        # print(f"DEBUG: test_namespace.py test_is_library_keyword_longname_with_alias {DATETIME_LIB_ALIAS+'.Current Date'}")
        assert self.ns.is_library_keyword(self.tcf, DATETIME_LIB_ALIAS+'.Current Date')

    def test_find_default_keywords(self):
        all_kws = self.ns.get_all_keywords([])
        assert all_kws is not None
        self.assert_in_keywords(all_kws, 'Should Be Equal')

    def test_find_suite_keywords(self):
        everything_tcf = TestCaseFile(
            source=TESTCASEFILE_WITH_EVERYTHING).populate()
        all_kws = self.ns.get_all_keywords([self.tcf, everything_tcf])
        self.assert_in_keywords(all_kws, 'Should be in keywords Uk',
                                         'Copy List',
                                         'Uk From Variable Resource')
        self.assert_in_keywords(all_kws, 'My Test Setup',
                                         'My Suite Teardown')

    def test_resource_kws_only_once(self):
        directory = TestDataDirectory(source=SIMPLE_TEST_SUITE_PATH).populate()
        all_kws = self.ns.get_all_keywords(directory.children)
        self._check_resource_keyword_only_once(all_kws)

    def test_resource_kws_only_once_through_project(self):
        # print("DEBUG: project path %s\n" % (SIMPLE_TEST_SUITE_PATH))
        project = construct_project(SIMPLE_TEST_SUITE_PATH+"/TestSuite1.robot")
        # print("DEBUG: project %s key %s\n" % (project.name, project.get_all_keywords))
        all_kws = project.get_all_keywords()
        project.close()
        # print("DEBUG: all keys %s\n" % all_kws)
        self._check_resource_keyword_only_once(all_kws)

    def _check_resource_keyword_only_once(self, all_kws):
        results = [(kw.name, kw.source)
                   for kw in all_kws if kw.name == "Only From Resource"]
        assert len(results) == 1
        # assert_equal(results[0], (u'Only From Resource', u'testdata_resource.robot'))
        assert results[0][0] == u'Only From Resource'
        # DEBUG was getting bytes on python3
        if isinstance(results[0][1], str):
            assert results[0][1] == 'testdata_resource.robot'
        else:
            assert results[0][1].decode('utf-8') == u'testdata_resource.robot'

    def test_find_user_keyword_name_normalized(self):
        assert self.ns.find_user_keyword(
            self.tcf, 'UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(self.tcf, 'Copy List') is None

    def test_is_user_keyword(self):
        assert self.ns.is_user_keyword(
            self.tcf, 'UKFromResource from ResourcewithVariable')
        assert not self.ns.is_user_keyword(self.tcf, 'hevoinen')
        assert not self.ns.is_user_keyword(self.tcf, 'Should Be Equal')

    def test_is_user_keyword_in_resource_file(self):
        everything_tcf = TestCaseFile(
            source=TESTCASEFILE_WITH_EVERYTHING).populate()
        assert self.ns.find_user_keyword(everything_tcf, 'Duplicate UK') is not None
        assert self.ns.is_user_keyword(everything_tcf, 'Duplicate UK')
        assert self.ns.find_user_keyword(everything_tcf, 'Another Resource UK') is not None
        assert self.ns.is_user_keyword(everything_tcf, 'Another Resource UK')

    def test_given_when_then_and_aliases(self):
        assert self.ns.find_user_keyword(
            self.tcf, 'Given   UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(
            self.tcf, 'when  UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(
            self.tcf, 'then UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(
            self.tcf, 'AND UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(
            self.tcf, 'but UK Fromresource from rESOURCE with variaBLE') is not None
        assert self.ns.find_user_keyword(
            self.tcf, 'given and UK Fromresource from rESOURCE with variaBLE') is None

    def assert_in_keywords(self, keywords, *kw_names):
        for kw_name in kw_names:
            if not self._in_keywords(keywords, kw_name):
                raise AssertionError(kw_name)

    def _in_keywords(self, keywords, kw_name):
        return any([kw_name.lower() == kw.name.lower() for kw in keywords])


class TestVariableStash(unittest.TestCase):

    def _variable_stash_contains(self, name, vars):
        assert '${{{0}}}'.format(name) in [v.name for v in vars]

    def test_variable_resolving(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock(), ['En'])
        var_table.add('${var1}', 'foo')
        var_table.add('${var2}', 'bar')
        vars.set_from_variable_table(var_table)
        result = vars.replace_variables('hoo${var1}hii${var2}huu')
        assert 'hoofoohiibarhuu' == result

    def test_list_variable_index_resolving(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock(), ['En'])
        var_table.add('@{var}', ['foo', 'bar'])
        vars.set_from_variable_table(var_table)
        assert 'Hi, foo!' == vars.replace_variables('Hi, @{var}[0]!')

    def test_dict_variable_key_resolving(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock(), ['En'])
        var_table.add('&{var}', ['foo=bar'])
        vars.set_from_variable_table(var_table)
        assert 'Hi, bar!' == vars.replace_variables('Hi, &{var}[foo]!')

    def test_variable_resolving_with_unresolvable_value(self):
        vars = _VariableStash()
        var_table = VariableTable(ParentMock(), ['En'])
        var_table.add('${var1}', '${unresolvable variable}')
        var_table.add('${var2}', 'bar')
        vars.set_from_variable_table(var_table)
        self._variable_stash_contains('var1', vars)
        self._variable_stash_contains('var2', vars)

    def test_has_default_values(self):
        vars = _VariableStash()
        self._variable_stash_contains('SPACE', vars)
        self._variable_stash_contains('PREV_TEST_MESSAGE', vars)

    def test_global_variable_trues_value_is_replaced_with_true(self):
        assert _VariableStash().replace_variables('${True}') == True

    def test_global_variable_falses_value_is_replaced_with_false(self):
        assert _VariableStash().replace_variables('${False}') == False

    def test_global_variable_nones_value_is_replaced_with_none(self):
        assert _VariableStash().replace_variables('${None}') == None

    def test_global_variable_nulls_value_is_replaced_with_none(self):
        assert _VariableStash().replace_variables('${null}') == None


class TestResourceGetter(_DataFileTest):

    def test_resource_getter(self):
        resources = self.ns.get_resources(self.tcf)
        assert len(resources) == 8
        paths = []
        for res in resources:
            normalized = normpath(res.source)
            assert not normalized in paths
            paths.append(normalized)


class TestResourceCache(_DataFileTest):

    def setUp(self):
        self._res_cache = self.ns._resource_factory

    def test_file_read_only_once(self):
        imp = Resource(None, RESOURCE_PATH)
        first = self._res_cache.get_resource(imp.directory, imp.name)
        second = self._res_cache.get_resource(imp.directory, imp.name)
        assert first is second

    def test_file_with_absolute_path(self):
        imp = Resource(ParentMock(), RESOURCE_PATH)
        assert self._res_cache.get_resource(imp.directory, imp.name)

    def test_file_with_invalid_path(self):
        imp = Resource(ParentMock(), '${kumikameli}')
        assert self._res_cache.get_resource(imp.directory, imp.name) is None

    if IS_WINDOWS:
        def test_case_sensetive_filenames(self):
            imp = Resource(None, RESOURCE_PATH)
            first = self._res_cache.get_resource(
                imp.directory, imp.name.lower())
            second = self._res_cache.get_resource(
                imp.directory, imp.name.upper())
            assert first is second


if __name__ == "__main__":
    unittest.main()
