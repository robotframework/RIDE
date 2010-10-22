from controller.base_command_test import *
from robotide.publish.messages import RideUserKeywordAdded, RideUserKeywordRemoved,\
    RideTestCaseAdded
from robotide.controller.commands import AddKeyword, RemoveMacro, Undo,\
    AddTestCase


class TestMacroCommands(TestCaseCommandTest):

    def setUp(self):
        TestCaseCommandTest.setUp(self)
        for listener, topic in [(self._on_keyword_added, RideUserKeywordAdded),
                                (self._on_keyword_deleted, RideUserKeywordRemoved),
                                ]:
            PUBLISHER.subscribe(listener, topic)

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
        self._exec(RemoveMacro(self._new_keyword))
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
        self._exec(RemoveMacro(self._new_keyword))
        self._new_keyword = None
        self._exec(Undo())
        assert_equals(self._new_keyword.name, new_kw_name)


class TestDataFileCommands(unittest.TestCase):

    def setUp(self):
        self._ctrl = TestCaseFileController(TestCaseFile())
        for listener, topic in [(self._on_macro_added, RideUserKeywordAdded),
                                (self._on_macro_added, RideTestCaseAdded)]:
            PUBLISHER.subscribe(listener, topic)

    def tearDown(self):
        self._new_macro = None

    def _on_macro_added(self, message):
        self._new_macro = message.item

    def _exec(self, command):
        self._ctrl.execute(command)

    def test_add_test(self):
        new_test_name = 'Kalle'
        self._exec(AddTestCase(new_test_name))
        assert_equals(self._new_macro.name, new_test_name)

    def test_add_keyword(self):
        new_kw_name = 'Floajask'
        self._exec(AddKeyword(new_kw_name))
        assert_equals(self._new_macro.name, new_kw_name)
        assert_equals(self._new_macro.arguments.value, '')


if __name__ == "__main__":
    unittest.main()
