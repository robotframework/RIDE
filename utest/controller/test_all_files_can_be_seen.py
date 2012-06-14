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
        self.assertEqual(len(all_files.suites), 1)
        self.assertEqual(set(c.name for c in all_files.children), set(['Used Resource', 'Unused Resource', 'Tests']))


if __name__ == '__main__':
    unittest.main()
