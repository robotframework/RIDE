import os
import tempfile
import unittest

from robot.utils.asserts import assert_true, assert_equals
from robotide.controller import NewDatafile


class NewDataFileTest(unittest.TestCase):

    def test_creating_new_datafile(self):
        ctrl = NewDatafile('./foo.txt', False)
        assert_equals(ctrl.name, 'Foo')

    def test_creating_directory_data(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        initpath = os.path.join(dirname, '__init__.html')
        ctrl = NewDatafile(initpath, True)
        assert_equals(ctrl.name, 'Controller')

    def test_creating_new_data_created_missing_subdirs(self):
        dirname = os.path.join(tempfile.gettempdir(), 'rideutest-newdirectory')
        if os.path.isdir(dirname):
            os.rmdir(dirname)
        ctrl = NewDatafile(os.path.join(dirname, 'mynew_tcf.html'),
                                     False)
        assert_equals(ctrl.name, 'Mynew Tcf')
        assert_true(os.path.isdir(dirname))
        os.rmdir(dirname)
