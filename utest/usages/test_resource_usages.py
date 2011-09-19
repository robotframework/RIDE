import unittest
import datafilereader
from robot.utils.asserts import assert_equals, assert_true
from robotide.usages.commands import FindResourceUsages


class ResourceUsageTests(unittest.TestCase):

    # NOTE! The data is shared among tests
    # This is for performance reasons but be warned when you add tests!
    @classmethod
    def setUpClass(cls):
        ctrl = datafilereader.construct_chief_controller(datafilereader.OCCURRENCES_PATH)
        cls.ts1 = datafilereader.get_ctrl_by_name('TestSuite1', ctrl.datafiles)
        cls.ts2 = datafilereader.get_ctrl_by_name('TestSuite2', ctrl.datafiles)
        cls.resu = datafilereader.get_ctrl_by_name(datafilereader.OCCURRENCES_RESOURCE_NAME, ctrl.datafiles)

    def test_resource_usages_finding(self):
        assert_equals(self.resu, self.ts1.imports[0].get_imported_resource_file_controller())
        assert_equals(self.resu, self.ts2.imports[0].get_imported_resource_file_controller())
        usages = [u.item for u in self.resu.execute(FindResourceUsages())]
        assert_equals(len(usages), 2)
        assert_true(self.ts1.imports in usages)
        assert_true(self.ts2.imports in usages)


if __name__ == '__main__':
    unittest.main()
