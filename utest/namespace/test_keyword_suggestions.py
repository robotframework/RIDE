import os
import unittest

from robot.parsing.settings import Resource
from robot.utils import normalizing
from robot.utils.asserts import assert_true, assert_false, \
    assert_not_none, assert_equals
from robotide.namespace.keyword_suggestions import KeywordSuggestions, Namespace, \
    ResourceCache
from robotide.robotapi import TestCaseFile


DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        '..', 'resources', 'robotdata')
RESOURCE_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                              'resource.html'))
RESOURCE_LIB_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                                  'resource_lib_imports.txt'))
RESOURCE_WITH_VARS = os.path.normpath(os.path.join(DATAPATH, 'resources',
                                                   'resource_with_variables.txt'))


class TestKeywordSuggestions(unittest.TestCase):

    def setUp(self):
        self.tcf = self._build_test_case_file()
        self.ns = Namespace(self.tcf)
        self.kw_suggestions = KeywordSuggestions(self.ns)

    def _build_test_case_file(self):
        tcf = TestCaseFile()
        self._add_settings_table(tcf)
        self._add_variable_table(tcf)
        self._add_keyword_table(tcf)
        return tcf

    def _add_settings_table(self, tcf):
        tcf.setting_table.add_library('Operating System')
        tcf.setting_table.add_resource(RESOURCE_PATH)
        tcf.setting_table.add_resource(RESOURCE_LIB_PATH)
        tcf.setting_table.add_resource('${resname}')
        tcf.setting_table.add_library('${libname}')

    def _add_variable_table(self, tcf):
        tcf.variable_table.add('${libname}', 'Collections')
        tcf.variable_table.add('${resname}', RESOURCE_WITH_VARS)

    def _add_keyword_table(self, tcf):
        uk_table = tcf.keyword_table
        uk_table.add('Should be in keywords Uk')

    def test_kw_suggestions_creation(self):
        assert_not_none(KeywordSuggestions(self.ns))

    def test_getting_suggestions_for_empty_datafile(self):
        start = 'shOulD'
        sugs = self.kw_suggestions.get_suggestions_for(start)
        for s in sugs:
            assert_true(s.name.lower().startswith(start.lower()))

    def test_getting_suggestions_in_order(self):
        sugs = self.kw_suggestions.get_suggestions_for('sHoUlD')
        assert_true(len(sugs) > 2)
        assert_equals(sugs, sorted(sugs))

    def test_user_keywords(self):
        sugs = self.kw_suggestions.get_suggestions_for('sHoUlD')
        assert_true('Should be in keywords Uk' in [s.name for s in sugs])

    def test_imported_lib_keywords(self):
        sugs = self.kw_suggestions.get_suggestions_for('create file')
        self._assert_import_kws(sugs, 'OperatingSystem')

    def test_lib_from_resource_file(self):
        sugs = self.kw_suggestions.get_suggestions_for('generate random')
        self._assert_import_kws(sugs, 'String')

    def test_lib_import_from_var(self):
        sugs = self.kw_suggestions.get_suggestions_for('Copy List')
        self._assert_import_kws(sugs, 'Collections')

    def test_resource_file_keywords(self):
        sugs = self.kw_suggestions.get_suggestions_for('Resource Uk')
        self._assert_import_kws(sugs, 'resource.html')

    def test_uk_from_resource_files_resource_file(self):
        sugs = self.kw_suggestions.get_suggestions_for('UK From Text Resource')
        self._assert_import_kws(sugs, 'resource.txt')

    def test_resource_file_from_variable(self):
        sugs = self.kw_suggestions.get_suggestions_for('UK From Variable Resource')
        self._assert_import_kws(sugs, 'resource_with_variables.txt')

    def test_library_from_resourcefile_variable(self):
        sugs = self.kw_suggestions.get_suggestions_for('Execute Manual')
        self._assert_import_kws(sugs, 'Dialogs')

    def test_keywords_only_once_per_source(self):
        sugs = self.kw_suggestions.get_suggestions_for('')
        kw_set = []
        for kw in sugs:
            key = 'kw: %s %s' % (kw.name, kw.source)
            assert_false(key in kw_set)
            kw_set.append(key)

    def _assert_import_kws(self, sugs, source):
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.source.endswith(source))


class TestResourceGetter(unittest.TestCase):

    def setUp(self):
        self.tcf = self._build_test_case_file()
        self.ns = Namespace(self.tcf)

    def _build_test_case_file(self):
        tcf = TestCaseFile()
        self._add_settings_table(tcf)
        self._add_variable_table(tcf)
        return tcf

    def _add_settings_table(self, tcf):
        tcf.setting_table.add_resource(RESOURCE_PATH)
        tcf.setting_table.add_resource(RESOURCE_LIB_PATH)
        tcf.setting_table.add_resource('${resname}')

    def _add_variable_table(self, tcf):
        return tcf.variable_table.add('${resname}', RESOURCE_WITH_VARS)

    def test_resource_getter(self):
        resources = self.ns.get_resources()
        assert_equals(len(resources),6)
        paths = []
        for res in resources:
            normalized = normalizing.normpath(res.source)
            assert_false(normalized in paths)
            paths.append(normalized)


class TestResourceCache(unittest.TestCase):

    def setUp(self):
        self.rc = ResourceCache()

    def test_file_read_only_once(self):
        imp = Resource(None, RESOURCE_PATH)
        first = self.rc.get_resource(imp.directory, imp.name)
        second = self.rc.get_resource(imp.directory, imp.name)
        assert_true(first is second)

    def test_file_with_absolute_path(self):
        imp = Resource(ParentMock(), RESOURCE_PATH)
        assert_true(self.rc.get_resource(imp.directory, imp.name))


class ParentMock(object):
    directory = '/tmp/exmaple'
