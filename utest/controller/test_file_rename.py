import os
import unittest
from nose.tools import assert_equals, assert_true

from robotide.robotapi import TestCaseFile
from robotide.controller.commands import RenameFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.validators import ERROR_ILLEGAL_CHARACTERS, ERROR_EMPTY_FILENAME, ERROR_NEWLINES_IN_THE_FILENAME, ERROR_FILE_ALREADY_EXISTS
from robotide.publish import PUBLISHER, RideFileNameChanged, RideInputValidationError


class TestRenameTestCaseFile(unittest.TestCase):
    _filenames_to_remove = []

    def setUp(self):
        PUBLISHER.subscribe(self._file_name_changed, RideFileNameChanged, "TestRenameTestCaseFile")
        PUBLISHER.subscribe(self._file_name_error, RideInputValidationError, "TestRenameTestCaseFile")
        self._clean_test_files(["quux.txt","some.txt"])

    def tearDown(self):
        self._clean_test_files()
        PUBLISHER.unsubscribe_all("TestRenameTestCaseFile")

    def _clean_test_files(self, paths = None):
        for filename in paths if paths else self._filenames_to_remove:
            try:
                os.remove(filename)
            except OSError:
                pass

    def _file_name_error(self, message):
        self._error_message = message.message

    def _file_name_changed(self, message):
        self._message = message.datafile

    def test_rename_changes_basename_but_keeps_extension(self):
        RenameFile('quux').execute(self._create_controller())
        assert_equals(self._error_message, None)
        assert_equals(self.ctrl.filename, 'quux.txt')
        assert_equals(self.ctrl.data.source, self.ctrl.filename)

    def test_rename_preserves_directory_path(self):
        RenameFile('quux').execute(self._create_controller('foo/bar.html'))
        assert_equals(self._error_message, None)
        assert_true(self.ctrl.filename.endswith(os.path.join('foo', 'quux.html')))

    def test_rename_deletes_old_path(self):
        RenameFile('quux').execute(self._create_controller())
        assert_equals(self._error_message, None)
        assert_true(self.deleted is True)

    def test_rename_saves_file(self):
        RenameFile('quux').execute(self._create_controller())
        assert_equals(self._error_message, None)
        assert_true(self.saved is True)

    def test_rename_publishes_message(self):
        RenameFile('some').execute(self._create_controller())
        assert_equals(self._error_message, None)
        assert_equals(self._message, self.ctrl)

    def test_rename_illegal_character_error(self):
        RenameFile("dsk\//\sdfj$''lkfdsjflk$'\'fdslkjlsuite....").execute(self._create_controller())
        assert_equals(self._error_message, ERROR_ILLEGAL_CHARACTERS)

    def test_rename_empty_name_error(self):
        RenameFile("").execute(self._create_controller())
        assert_equals(self._error_message, ERROR_EMPTY_FILENAME)

    def test_rename_newlines_in_name_error(self):
        RenameFile("ashdjashdhjasd\nasdads").execute(self._create_controller())
        assert_equals(self._error_message, ERROR_NEWLINES_IN_THE_FILENAME)

    def test_rename_already_existing_error(self):
        rename_command = RenameFile("jup")
        rename_command._validator._file_exists = lambda *_: True
        rename_command.execute(self._create_controller())
        assert_equals(self._error_message, ERROR_FILE_ALREADY_EXISTS % "jup.txt")

    def _create_controller(self, path='some.txt'):
        self._filenames_to_remove.append(path)
        self.ctrl = TestCaseFileController(TestCaseFile(source=path))
        self.saved = False
        self.deleted = False
        self._message = None
        self._error_message = None
        def save(*args): self.saved = True
        def remove_from_filesystem(*Args): self.deleted = True
        self.ctrl.save = save
        self.ctrl.remove_from_filesystem = remove_from_filesystem
        return self.ctrl
