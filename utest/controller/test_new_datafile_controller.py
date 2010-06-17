import os
import tempfile
import unittest

from robot.utils.asserts import assert_true, assert_equals
from robotide.controller import NewDatafileController
from robotide.controller.filecontroller import TestCaseFileController, \
    TestDataDirectoryController


class NewDataFileTest(unittest.TestCase):

    def test_creating_new_datafile(self):
        ctrl = NewDatafileController('./foo.txt', False)
        assert_equals(ctrl.name, 'Foo')
        assert_true(isinstance(ctrl, TestCaseFileController))

    def test_creating_directory_data(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        initpath = os.path.join(dirname, '__init__.html')
        ctrl = NewDatafileController(initpath, True)
        assert_equals(ctrl.name, 'Controller')
        assert_true(isinstance(ctrl, TestDataDirectoryController))

    def test_creating_new_data_created_missing_subdirs(self):
        dirname = os.path.join(tempfile.gettempdir(), 'rideutest-newdirectory')
        if os.path.isdir(dirname):
            os.rmdir(dirname)
        ctrl = NewDatafileController(os.path.join(dirname, 'mynew_tcf.html'),
                                     False)
        assert_equals(ctrl.name, 'Mynew Tcf')
        assert_true(os.path.isdir(dirname))
        os.rmdir(dirname)
