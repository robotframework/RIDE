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

import os
import tempfile
import unittest

from nose.tools import assert_true, assert_equal
from robotide.controller.robotdata import NewTestCaseFile, NewTestDataDirectory


class NewDataFileTest(unittest.TestCase):

    def test_creating_new_datafile(self):
        ctrl = NewTestCaseFile('./foo.robot')
        assert_equal(ctrl.name, 'Foo')

    def test_creating_directory_data(self):
        dirname = os.path.dirname(os.path.abspath(__file__))
        initpath = os.path.join(dirname, '__init__.html')
        ctrl = NewTestDataDirectory(initpath)
        assert_equal(ctrl.name, 'Controller')

    def test_creating_new_data_created_missing_subdirs(self):
        dirname = os.path.join(tempfile.gettempdir(), 'rideutest-newdirectory')
        if os.path.isdir(dirname):
            os.rmdir(dirname)
        ctrl = NewTestCaseFile(os.path.join(dirname, 'mynew_tcf.html'))
        assert_equal(ctrl.name, 'Mynew Tcf')
        assert_true(os.path.isdir(dirname))
        os.rmdir(dirname)


if __name__ == '__main__':
    unittest.main()

