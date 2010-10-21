from controller.base_command_test import *
from robotide.publish.messages import RideUserKeywordAdded, RideUserKeywordRemoved
from robotide.controller.commands import AddKeyword, RemoveUserScript, Undo


class TestKeywordCommands(TestCaseCommandTest):

    def setUp(self):
        TestCaseCommandTest.setUp(self)
        PUBLISHER.subscribe(self._on_keyword_added, RideUserKeywordAdded)
        PUBLISHER.subscribe(self._on_keyword_deleted, RideUserKeywordRemoved)

    def _on_keyword_added(self, message):
        self._new_keyword = message.item

    def _on_keyword_deleted(self, message):
        self._deleted_keyword = message.item

    def test_add_keyword_command_with_name(self):
        new_kw_name = 'Floajask'
        self._exec(AddKeyword(new_kw_name))
        assert_equals(self._new_keyword.name, new_kw_name)
        assert_equals(self._new_keyword.arguments.value, '')

    def test_add_keyword_command_with_step(self):
        new_kw_name = 'Akjskajs'
        self._exec(AddKeyword(new_kw_name, ['foo', 'bar']))
        assert_equals(self._new_keyword.name, new_kw_name)
        assert_equals(self._new_keyword.arguments.value, '${arg1} | ${arg2}')

    def test_delete_keyword_command(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        assert_equals(self._new_keyword.name, new_kw_name)
        self._exec(RemoveUserScript(self._new_keyword))
        assert_equals(self._deleted_keyword.name, new_kw_name)

    def test_add_keyword_undo(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        assert_equals(self._new_keyword.name, new_kw_name)
        self._exec(Undo())
        assert_equals(self._deleted_keyword.name, new_kw_name)

    def test_delete_keyword_undo(self):
        new_kw_name = 'Jiihaa'
        self._exec(AddKeyword(new_kw_name))
        self._exec(RemoveUserScript(self._new_keyword))
        self._new_keyword = None
        self._exec(Undo())
        assert_equals(self._new_keyword.name, new_kw_name)

if __name__ == "__main__":
    unittest.main()
