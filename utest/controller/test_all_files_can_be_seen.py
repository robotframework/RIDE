import unittest
# Used File structure
#
# all_files/__init__.txt         <- main suite
#           tests.txt            <- test suite
#           used_resource.txt    <- tests.txt has an import to this
#           unused_resource.txt  <- valid resource file without referrer
#           some_file.bla        <- not a robot file
#
import datafilereader

class TestAllFilesCanBeSeenCase(unittest.TestCase):

    def test_all_files_can_be_seen(self):
        chief = datafilereader.construct_chief_controller(datafilereader.ALL_FILES_PATH)
        all_files = chief.data
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


if __name__ == '__main__':
    unittest.main()
