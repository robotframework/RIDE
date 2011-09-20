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

    def test_resource_import_knows_imported_resource_controller(self):
        assert_equals(self.resu, self.ts1.imports[0].get_imported_resource_file_controller())
        assert_equals(self.resu, self.ts2.imports[0].get_imported_resource_file_controller())

    def test_resource_usages_finding(self):
        usages = list(self.resu.execute(FindResourceUsages()))
        self._verify_length(2, usages)
        self._verify_that_contains(self.ts1, usages)
        self._verify_that_contains(self.ts2, usages)

    def _verify_length(self, expected, usages):
        assert_equals(len(usages), expected)

    def _verify_that_contains(self, item, usages):
        for u in usages:
            if u.item == item.imports:
                if item.display_name != u.location:
                    raise AssertionError('location "%s" was not expected "%s"!' % (u.location, item.display_name))
                return
        raise AssertionError('Item %r not in usages %r!' % (item, usages))

    def test_import_in_resource_file(self):
        inner_resu = self.resu.imports[0].get_imported_resource_file_controller()
        usages = list(inner_resu.execute(FindResourceUsages()))
        self._verify_length(1, usages)
        self._verify_that_contains(self.resu, usages)

    def test_none_existing_import(self):
        imp = self.ts1.imports.add_resource('this_does_not_exists.txt')
        assert_equals(imp.get_imported_resource_file_controller(), None)

if __name__ == '__main__':
    unittest.main()
