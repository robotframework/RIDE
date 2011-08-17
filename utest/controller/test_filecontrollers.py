import unittest
import os
import shutil

from robot.parsing import TestCase
from robot.parsing.model import TestCaseFile, TestDataDirectory
from robot.utils.asserts import (assert_equals, assert_true, assert_false)

from robotide.controller.filecontrollers import TestCaseFileController, \
    TestDataDirectoryController, _DataController
from robotide.controller.tablecontrollers import TestCaseController
from robotide.controller.commands import AddSuite
from robotide.controller import NewDatafile
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideDataChangedToDirty,\
RideDataDirtyCleared

from resources import SUITEPATH
import datafilereader


class TestMarkUnMarkDirty(unittest.TestCase):

    def setUp(self):
        class Data(object):
            source = directory = None
        self.ctrl = _DataController(Data())
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
        assert_equals(self._has_unsaved_changes, self.ctrl)

    def test_clearing_dirty_mark_publishes_data_saved_message(self):
        self.ctrl.mark_dirty()
        self.ctrl.unmark_dirty()
        assert_equals(self._saved, self.ctrl)

    def test_remarking_data_dirty_does_not_publish_data_has_changes_message(self):
        self.ctrl.mark_dirty()
        self._has_unsaved_changes = None
        self.ctrl.mark_dirty()
        assert_equals(self._has_unsaved_changes, None)

    def test_reclearing_dirty_mark_does_not_publish_data_saved_message(self):
        self.ctrl.unmark_dirty()
        self._saved = None
        self.ctrl.unmark_dirty()
        assert_equals(self._saved, None)


class TestCaseFileControllerTest(unittest.TestCase):
    SOURCE_HTML = os.path.abspath(os.path.join('tmp', '.path.with.dots', 'test.cases.html'))
    SOURCE_TXT = SOURCE_HTML.replace('.html', '.txt')

    def setUp(self):
        self.ctrl = TestCaseFileController(TestCaseFile(source=self.SOURCE_HTML))

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(self.ctrl.settings), 9)
        assert_false(self.ctrl.dirty)

    def test_has_format(self):
        assert_true(self.ctrl.has_format())

    def test_get_format(self):
        assert_equals(self.ctrl.get_format(), 'html')

    def test_source(self):
        assert_equals(self.ctrl.filename, self.SOURCE_HTML)

    def test_set_format(self):
        self.ctrl.set_format('txt')
        assert_equals(self.ctrl.filename, self.SOURCE_TXT)

    def test_add_test_or_kw(self):
        assert_equals(len(self.ctrl.tests), 0)
        new_test = TestCaseController(self.ctrl, TestCase(TestCaseFile(), 'New test'))
        self.ctrl.add_test_or_keyword(new_test)
        assert_equals(len(self.ctrl.tests), 1)
        assert_true(self.ctrl.tests[0]._test.parent is self.ctrl.datafile)
        assert_true(self.ctrl.dirty)

    def test_new_test(self):
        test_ctrl = self.ctrl.create_test('Foo')
        assert_equals(test_ctrl.name, 'Foo')

    def test_create_keyword(self):
        kw_ctrl = self.ctrl.create_keyword('An UK')
        assert_equals(kw_ctrl.name, 'An UK')

    def test_create_keyword_with_args(self):
        kw_ctrl = self.ctrl.create_keyword('UK', '${a1} | ${a2}')
        assert_equals(kw_ctrl.name, 'UK')
        assert_equals(kw_ctrl.data.args.value, ['${a1}', '${a2}'])


class TestResourceFileControllerTest(unittest.TestCase):

    def _get_ctrl_by_name(self, name, datafiles):
        for file in datafiles:
            if file.name == name:
                return file
        return None

    def test_resource_file_display_name_is_file_name_with_extension(self):
        chief = datafilereader.construct_chief_controller(datafilereader.OCCURRENCES_PATH)
        resource_ctrl = self._get_ctrl_by_name(datafilereader.OCCURRENCES_RESOURCE_NAME, chief.datafiles)
        assert_equals(resource_ctrl.display_name, datafilereader.OCCURRENCES_RESOURCE_FILE)

class TestDataDirectoryControllerTest(unittest.TestCase):

    def setUp(self):
        self.data = TestDataDirectory(source='source')

    def test_creation(self):
        ctrl = TestDataDirectoryController(self.data)
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(ctrl.settings), 6)

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
        assert_true(ctrl.default_dir, os.path.dirname(ctrl.source))

    def test_set_format(self):
        ctrl = TestDataDirectoryController(self.data)
        assert_false(ctrl.has_format())
        ctrl.set_format('txt')
        assert_true(ctrl.has_format())
        assert_equals(ctrl.source, os.path.abspath(os.path.join('source', '__init__.txt')))

    def test_adding_new_child(self):
        ctrl = TestDataDirectoryController(self.data)
        assert_true(ctrl.new_datafile(NewDatafile('path/to/data.txt',
                                                  is_dir_type=False)))

    def test_adding_new_suite_with_command(self):
        ctrl = TestDataDirectoryController(self.data)
        suite = ctrl.execute(AddSuite(NewDatafile('path/to/suite.txt',
                                                  is_dir_type=False)))
        assert_equals(suite.data.parent, ctrl.data)


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
                if controller.source and controller.source.endswith('test.txt'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df in self.directory_controller.iter_datafiles()]
        assert_true(check_count_and_sub_dir.iteration_count == 5)
        assert_true(check_count_and_sub_dir.in_sub_dir)
