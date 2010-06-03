import os
import unittest

from robot.utils.asserts import assert_true, assert_none, assert_false, \
    assert_not_none, assert_equals
from robotide.namespace.keyword_suggestions import KeywordSuggestions, Namespace, \
    ResourceCache
from robotide.robotapi import TestCaseFile
from robot.parsing.settings import Resource


DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        '..', 'resources', 'robotdata')
RESOURCE_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources', 'resource.html'))
RESOURCE_LIB_PATH = os.path.normpath(os.path.join(DATAPATH, 'resources', 'resource_lib_imports.txt'))

class TestKeywordSuggestions(unittest.TestCase):

    def setUp(self):
        self.tcf = self._build_test_case_file()
        self.ns = Namespace(self.tcf)
        self.kw_suggestions = KeywordSuggestions(self.ns)

    def _build_test_case_file(self):
        tcf = TestCaseFile()
        tcf.setting_table.add_library('Operating System')
        tcf.setting_table.add_resource(RESOURCE_PATH)
        tcf.setting_table.add_resource(RESOURCE_LIB_PATH)
        uk_table = tcf.keyword_table
        uk_table.add('Should be in keywords Uk')
        return tcf

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


    def test_resource_file_keywords(self):
        sugs = self.kw_suggestions.get_suggestions_for('Resource Uk')
        self._assert_import_kws(sugs, 'resource.html')

    def test_uk_from_resource_files_resource_file(self):
        sugs = self.kw_suggestions.get_suggestions_for('UK From Text Resource')
        self._assert_import_kws(sugs, 'resource.txt')

    def _assert_import_kws(self, sugs, source):
        assert_true(len(sugs) > 0)
        for s in sugs:
            assert_true(s.source.endswith(source))


class TestResourceCache(unittest.TestCase):

    def setUp(self):
        self.rc = ResourceCache()

    def test_file_read_only_once(self):
        imp = Resource(None, RESOURCE_PATH)
        first = self.rc.get_resource(imp)
        second = self.rc.get_resource(imp)
        assert_true(first is second)

    def test_file_with_absolute_path(self):
        imp = Resource(ParentMock(), RESOURCE_PATH)
        first = self.rc.get_resource(imp)
        assert_true(first)

class ParentMock(object):
    directory = '/tmp/exmaple'