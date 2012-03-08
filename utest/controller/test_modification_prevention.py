import unittest
from robotide.controller.basecontroller import _BaseController
from robotide.controller.commands import _Command
from robotide.controller.filecontrollers import TestCaseFileController, ResourceFileController
from robotide.controller.macrocontrollers import UserKeywordController, TestCaseController
from robotide.controller.settingcontrollers import _SettingController, LibraryImportController, ResourceImportController
from robotide.controller.stepcontrollers import StepController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideModificationPrevented


class _Controller(_BaseController):

    modifiable = False

    def is_modifiable(self):
        return self.modifiable


class _ModifyingCommand(_Command):

    executed = False

    def execute(self, context):
        self.executed = True


class _SomeSetting(_SettingController):

    def _init(self, *args):
        pass


class ModificationPreventionTestCase(unittest.TestCase):

    def setUp(self):
        self._controller = _Controller()
        self._reset_command()
        PUBLISHER.subscribe(self._modification_prevented, RideModificationPrevented)

    def tearDown(self):
        PUBLISHER.unsubscribe(self._modification_prevented, RideModificationPrevented)

    def _reset_command(self):
        self._command = _ModifyingCommand()
        self._modification_prevented_controller = None

    def _modification_prevented(self, message):
        self._modification_prevented_controller = message.controller

    def test_modification_prevented(self):
        self._execution_prevented()

    def test_modification_allowed(self):
        self._controller.modifiable = True
        self._execution_allowed()

    def test_nonmodifying_command_is_not_prevented(self):
        self._command.modifying = False
        self._execution_allowed()

    def test_nonmodifying_command_implies_no_is_modifiable_call(self):
        self._command.modifying = False
        def no_call():
            raise AssertionError('Should not be called')
        self._controller.is_modifiable = no_call
        self._execution_allowed()

    def test_nonmodifying_command_and_modifications_allowed(self):
        self._command.modifying = False
        self._controller.modifiable = True
        self._execution_allowed()

    def test_test_case_file_modifications_are_prevented_when_file_is_read_only(self):
        self._use_testcasefilecontroller()
        self._controller.is_readonly = lambda: True
        self._execution_prevented()

    def test_test_case_file_modifications_are_allowed_when_file_is_not_read_only(self):
        self._use_testcasefilecontroller()
        self._controller.is_readonly = lambda: False
        self._execution_allowed()

    def test_test_case_file_modifications_are_allowed_when_file_does_not_exist(self):
        self._use_testcasefilecontroller()
        self._controller.exists = lambda: False
        self._execution_allowed()

    def test_resource_file_modifications_are_prevented_when_file_is_read_only(self):
        self._use_resourcefilecontroller()
        self._controller.is_readonly = lambda: True
        self._execution_prevented()

    def test_resource_file_modifications_are_allowed_when_file_is_not_read_only(self):
        self._use_resourcefilecontroller()
        self._controller.is_readonly = lambda: False
        self._execution_allowed()

    def test_resource_file_modifications_are_allowed_when_file_does_not_exist(self):
        self._use_resourcefilecontroller()
        self._controller.exists = lambda: False
        self._execution_allowed()

    def test_settings_are_modifiable_equals_file_is_modifiable(self):
        data = lambda:0
        data.setting_name = 'some setting'
        self._verify_controller_obeys_datafile_modifiability(_SomeSetting, data)

    def test_steps_are_modifiable_equals_file_is_modifiable(self):
        self._verify_controller_obeys_datafile_modifiability(UserKeywordController)
        self._verify_controller_obeys_datafile_modifiability(TestCaseController)

    def test_step_is_modifiable_equals_file_is_modifiable(self):
        data = lambda:0
        data.args = []
        data.comment = None
        self._verify_controller_obeys_datafile_modifiability(StepController, data)

    def test_imports_are_modifiable_equals_file_is_modifiable(self):
        data = lambda:0
        data.type = None
        self._verify_controller_obeys_datafile_modifiability(LibraryImportController, data)
        self._verify_controller_obeys_datafile_modifiability(ResourceImportController, data)

    def test_variables_are_modifiable_equals_file_is_modifiable(self):
        self._verify_controller_obeys_datafile_modifiability(VariableTableController)

    def _verify_controller_obeys_datafile_modifiability(self, controller_class, data=None):
        controller = controller_class(self._parent_with_datafile(), data or (lambda:0))
        controller.datafile_controller.is_modifiable = lambda: False
        self._controller = controller
        self.assertFalse(controller.is_modifiable())
        self._reset_command()
        self._execution_prevented()
        controller.datafile_controller.is_modifiable = lambda: True
        self.assertTrue(controller.is_modifiable())
        self._reset_command()
        self._execution_allowed()

    def _parent_with_datafile(self):
        parent = lambda:0
        parent.datafile_controller = lambda:0
        parent.datafile_controller.register_for_namespace_updates = lambda *args:0
        return parent

    def _use_resourcefilecontroller(self):
        self._create_ctrl(ResourceFileController)

    def _use_testcasefilecontroller(self):
        self._create_ctrl(TestCaseFileController)

    def _create_ctrl(self, clazz):
        data = lambda:0
        data.source = ''
        data.directory = ''
        self._controller = clazz(data)
        self._controller.exists = lambda: True

    def _execution_prevented(self):
        self._controller.execute(self._command)
        self.assertFalse(self._command.executed)
        self.assertEqual(self._controller, self._modification_prevented_controller)

    def _execution_allowed(self):
        self._controller.execute(self._command)
        self.assertTrue(self._command.executed)
        self.assertEqual(None, self._modification_prevented_controller)

if __name__ == '__main__':
    unittest.main()
