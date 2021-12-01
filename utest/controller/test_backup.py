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

from robotide.controller.project import Backup


class BackupTestCase(unittest.TestCase):

    def setUp(self):
        file_controller = lambda: None
        file_controller.filename = 'some_filename.robot'
        file_controller.refresh_stat = lambda: None
        self._backupper = _MyBackup(file_controller)

    def test_backup_is_restored_when_save_raises_exception(self):
        try:
            with self._backupper:
                raise _SaveFailed('expected')
            self.fail('should not get here')
        except _SaveFailed:
            self.assertTrue(self._backupper.restored)

    def test_backup_is_not_restored_when_save_passes(self):
        with self._backupper:
            self.assertNotEqual(None, self._backupper._backup)
        self.assertFalse(self._backupper.restored)
        self.assertEqual(None, self._backupper._backup)

    def test_save_can_be_done_if_backup_move_fails(self):
        def move_fails(*args):
            raise IOError('failed')
        self._backupper._move = move_fails
        save_done = False
        with self._backupper:
            save_done = True
        self.assertTrue(save_done)


class _SaveFailed(Exception):
    pass


class _MyBackup(Backup):

    def __init__(self, file_controller):
        Backup.__init__(self, file_controller)
        self._backup = object()
        self.restored = False

    def _move(self, from_path, to_path):
        self.restored = (self._backup == from_path)

    def _remove_backup(self):
        self._backup = None

    def _remove_backup_dir(self):
        pass


if __name__ == '__main__':
    unittest.main()
