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

import random
import unittest
import os
import tempfile
import shutil
from nose.tools import assert_true, assert_false, assert_equal

from robotide.robotapi import TestCaseFile, TestDataDirectory, ResourceFile
from robotide.controller.ctrlcommands import (
    DeleteResourceAndImports, DeleteFile, SaveFile)
from robotide.controller.filecontrollers import (
    TestCaseFileController, TestDataDirectoryController,
    ResourceFileController)
from robotide.controller import Project
from robotide.publish.messages import RideDataFileRemoved
from robotide.publish import PUBLISHER
from robotide.namespace.namespace import Namespace
from robotide.spec.librarymanager import LibraryManager
from resources.mocks import FakeSettings


def create_test_data(path, filepath, resourcepath, initpath):
    if not os.path.exists(path):
        os.mkdir(path)
    with open(filepath, 'w') as file:
        file.write('''\
*Settings*
Resource  resource.txt
*Test Cases*
Ride Unit Test  No Operation
''')
    with open(resourcepath, 'w') as resource:
        resource.write('*Keywords*\nUnit Test Keyword  No Operation\n')
    with open(initpath, 'w') as settings:
        settings.write('''\
*Settings*
Documentation  Ride unit testing file
''')

def remove_test_data(path):
    shutil.rmtree(path)

def create_project():
    library_manager = LibraryManager(':memory:')
    library_manager.create_database()
    return Project(Namespace(FakeSettings()), FakeSettings(), library_manager)


class _DataDependentTest(unittest.TestCase):

    def setUp(self):
        self._dirpath = os.path.join(tempfile.gettempdir(), 'ride_controller_utest_dir'+str(random.randint(0,100000000)))
        self._filepath = os.path.join(self._dirpath, 'tests.txt')
        self._resource_path = os.path.join(self._dirpath, 'resource.txt')
        self._init_path = os.path.join(self._dirpath, '__init__.txt')
        create_test_data(self._dirpath, self._filepath, self._resource_path, self._init_path)

    def tearDown(self):
        remove_test_data(self._dirpath)


class TestModifiedOnDiskWithFileSuite(_DataDependentTest):

    def test_mtime(self):
        ctrl = TestCaseFileController(TestCaseFile(source=self._filepath).populate())
        assert_false(ctrl.has_been_modified_on_disk())
        os.utime(self._filepath, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())

    def test_size_change(self):
        os.utime(self._filepath, None)
        ctrl = TestCaseFileController(TestCaseFile(source=self._filepath).populate())
        with open(self._filepath, 'a') as file:
            file.write('#Ninja edit\n')
        assert_true(ctrl.has_been_modified_on_disk())

    def test_reload(self):
        controller_parent = object()
        model_parent = object()
        ctrl = TestCaseFileController(
            TestCaseFile(parent=model_parent, source=self._filepath).populate(),
            parent=controller_parent)
        assert_equal(len(ctrl.tests), 1)
        with open(self._filepath, 'a') as file:
            file.write('Second Test  Log  Hello World!\n')
        ctrl.reload()
        assert_equal(len(ctrl.tests), 2)
        assert_equal(ctrl.tests[-1].name, 'Second Test')
        assert_equal(ctrl.parent, controller_parent)
        assert_equal(ctrl.data.parent, model_parent)

    def test_overwrite(self):
        ctrl = TestCaseFileController(TestCaseFile(source=self._filepath).populate(),
                                      create_project())
        os.utime(self._filepath, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())
        ctrl.execute(SaveFile())
        assert_false(ctrl.has_been_modified_on_disk())


class TestModifiedOnDiskWithDirectorySuite(_DataDependentTest):

    def test_reload_with_directory_suite(self):
        model_parent = object()
        controller_parent = object()
        ctrl = TestDataDirectoryController(TestDataDirectory(source=self._dirpath, parent=model_parent).populate(),
            parent=controller_parent)
        with open(self._init_path, 'a') as file:
            file.write('...  ninjaed more documentation')
        ctrl.reload()
        assert_equal(ctrl.settings[0].value,
                      'Ride unit testing file\\nninjaed more documentation')
        assert_equal(ctrl.parent, controller_parent)
        assert_equal(ctrl.data.parent, model_parent)

    def test_mtime_with_directory_suite(self):
        ctrl = TestDataDirectoryController(TestDataDirectory(source=self._dirpath).populate())
        assert_false(ctrl.has_been_modified_on_disk())
        os.utime(self._init_path, (1,1))
        assert_true(ctrl.has_been_modified_on_disk())


class TestModifiedOnDiskWithresource(_DataDependentTest):

    def test_reload_with_resource(self):
        controller_parent = lambda:0
        controller_parent.children = []
        controller_parent.add_child = controller_parent.children.append
        ctrl = ResourceFileController(ResourceFile(source=self._resource_path).populate(), parent=controller_parent)
        assert_equal(len(ctrl.keywords), 1)
        with open(self._resource_path, 'a') as fp:
            fp.write('Ninjaed Keyword  Log  I am taking over!\n')
        ctrl.reload()
        assert_equal(len(ctrl.keywords), 2)
        assert_equal(ctrl.keywords[-1].name, 'Ninjaed Keyword')
        assert_equal(ctrl.parent, controller_parent)


class TestDataFileRemoval(_DataDependentTest):

    def setUp(self):
        _DataDependentTest.setUp(self)
        PUBLISHER.subscribe(self._datafile_removed, RideDataFileRemoved)

    def tearDown(self):
        _DataDependentTest.tearDown(self)
        PUBLISHER.unsubscribe(self._datafile_removed, RideDataFileRemoved)

    def _datafile_removed(self, message):
        self._removed_datafile = message.datafile

    def test_deleting_source_should_remove_it_from_model(self):
        project = create_project()
        project._controller = TestCaseFileController(TestCaseFile(source=self._filepath), project)
        os.remove(self._filepath)
        ctrl = project.data
        ctrl.remove()
        assert_true(project.data is None)
        assert_true(self._removed_datafile is ctrl)

    def test_deleting_file_suite_under_dir_suite(self):
        project = create_project()
        project._controller = TestDataDirectoryController(TestDataDirectory(source=self._dirpath).populate(), project)
        original_children_length = len(project.data.children)
        file_suite = project.data.children[0]
        file_suite.remove()
        assert_true(len(project.data.children) == original_children_length-1, 'Child suite was not removed')

    def test_deleting_resource_file(self):
        project = create_project()
        res = project.new_resource(self._resource_path)
        res.remove()
        assert_true(len(project.resources) == 0, 'Resource was not removed')

    def test_deleting_init_file(self):
        project = create_project()
        project._controller = TestDataDirectoryController(TestDataDirectory(source=self._dirpath).populate(), project)
        os.remove(self._init_path)
        project.data.remove()
        with open(self._init_path, 'w') as initfile:
            initfile.write('*Settings*\nDocumentation  Ride unit testing file\n')
        assert_true(project.data.has_format() is False, project.data.data.initfile)


class DeleteCommandTest(_DataDependentTest):

    def setUp(self):
        _DataDependentTest.setUp(self)
        self.project = create_project()
        self.project.load_data(self._dirpath)
        self.suite = self.project.suite.children[0]
        self.resource = self.project.resources[0]

    def test_delete_resource_and_imports(self):
        self.assert_resource_count(1)
        self.assert_import_count(1)
        self.resource.execute(DeleteResourceAndImports())
        self.assert_resource_count(0)
        self.assert_import_count(0)

    def test_delete_file(self):
        self.assert_resource_count(1)
        self.assert_import_count(1)
        self.resource.execute(DeleteFile())
        self.assert_resource_count(0)
        self.assert_import_count(1)

    def assert_resource_count(self, resource_count):
        assert_equal(len(self.project.resources), resource_count)

    def assert_import_count(self, import_count):
        assert_equal(len(self.suite.setting_table.imports), import_count)


if __name__ == "__main__":
    unittest.main()
