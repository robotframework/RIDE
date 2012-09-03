import unittest
import datafilereader


class TestImportErrors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        chief = datafilereader.construct_chief_controller(datafilereader.IMPORT_ERRORS)
        suite = chief.data.suites[0]
        cls.imports =  [i for i in suite.imports]

    def _find_by_name(self, name):
        for i in self.imports:
            if i.name == name:
                return i
        raise AssertionError('No import found with name "%s"' % name)

    def _has_error(self, name):
        self.assertTrue(self._find_by_name(name).has_error(), 'Import "%s" should have error' % name)

    def _has_no_error(self, name):
        self.assertFalse(self._find_by_name(name).has_error(), 'Import "%s" should have no error' % name)

    def test_importing_existing_resource_has_no_error(self):
        self._has_no_error('res//existing.txt')

    def test_importing_existing_library_from_pythonpath_has_no_error(self):
        self._has_no_error('String')

    def test_importing_existing_library_with_path_has_no_error(self):
        self._has_no_error('libs//existing.py')

    def test_importing_none_existing_resource_has_error(self):
        self._has_error('res//none_existing.txt')

    def test_importing_none_existing_library_has_error(self):
        self._has_error('libs//none_existing.py')

    def test_importing_corrupted_library_has_error(self):
        self._has_error('libs//corrupted.py')

    def test_resource_import_with_variable_has_no_error(self):
        self._has_no_error('${RESU}')

    def test_library_import_with_variable_has_no_error(self):
        self._has_no_error('${LIB}')


if __name__ == '__main__':
    unittest.main()
