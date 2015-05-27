import unittest

from robotide.controller.project import Backup


class BackupTestCase(unittest.TestCase):

    def setUp(self):
        file_controller = lambda: None
        file_controller.filename = 'some_filename.txt'
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
