import unittest
from robotide.controller.basecontroller import _BaseController
from robotide.controller.commands import _Command


class _Controller(_BaseController):

    modifiable = False

    def is_modifiable(self):
        return self.modifiable


class _ModifyingCommand(_Command):

    executed = False

    def execute(self, context):
        self.executed = True


class ModificationPreventionTestCase(unittest.TestCase):

    def setUp(self):
        self._command = _ModifyingCommand()
        self._controller = _Controller()

    def test_modification_prevented(self):
        self._controller.execute(self._command)
        self.assertFalse(self._command.executed)

    def test_modification_allowed(self):
        self._controller.modifiable = True
        self._controller.execute(self._command)
        self.assertTrue(self._command.executed)

    def test_nonmodifying_command_is_not_prevented(self):
        self._command.modifying = False
        self._controller.execute(self._command)
        self.assertTrue(self._command.executed)

    def test_nonmodifying_command_and_modifications_allowed(self):
        self._command.modifying = False
        self._controller.modifiable = True
        self._controller.execute(self._command)
        self.assertTrue(self._command.executed)


if __name__ == '__main__':
    unittest.main()
