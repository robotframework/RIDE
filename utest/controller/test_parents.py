import unittest
import datafilereader


class TestParents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = datafilereader.construct_project(
            datafilereader.SIMPLE_TEST_SUITE_PATH)
        cls.directory = cls.project.data
        cls.test = datafilereader.get_ctrl_by_name(
            'TestSuite1', cls.project.datafiles)
        cls.resource = datafilereader.get_ctrl_by_name(
            datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME,
            cls.project.datafiles)
        cls.external_resource = datafilereader.get_ctrl_by_name(
            'Resu', cls.project.datafiles)

    @classmethod
    def tearDownClass(cls):
        cls.project.close()

    def test_test_suite_parent_is_directory(self):
        self.assertEquals(self.test.parent, self.directory)
        self.assertTrue(self.test in self.directory.children)

    def test_local_resource_parent_is_directory(self):
        self.assertEquals(self.resource.parent, self.directory)
        self.assertTrue(self.resource in self.directory.children)

    def test_external_resource_parent_is_undefined(self):
        self.assertEquals(self.external_resource.parent, None)
        self.assertTrue(self.external_resource not in self.directory.children)

if __name__ == '__main__':
    unittest.main()
