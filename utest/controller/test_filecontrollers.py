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

from robotide.robotapi import TestCase, TestCaseFile, TestDataDirectory
from nose.tools import (assert_equal, assert_true, assert_false)

from robotide.controller.filecontrollers import TestCaseFileController, \
    TestDataDirectoryController, _FileSystemElement
from robotide.controller.tablecontrollers import TestCaseController
from robotide.controller.ctrlcommands import AddTestCaseFile, AddTestDataDirectory,\
    SortKeywords, Undo, Redo
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideDataChangedToDirty,\
RideDataDirtyCleared

from resources import SUITEPATH
import datafilereader


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

    def _changes(self, payload):
        self._has_unsaved_changes = payload.datafile

    def _cleared(self, payload):
        self._saved = payload.datafile

    def test_marking_data_dirty_publishes_data_has_changes_message(self):
        self.ctrl.mark_dirty()
        assert_equal(self._has_unsaved_changes, self.ctrl)

    def test_clearing_dirty_mark_publishes_data_saved_message(self):
        self.ctrl.mark_dirty()
        self.ctrl.unmark_dirty()
        assert_equal(self._saved, self.ctrl)

    def test_remarking_data_dirty_does_not_publish_data_has_changes_message(self):
        self.ctrl.mark_dirty()
        self._has_unsaved_changes = None
        self.ctrl.mark_dirty()
        assert_equal(self._has_unsaved_changes, None)

    def test_reclearing_dirty_mark_does_not_publish_data_saved_message(self):
        self.ctrl.unmark_dirty()
        self._saved = None
        self.ctrl.unmark_dirty()
        assert_equal(self._saved, None)


class TestCaseFileControllerTest(unittest.TestCase):
    SOURCE_HTML = os.path.abspath(os.path.join('tmp', '.path.with.dots', 'test.cases.html'))
    SOURCE_TXT = SOURCE_HTML.replace('.html', '.txt')

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile(source=self.SOURCE_HTML))

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equal(len(self.ctrl.settings), 9)
        assert_false(self.ctrl.dirty)

    def test_has_format(self):
        assert_true(self.ctrl.has_format())

    def test_get_format(self):
        assert_equal(self.ctrl.get_format(), 'html')

    def test_source(self):
        assert_equal(self.ctrl.filename, self.SOURCE_HTML)

    def test_longname(self):
        assert_equal(self.ctrl.longname, 'Test.Cases')
        self.ctrl.parent = lambda:0
        self.ctrl.parent.longname = 'Parent'
        assert_equal(self.ctrl.longname, 'Parent.Test.Cases')

    def test_set_format(self):
        self.ctrl.set_format('txt')
        assert_equal(self.ctrl.filename, self.SOURCE_TXT)

    def test_add_test_or_kw(self):
        assert_equal(len(self.ctrl.tests), 0)
        new_test = TestCaseController(self.ctrl, TestCase(TestCaseFile(), 'New test'))
        self.ctrl.add_test_or_keyword(new_test)
        assert_equal(len(self.ctrl.tests), 1)
        assert_true(self.ctrl.tests[0]._test.parent.parent is self.ctrl.datafile)
        assert_true(self.ctrl.dirty)

    def test_new_test(self):
        test_ctrl = self.ctrl.create_test('Foo')
        assert_equal(test_ctrl.name, 'Foo')

    def test_create_keyword(self):
        kw_ctrl = self.ctrl.create_keyword('An UK')
        assert_equal(kw_ctrl.name, 'An UK')

    def test_create_keyword_with_args(self):
        kw_ctrl = self.ctrl.create_keyword('UK', '${a1} | ${a2}')
        assert_equal(kw_ctrl.name, 'UK')
        assert_equal(kw_ctrl.data.args.value, ['${a1}', '${a2}'])


class TestResourceFileControllerTest(unittest.TestCase):

    def setUp(self):
        self.project = datafilereader.construct_project(datafilereader.SIMPLE_TEST_SUITE_PATH)

    def tearDown(self):
        self.project.close()

    def _get_ctrl_by_name(self, name):
        return datafilereader.get_ctrl_by_name(name , self.project.datafiles)

    def test_resource_file_display_name_is_file_name_with_extension(self):
        resource_ctrl = self._get_ctrl_by_name(datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME)
        assert_equal(resource_ctrl.display_name, datafilereader.SIMPLE_TEST_SUITE_RESOURCE_FILE)

    def test_sort_and_restore_keywords(self):
        resource_ctrl = self._get_ctrl_by_name(datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME)

        # Capture keyword list before sorting
        original_keywords = resource_ctrl.get_keyword_names()
        list_for_undo_comparison = original_keywords[:]

        # Sort the list
        resource_ctrl.execute(SortKeywords())
        sorted_keywords = resource_ctrl.get_keyword_names()
        original_keywords.sort()
        assert_equal(original_keywords, sorted_keywords)

        # Undo sorting
        resource_ctrl.execute(Undo())
        restored_list = resource_ctrl.get_keyword_names()
        assert_equal(restored_list, list_for_undo_comparison)

        # Redo sorting
        resource_ctrl.execute(Redo())
        keywords_after_redo = resource_ctrl.get_keyword_names()
        assert_equal(keywords_after_redo, sorted_keywords)


class TestDataDirectoryControllerTest(unittest.TestCase):
    TEST_CASE_FILE_PATH = os.path.abspath('path/to/suite.txt')
    INIT_FILE_PATH = os.path.abspath('path/to/__init__.txt')
    DATA_DIRECTORY_NAME = os.path.split(os.path.dirname(INIT_FILE_PATH))[-1].title()

    def setUp(self):
        self.data = TestDataDirectory(source='source')

    def test_creation(self):
        ctrl = TestDataDirectoryController(self.data)
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equal(len(ctrl.settings), 6)

    def test_has_format(self):
        ctrl = TestDataDirectoryController(self.data)
        assert_false(ctrl.has_format())
        ctrl.mark_dirty()
        assert_false(ctrl.has_format())
        ctrl.data.initfile = os.path.join('source', '__init__.html')
        assert_true(ctrl.has_format())

    def test_default_dir_is_source(self):
        self.data.initfile = os.path.join('source', '__init__.html')
        ctrl = TestDataDirectoryController(self.data)
        assert_true(ctrl.default_dir, os.path.dirname(ctrl.filename))

    def test_set_format(self):
        ctrl = TestDataDirectoryController(self.data)
        assert_false(ctrl.has_format())
        ctrl.set_format('txt')
        assert_true(ctrl.has_format())
        assert_equal(ctrl.source, os.path.abspath(os.path.join('source', '__init__.txt')))

    def test_longname(self):
        ctrl = TestDataDirectoryController(self.data)
        assert_equal(ctrl.longname, 'Source')
        ctrl.parent = lambda:0
        ctrl.parent.longname = 'Parent'
        assert_equal(ctrl.longname, 'Parent.Source')

    def test_adding_test_case_file(self):
        new_data = TestDataDirectoryController(self.data).\
                    new_test_case_file(self.TEST_CASE_FILE_PATH)
        assert_true(new_data.dirty)
        assert_true(isinstance(new_data, TestCaseFileController))
        assert_equal(new_data.filename, self.TEST_CASE_FILE_PATH)

    def test_adding_test_suite_directory(self):
        new_data = TestDataDirectoryController(self.data).\
                        new_test_data_directory(self.INIT_FILE_PATH)
        assert_true(isinstance(new_data, TestDataDirectoryController))
        assert_equal(new_data.name, self.DATA_DIRECTORY_NAME)
        assert_equal(new_data.filename, self.INIT_FILE_PATH)

    def test_adding_test_case_file_using_command(self):
        ctrl = TestDataDirectoryController(self.data)
        suite = ctrl.execute(AddTestCaseFile(self.TEST_CASE_FILE_PATH))
        assert_equal(suite.data.parent, ctrl.data)

    def test_adding_test_data_directory_using_command(self):
        ctrl = TestDataDirectoryController(self.data)
        suite = ctrl.execute(AddTestDataDirectory(self.INIT_FILE_PATH))
        assert_equal(suite.data.parent, ctrl.data)

    def test_exclude(self):
        parent = lambda:0
        project = self._mock_project()
        ctrl = TestDataDirectoryController(self.data, project, parent)
        parent.children = [ctrl]
        ctrl.exclude()
        self.assertEqual(len(parent.children), 1)
        self.assertTrue(parent.children[0].is_excluded())
        self.assertTrue(self.called)

    def _mock_project(self):
        project = lambda:0
        project._namespace = lambda:0
        project.resource_file_controller_factory = lambda:0
        project.is_datafile_dirty = lambda *_:False
        project._settings = lambda:0
        project._settings.excludes = lambda:0
        self.called = False

        def update_excludes(new_excludes):
            self.assertEqual(len(new_excludes), 1)
            self.assertTrue(new_excludes[0].endswith('source'))
            self.called = True
        project._settings.excludes.update_excludes = update_excludes
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
                if controller.filename and controller.filename.endswith('test.txt'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df
                in self.directory_controller.iter_datafiles()]
        assert_true(check_count_and_sub_dir.iteration_count == 5)
        assert_true(check_count_and_sub_dir.in_sub_dir)


class TestRelativePathTo(unittest.TestCase):

    def test_relative_path_to(self):
        fse1 = _FileSystemElement('foo.txt', 'bar')
        fse2 = _FileSystemElement('zoo.html', 'goo')
        self.assertEqual('../goo/zoo.html', fse1.relative_path_to(fse2))
        self.assertEqual('../bar/foo.txt', fse2.relative_path_to(fse1))


if __name__ == '__main__':
    unittest.main()
