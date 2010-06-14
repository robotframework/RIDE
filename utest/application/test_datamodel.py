#  Copyright 2008 Nokia Siemens Networks Oyj
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
import tempfile
import os

from robotide.application import ChiefController
from robotide.namespace import Namespace
from robot.utils.asserts import assert_none, assert_false, assert_equals,\
    assert_true, assert_raises_with_msg
from robotide import utils
from robotide.errors import DataError
from resources import SUITEPATH, RESOURCE_PATH, INVALID_PATH, PATH_RESOURCE_NAME


class _FakeTree(object):
    remove_item = add_test = add_user_keyword = lambda *args: None


class TestModelInitialization(unittest.TestCase):

    def test_initing_with_no_path_sets_suite_as_none(self):
        model = ChiefController(Namespace())
        assert_none(model.suite)

    def test_initing_with_nonexisting_path_with_extension_creates_new_file_suite(self):
        path = tempfile.mktemp('.html')
        assert_false(os.path.exists(path))
        model = ChiefController(Namespace(), path)
        assert_equals(model.suite.name, utils.printable_name_from_path(path))
        assert_true(isinstance(model.suite, TestCaseFile))

    def test_initing_with_nonexisting_path_without_extension_creates_new_dir_suite(self):
        path = tempfile.mktemp()
        assert_false(os.path.exists(path))
        model = ChiefController(Namespace(), path)
        assert_equals(model.suite.name, utils.printable_name_from_path(path))
        assert_true(isinstance(model.suite, TestCaseFile))

    def test_initing_with_path_to_resource(self):
        model = ChiefController(Namespace(), RESOURCE_PATH)
        assert_none(model.suite)
        assert_equals(model.resources[0].name, os.path.basename(RESOURCE_PATH))

    def test_initing_with_existing_non_robot_file_fails(self):
        msg = "Given file '%s' is not a valid Robot Framework test case or " \
              "resource file" % INVALID_PATH
        assert_raises_with_msg(DataError, msg, ChiefController, Namespace(),
                               INVALID_PATH)


class TestDataModelInAction(unittest.TestCase):

    def setUp(self):
        self.model = ChiefController(Namespace(), SUITEPATH)

    def test_resolving_simple_resource_import(self):
        assert_equals(self.model.resources[0].name, 'resource.html')
        assert_equals(self.model.resources[1].name, PATH_RESOURCE_NAME)
        assert_equals(self.model.resources[2].name, 'Spec Resource')


if __name__ == '__main__':
    unittest.main()
