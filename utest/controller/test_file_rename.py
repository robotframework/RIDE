import unittest
from robot.parsing.model import TestCaseFile

from robot.utils.asserts import assert_equals, assert_true
from robotide.controller.commands import RenameFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.publish import PUBLISHER, RideFileNameChanged


class TestRenameTestCaseFile(unittest.TestCase):

    def setUp(self):
        PUBLISHER.subscribe(self._file_name_changed, RideFileNameChanged)

    def tearDown(self):
        PUBLISHER.unsubscribe(self._file_name_changed, RideFileNameChanged)

    def _file_name_changed(self, message):
        self._message = message.datafile

    def test_rename_changes_basename_but_keeps_extension(self):
        RenameFile('quux').execute(self._create_controller())
        assert_equals(self.ctrl.filename, 'quux.txt')
        assert_equals(self.ctrl.data.source, 'quux.txt')

    def test_rename_preserves_directory_path(self):
        RenameFile('quux').execute(self._create_controller('foo/bar.html'))
        assert_equals(self.ctrl.filename, 'foo/quux.html')

    def test_rename_deletes_old_path(self):
        RenameFile('quux').execute(self._create_controller())
        assert_true(self.deleted is True)

    def test_rename_saves_file(self):
        RenameFile('quux').execute(self._create_controller())
        assert_true(self.saved is True)

    def test_rename_publishes_message(self):
        RenameFile('some').execute(self._create_controller())
        assert_equals(self._message, self.ctrl)

    def _create_controller(self, path='some.txt'):
        self.ctrl = TestCaseFileController(TestCaseFile(source=path))
        self.saved = False
        self.deleted = False
        self._message = None
        def save(*args): self.saved = True
        def remove_from_filesystem(*Args): self.deleted = True
        self.ctrl.save = save
        self.ctrl.remove_from_filesystem = remove_from_filesystem
        return self.ctrl
