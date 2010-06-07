import os
import unittest

from robot.parsing.settings import Resource
from robot.utils import normalizing
from robot.utils.asserts import assert_true, assert_false, assert_not_none, \
    assert_equals, fail, assert_none
from robotide.namespace import Namespace
from robotide.namespace.namespace import VariableStash
from robotide.robotapi import TestCaseFile
from robot.parsing.model import VariableTable



DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        '..', 'resources', 'robotdata')
RESOURCE_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                              'resource.html'))
RESOURCE_LIB_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                                  'resource_lib_imports.txt'))
RESOURCE_WITH_VARS = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                                   'resource_with_variables.txt'))
TESTCASEFILE_WITH_EVERYTHING = os.path.normpath(os.path.join(DATAPATH, 'testsuite',
                                                   'everything.html'))
RESOURCE_WITH_VARIABLE_IN_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                                   'resu.${extension}'))


def _build_test_case_file():
    tcf = TestCaseFile()
    tcf.directory = '/tmp/'
    _add_settings_table(tcf)
    _add_variable_table(tcf)
    _add_keyword_table(tcf)
    return tcf

def _add_settings_table(tcf):
    tcf.setting_table.add_library('Operating System')
    tcf.setting_table.add_resource(RESOURCE_PATH)
    tcf.setting_table.add_resource(RESOURCE_LIB_PATH)
    tcf.setting_table.add_resource('${resname}')
    tcf.setting_table.add_library('${libname}')
    tcf.setting_table.add_library('${libname}')
    tcf.setting_table.add_resource(RESOURCE_WITH_VARIABLE_IN_PATH)

def _add_variable_table(tcf):
    tcf.variable_table.add('${libname}', 'Collections')
    tcf.variable_table.add('${resname}', RESOURCE_WITH_VARS)
    tcf.variable_table.add('${extension}', 'txt')

def _add_keyword_table(tcf):
    uk_table = tcf.keyword_table
    uk_table.add('Should be in keywords Uk')


class _DataFileTest(unittest.TestCase):
    tcf = _build_test_case_file()
    ns = Namespace()


class TestKeywordSuggestions(_DataFileTest):

    def test_getting_suggestions_for_empty_datafile(self):
        start = 'shOulD'
        sugs = self.ns.get_suggestions_for(self.tcf, start)
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.name.lower().startswith(start.lower()))

    def test_getting_suggestions_in_order(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'sHoUlD')
        assert_true(len(sugs) > 2)
        assert_equals(sugs, sorted(sugs))

    def test_user_keywords(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'sHoUlD')
        assert_true('Should be in keywords Uk' in [s.name for s in sugs])

    def test_imported_lib_keywords(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'create file')
        self._assert_import_kws(sugs, 'OperatingSystem')

    def test_lib_from_resource_file(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'generate random')
        self._assert_import_kws(sugs, 'String')

    def test_lib_import_from_var(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'Copy List')
        self._assert_import_kws(sugs, 'Collections')

    def test_resource_file_keywords(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'Resource Uk')
        self._assert_import_kws(sugs, 'resource.html')

    def test_keywords_normalization(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'Reso   Urceuk')
        self._assert_import_kws(sugs, 'resource.html')

    def test_uk_from_resource_files_resource_file(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'UK From Text Resource')
        self._assert_import_kws(sugs, 'resource.txt')

    def test_resource_file_from_variable(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'UK From Variable Resource')
        self._assert_import_kws(sugs, 'resource_with_variables.txt')

    def test_resource_file_from_resource_file_with_variable(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'UK From Resource from Resource with Variable')
        self._assert_import_kws(sugs, 'resource_from_resource_with_variable.txt')

    def test_library_from_resourcefile_variable(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'Execute Manual')
        self._assert_import_kws(sugs, 'Dialogs')

    def test_keywords_only_once_per_source(self):
        sugs = self.ns.get_suggestions_for(self.tcf, '')
        kw_set = []
        for kw in sugs:
            key = 'kw: %s %s' % (kw.name, kw.source)
            assert_false(key in kw_set)
            kw_set.append(key)

    def test_resource_with_variable_in_path(self):
        sugs = self.ns.get_suggestions_for(self.tcf, 'Resu UK')
        self._assert_import_kws(sugs, 'resu.txt')

    def _assert_import_kws(self, sugs, source):
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.source.endswith(source),
                        '%s does not end with %s' % (s.source, source))


class TestKeywordSearch(_DataFileTest):

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

    def assert_in_keywords(self, keywords, *kw_names):
        for kw_name in kw_names:
            if not self._in_keywords(keywords, kw_name):
                fail(kw_name)

    def _in_keywords(self, keywords, kw_name):
        return any([kw_name.lower() == kw.name.lower() for kw in keywords])


class TestFindUserKeyword(_DataFileTest):

    def test_find_uk(self):
        assert_not_none(self.ns.find_user_keyword(self.tcf, 'UK From Resource from Resource with Variable'))
        assert_none(self.ns.find_user_keyword(self.tcf, 'Copy List'))


class TestVariableStash(unittest.TestCase):

    def test_variable_resolving(self):
        vars = VariableStash()
        var_table = VariableTable(None)
        var_table.add('${var1}', 'foo')
        var_table.add('${var2}', 'bar')
        vars.add_vars(var_table)
        result = vars.replace_variables('hoo${var1}hii${var2}huu')
        assert_equals('hoofoohiibarhuu',result)


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


class ParentMock(object):
    directory = '/tmp/exmaple'
