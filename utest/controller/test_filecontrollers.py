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
import os
import shutil
import sys

import pytest

from robotide.robotapi import TestCase, TestCaseFile, TestDataDirectory

from robotide.controller.filecontrollers import TestCaseFileController, \
    TestDataDirectoryController, _FileSystemElement, start_filemanager, explorer_linux, explorer_mac
from robotide.controller.macrocontrollers import TestCaseController
from robotide.controller.ctrlcommands import AddTestCaseFile, AddTestDataDirectory, \
    SortKeywords, SortTests, SortVariables, Undo, Redo
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideDataChangedToDirty, RideDataDirtyCleared

from utest.resources import SUITEPATH
from utest.resources import datafilereader


class TestMarkUnMarkDirty(unittest.TestCase):

    def setUp(self):
        class Data(object):
            source = directory = None
        self.ctrl = TestCaseFileController(Data())
        self._has_unsaved_changes = False
        self._saved = False
        self.messages = [(self._changes, RideDataChangedToDirty),
                         (self._cleared, RideDataDirtyCleared)]
        for listener, topic in self.messages:
            PUBLISHER.subscribe(listener, topic)

    def tearDown(self):
        for listener, topic in self.messages:
            PUBLISHER.unsubscribe(listener, topic)
        if os.path.exists('path'):
            shutil.rmtree('path')

    def _changes(self, message):
        self._has_unsaved_changes = message.datafile

    def _cleared(self, message):
        self._saved = message.datafile

    def test_marking_data_dirty_publishes_data_has_changes_message(self):
        self.ctrl.mark_dirty()
        assert self._has_unsaved_changes == self.ctrl

    def test_clearing_dirty_mark_publishes_data_saved_message(self):
        self.ctrl.mark_dirty()
        self.ctrl.unmark_dirty()
        assert self._saved == self.ctrl

    def test_remarking_data_dirty_does_not_publish_data_has_changes_message(self):
        self.ctrl.mark_dirty()
        self._has_unsaved_changes = None
        self.ctrl.mark_dirty()
        assert self._has_unsaved_changes is None

    def test_reclearing_dirty_mark_does_not_publish_data_saved_message(self):
        self.ctrl.unmark_dirty()
        self._saved = None
        self.ctrl.unmark_dirty()
        assert self._saved is None


class TestCaseFileControllerTest(unittest.TestCase):
    SOURCE_HTML = os.path.abspath(os.path.join('tmp', '.path.with.dots', 'test.cases.html'))
    SOURCE_TXT = SOURCE_HTML.replace('.html', '.robot')

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile(source=self.SOURCE_HTML))

    def test_creation(self):
        for st in self.ctrl.settings:
            assert st is not None
        assert len(self.ctrl.settings) == 10
        assert not self.ctrl.dirty

    def test_has_format(self):
        assert self.ctrl.has_format()

    def test_get_format(self):
        assert self.ctrl.get_format() == 'html'

    def test_source(self):
        assert self.ctrl.filename == self.SOURCE_HTML

    def test_longname(self):
        assert self.ctrl.longname == 'Test.Cases'
        self.ctrl.parent = lambda: 0
        self.ctrl.parent.longname = 'Parent'
        assert self.ctrl.longname == 'Parent.Test.Cases'

    def test_set_format(self):
        self.ctrl.set_format('robot')
        assert self.ctrl.filename == self.SOURCE_TXT

    def test_add_test_or_kw(self):
        assert len(self.ctrl.tests) == 0
        new_test = TestCaseController(self.ctrl, TestCase(TestCaseFile(), 'New test'))
        self.ctrl.add_test_or_keyword(new_test)
        assert len(self.ctrl.tests) == 1
        assert self.ctrl.tests[0]._test.parent.parent is self.ctrl.datafile
        assert self.ctrl.dirty

    def test_new_test(self):
        test_ctrl = self.ctrl.create_test('Foo')
        assert test_ctrl.name == 'Foo'

    def test_create_keyword(self):
        kw_ctrl = self.ctrl.create_keyword('An UK')
        assert kw_ctrl.name == 'An UK'

    def test_create_keyword_with_args(self):
        kw_ctrl = self.ctrl.create_keyword('UK', '${a1} | ${a2}')
        assert kw_ctrl.name == 'UK'
        assert kw_ctrl.data.args.value == ['${a1}', '${a2}']

    def test_sort_and_restore_tests(self):
        # Add tests
        for test in ['Blabla', 'Atest', '2222222', '111111']:
            new_test = TestCaseController(self.ctrl, TestCase(TestCaseFile(), test))
            self.ctrl.add_test_or_keyword(new_test)

        # Capture test list before sorting
        original_tests = self.get_test_names()
        list_for_undo_comparison = original_tests[:]

        # Sort the list
        self.ctrl.execute(SortTests())
        sorted_tests = self.get_test_names()
        original_tests.sort()
        assert original_tests == sorted_tests

        # Undo sorting
        self.ctrl.execute(Undo())
        restored_list = self.get_test_names()
        assert restored_list == list_for_undo_comparison

        # Redo sorting
        self.ctrl.execute(Redo())
        keywords_after_redo = self.get_test_names()
        assert keywords_after_redo == sorted_tests

    def get_test_names(self):
        return [test.name for test in self.ctrl.tests]


class TestResourceFileControllerTest(unittest.TestCase):

    def setUp(self):
        self.project = datafilereader.construct_project(datafilereader.SIMPLE_TEST_SUITE_PATH)
        self.ctrl = self._get_ctrl_by_name(datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME)

    def tearDown(self):
        self.project.close()

    def _get_ctrl_by_name(self, name):
        return datafilereader.get_ctrl_by_name(name, self.project.datafiles)

    def test_resource_file_display_name_is_file_name_with_extension(self):
        assert self.ctrl.display_name == datafilereader.SIMPLE_TEST_SUITE_RESOURCE_FILE

    def test_sort_and_restore_keywords(self):
        resource_ctrl = self._get_ctrl_by_name(datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME)

        assert resource_ctrl is not None

        # Capture keyword list before sorting
        original_keywords = self.ctrl.get_keyword_names()
        list_for_undo_comparison = original_keywords[:]

        # Sort the list
        self.ctrl.execute(SortKeywords())
        sorted_keywords = self.ctrl.get_keyword_names()
        original_keywords.sort()
        assert original_keywords == sorted_keywords

        # Undo sorting
        self.ctrl.execute(Undo())
        restored_list = self.ctrl.get_keyword_names()
        assert restored_list == list_for_undo_comparison

        # Redo sorting
        self.ctrl.execute(Redo())
        keywords_after_redo = self.ctrl.get_keyword_names()
        assert keywords_after_redo == sorted_keywords

    def test_sort_and_restore_variables(self):
        # Capture test list before sorting
        original_variables = self.get_variable_names()
        list_for_undo_comparison = original_variables[:]

        # Sort the list
        self.ctrl.execute(SortVariables())
        sorted_variables = self.get_variable_names()
        original_variables.sort()
        assert original_variables == sorted_variables

        # Undo sorting
        self.ctrl.execute(Undo())
        restored_list = self.get_variable_names()
        assert restored_list == list_for_undo_comparison

        # Redo sorting
        self.ctrl.execute(Redo())
        variables_after_redo = self.get_variable_names()
        assert variables_after_redo == sorted_variables

    def get_variable_names(self):
        return [variable.name for variable in self.ctrl.variables]


class TestDataDirectoryControllerTest(unittest.TestCase):
    TEST_CASE_FILE_PATH = os.path.abspath('path/to/suite.robot')
    INIT_FILE_PATH = os.path.abspath('path/to/__init__.robot')
    DATA_DIRECTORY_NAME = os.path.split(os.path.dirname(INIT_FILE_PATH))[-1].title()

    def setUp(self):
        self.data = TestDataDirectory(source='source')

    def test_creation(self):
        ctrl = TestDataDirectoryController(self.data)
        for st in ctrl.settings:
            assert st is not None
        assert len(ctrl.settings) == 7

    def test_has_format(self):
        ctrl = TestDataDirectoryController(self.data)
        assert not ctrl.has_format()
        ctrl.mark_dirty()
        assert not ctrl.has_format()
        ctrl.data.initfile = os.path.join('source', '__init__.html')
        assert ctrl.has_format()

    def test_default_dir_is_source(self):
        self.data.initfile = os.path.join('source', '__init__.html')
        ctrl = TestDataDirectoryController(self.data)
        assert ctrl.default_dir, os.path.dirname(ctrl.filename)

    def test_set_format(self):
        ctrl = TestDataDirectoryController(self.data)
        assert not ctrl.has_format()
        ctrl.set_format('robot')
        assert ctrl.has_format()
        assert ctrl.source == os.path.abspath(os.path.join('source', '__init__.robot'))

    def test_longname(self):
        ctrl = TestDataDirectoryController(self.data)
        assert ctrl.longname == 'Source'
        ctrl.parent = lambda: 0
        ctrl.parent.longname = 'Parent'
        assert ctrl.longname == 'Parent.Source'

    def test_adding_test_case_file(self):
        new_data = TestDataDirectoryController(self.data).\
                    new_test_case_file(self.TEST_CASE_FILE_PATH)
        assert new_data.dirty
        assert isinstance(new_data, TestCaseFileController)
        assert new_data.filename == self.TEST_CASE_FILE_PATH

    def test_adding_test_suite_directory(self):
        new_data = TestDataDirectoryController(self.data).\
                        new_test_data_directory(self.INIT_FILE_PATH)
        assert isinstance(new_data, TestDataDirectoryController)
        assert new_data.name == self.DATA_DIRECTORY_NAME
        assert new_data.filename == self.INIT_FILE_PATH

    def test_adding_test_case_file_using_command(self):
        ctrl = TestDataDirectoryController(self.data)
        suite = ctrl.execute(AddTestCaseFile(self.TEST_CASE_FILE_PATH))
        assert suite.data.parent == ctrl.data

    def test_adding_test_data_directory_using_command(self):
        ctrl = TestDataDirectoryController(self.data)
        suite = ctrl.execute(AddTestDataDirectory(self.INIT_FILE_PATH))
        assert suite.data.parent == ctrl.data

    def test_exclude(self):
        parent = lambda: 0
        project = self._mock_project()
        ctrl = TestDataDirectoryController(self.data, project, parent)
        parent.children = [ctrl]
        ctrl.exclude()
        self.assertEqual(len(parent.children), 1)
        self.assertTrue(parent.children[0].is_excluded())
        self.assertTrue(self.called)

    def _mock_project(self):
        project = lambda: 0
        project.namespace = lambda: 0
        project.resource_file_controller_factory = lambda: 0
        project.is_datafile_dirty = lambda *_: False
        project.internal_settings = lambda: 0
        project.internal_settings.excludes = lambda: 0
        self.called = False

        def update_excludes(new_excludes):
            self.assertEqual(len(new_excludes), 1)
            self.assertTrue(new_excludes[0].endswith('source'))
            self.called = True
        project.internal_settings.excludes.update_excludes = update_excludes
        return project


class DatafileIteratorTest(unittest.TestCase):

    def setUp(self):
        test_data_suite = TestDataDirectory(source=SUITEPATH).populate()
        self.directory_controller = TestDataDirectoryController(test_data_suite)

    def test_iterate_all(self):
        class Checker(object):
            def __init__(self):
                self.iteration_count = 0
                self.in_sub_dir = False

            def __call__(self, controller):
                self.iteration_count += 1
                print(controller.filename)
                if controller.filename and controller.filename.endswith('test.robot'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df in self.directory_controller.iter_datafiles()]
        assert check_count_and_sub_dir.iteration_count == 5
        assert check_count_and_sub_dir.in_sub_dir


class TestRelativePathTo(unittest.TestCase):

    def test_relative_path_to(self):
        fse1 = _FileSystemElement('foo.robot', 'bar')
        fse2 = _FileSystemElement('zoo.html', 'goo')
        self.assertEqual('../goo/zoo.html', fse1.relative_path_to(fse2))
        self.assertEqual('../bar/foo.robot', fse2.relative_path_to(fse1))


class TestFileManager(unittest.TestCase):

    def test_explorer_linux(self):
        try:
            explorer_linux('this_path_does_not_exist')
        except Exception as e:
            print(f"DEBUG: TestFileManager raised ERROR {e}")

    def test_explorer_mac(self):
        try:
            explorer_mac('this_path_does_not_exist')
        except Exception as e:
            print(f"DEBUG: TestFileManager raised ERROR {e}")

    @pytest.mark.skipif(sys.platform == 'win32', reason="Fails with exception on Windows")
    def test_start_filemanager_bad_tool(self):
        try:
            start_filemanager(path=__file__, tool='this_tool_does_not_exist')
        except Exception as e:
            print(f"DEBUG: TestFileManager raised ERROR {e}")

    @pytest.mark.skipif(sys.platform == 'win32', reason="Fails with exception on Windows")
    def test_start_filemanager_good_path(self):
        try:
            start_filemanager(path=__file__)
        except Exception as e:
            print(f"DEBUG: TestFileManager raised ERROR {e}")

    def test_start_filemanager_bad_path(self):
        try:
            start_filemanager(path='this_path_does_not_exist')
        except Exception as e:
            print(f"DEBUG: TestFileManager raised ERROR {e}")


if __name__ == '__main__':
    unittest.main()
