import unittest
import datafilereader


class TestImports(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chief = datafilereader.construct_chief_controller(datafilereader.IMPORTS)
        suite = cls.chief.data.suites[0]
        cls.imports =  [i for i in suite.imports]

    @classmethod
    def tearDownClass(cls):
        cls.chief.close()

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

    def test_importing_system_exiting_library_has_error(self):
        self._has_error('libs//exiting.py')

    def test_resource_import_with_variable_has_no_error(self):
        self._has_no_error('${RESU}')

    def test_library_import_with_variable_has_no_error(self):
        self._has_no_error('${LIB}')

    def test_variable_import_has_no_error(self):
        self._has_no_error('vars//vars.py')

    def test_importing_none_existing_variable_file_has_error(self):
        self._has_error('vars//none_existing.py')

    def test_importing_exiting_variable_file_has_error(self):
        self._has_error('vars//exiting.py')


if __name__ == '__main__':
    unittest.main()
