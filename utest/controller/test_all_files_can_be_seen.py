import unittest
import datafilereader

class TestAllFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chief = datafilereader.construct_chief_controller(datafilereader.ALL_FILES_PATH)

    def test_all_files_can_be_seen(self):
        all_files = self.chief.data
        self.assertEqual(all_files.name, 'All Files')
        self.assertEqual(len(all_files.suites), 2)
        self._verify_names(all_files, 'Used Resource', 'Unused Resource', 'resource_dir', 'Suite Dir', 'Suite2 Dir')
        resource_dir = self._get_child(all_files, 'resource_dir')
        self._verify_names(resource_dir, 'Unused')
        suite_dir = self._get_child(all_files, 'Suite Dir')
        self._verify_names(suite_dir, 'Suite')

    def _get_child(self, controller, name):
        return [c for c in controller.children if c.name == name][0]

    def _verify_names(self, controller, *names):
        self.assertEqual(set(c.name for c in controller.children), set(names))

    def test_unused_resource_knows_it_is_unused(self):
        unused = datafilereader.get_ctrl_by_name('Unused Resource', self.chief.datafiles)
        self.assertFalse(unused.is_used())

    def test_used_resource_knows_it_is_used(self):
        used = datafilereader.get_ctrl_by_name('Used Resource', self.chief.datafiles)
        self.assertTrue(used.is_used())


if __name__ == '__main__':
    unittest.main()
