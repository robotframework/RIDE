import unittest
from robotide.controller.chiefcontroller import Backup


class BackupTestCase(unittest.TestCase):

    def setUp(self):
        self._backupper = _MyBackup()

    def test_backup_is_restored_when_save_raises_exception(self):
        try:
            with self._backupper:
                raise _SaveFailed('expected')
            self.fail('should not get here')
        except _SaveFailed:
            self.assertTrue(self._backupper.restored)
        self.assertEqual(None, self._backupper._backup)

    def test_backup_is_not_restored_when_save_passes(self):
        with self._backupper:
            pass
        self.assertFalse(self._backupper.restored)
        self.assertEqual(None, self._backupper._backup)


class _SaveFailed(Exception):
    pass


class _MyBackup(Backup):

    def __init__(self):
        self._path = object()
        self._backup = object()
        self.restored = False

    def _make_backup(self):
        self._backup = object()

    def _restore_backup(self):
        if not self._backup:
            raise AssertionError('No backup')
        self.restored = True

    def _remove_backup(self):
        self._backup = None

if __name__ == '__main__':
    unittest.main()
