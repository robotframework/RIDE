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

from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.publish.messages import RideUserKeywordAdded,\
    RideUserKeywordRemoved, RideTestCaseAdded, RideTestCaseRemoved,\
    RideItemNameChanged
from robotide.controller.ctrlcommands import AddKeyword, RemoveMacro, Undo,\
    AddTestCase, add_keyword_from_cells, RenameTest
from robotide.publish import PUBLISHER

from controller.base_command_test import _testcase_controller


class _TestMacroCommands(object):

    def setUp(self):
        for listener, topic in [(self._on_keyword_added, RideUserKeywordAdded),
                                (self._on_keyword_deleted,
                                 RideUserKeywordRemoved),
                                (self._on_test_added, RideTestCaseAdded),
                                (self._on_test_deleted, RideTestCaseRemoved)]:
            PUBLISHER.subscribe(listener, topic)

    def tearDown(self):
        self._new_keyword = None
        self._deleted_keyword = None
        self._new_test = None
        self._deleted_test = None

    def _exec(self, command):
        return self._ctrl.execute(command)

    def _on_keyword_added(self, message):
        self._new_keyword = message.item

    def _on_keyword_deleted(self, message):
        self._deleted_keyword = message.item

    def _on_test_added(self, message):
        self._new_test = message.item

    def _on_test_deleted(self, message):
        self._deleted_test = message.item

    def test_add_keyword_command_with_name(self):
        new_kw_name = 'Floajask'
        self._exec(AddKeyword(new_kw_name))
        assert self._new_keyword.name == new_kw_name
        assert self._new_keyword.arguments.value == ''

    def test_add_keyword_command_with_step(self):
        new_kw_name = 'Akjskajs'
        self._exec(add_keyword_from_cells([new_kw_name, 'foo', 'bar']))
        assert self._new_keyword.name == new_kw_name
        assert self._new_keyword.arguments.value == '${arg1} | ${arg2}'

    def test_delete_keyword_command(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        assert self._new_keyword.name == new_kw_name
        self._exec(RemoveMacro(self._new_keyword))
        assert self._deleted_keyword.name == new_kw_name

    def test_add_keyword_undo(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        assert self._new_keyword.name == new_kw_name
        self._exec(Undo())
        assert self._deleted_keyword.name == new_kw_name

    def test_delete_keyword_undo(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        self._exec(RemoveMacro(self._new_keyword))
        self._new_keyword = None
        self._exec(Undo())
        assert self._new_keyword.name == new_kw_name

    def test_add_test(self):
        new_test_name = 'Kalle'
        self._exec(AddTestCase(new_test_name))
        assert self._new_test.name == new_test_name

    def test_remove_test(self):
        test_name = 'Kukka'
        tc = self._exec(AddTestCase(test_name))
        self._exec(RemoveMacro(tc))
        assert self._deleted_test.name == test_name

    def test_add_keyword(self):
        new_kw_name = 'Floajask'
        self._exec(AddKeyword(new_kw_name))
        assert self._new_keyword.name == new_kw_name
        assert self._new_keyword.arguments.value == ''

    def test_add_keyword_with_bdd_given(self):
        self._bdd_test('Given', 'george is a dog')
        self._bdd_test('given', 'steve is a cat')

    def _bdd_test(self, prefix, new_kw_name):
        self._exec(AddKeyword(prefix + ' ' + new_kw_name))
        assert self._new_keyword.name == self._bdd_name(prefix,
                                                             new_kw_name)
        assert self._new_keyword.arguments.value == ''

    def test_add_keyword_with_bdd_when(self):
        self._bdd_test('When', 'george runs')
        self._bdd_test('when', 'steve says hello')

    def test_add_keyword_with_bdd_then(self):
        self._bdd_test('Then', 'george sleeps')
        self._bdd_test('then', 'steve goes home')

    def test_add_keyword_with_bdd_and(self):
        self._bdd_test('And', 'the end')
        self._bdd_test('and', 'really no more')

    def test_add_keyword_with_bdd_but(self):
        self._bdd_test('But', 'george awakes')
        self._bdd_test('but', 'steve says bye')


class TestMacroCommandsInTestCaseContext(_TestMacroCommands,
                                         unittest.TestCase):

    def setUp(self):
        _TestMacroCommands.setUp(self)
        self._ctrl = _testcase_controller()

    def _bdd_name(self, prefix, name):
        return name


class TestMacroCommandsInDataFileContext(_TestMacroCommands,
                                         unittest.TestCase):

    def setUp(self):
        _TestMacroCommands.setUp(self)
        self._ctrl = TestCaseFileController(TestCaseFile())

    def _bdd_name(self, prefix, name):
        return prefix + ' ' + name


class TestCaseRenameCommandTest(unittest.TestCase):

    def setUp(self):
        self.ctrl = _testcase_controller()
        PUBLISHER.subscribe(self._test_renamed, RideItemNameChanged)

    def tearDown(self):
        PUBLISHER.unsubscribe(self._test_renamed, RideItemNameChanged)

    def _test_renamed(self, message):
        self._test = message.item

    def test_(self):
        new_name = 'New name'
        self.ctrl.execute(RenameTest(new_name))
        assert self._test.name == new_name


if __name__ == "__main__":
    unittest.main()
