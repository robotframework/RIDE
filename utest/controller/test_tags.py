import unittest
from robot.utils.asserts import fail, assert_true
from controller_creator import testcase_controller
from robotide.controller.tags import Tag, DefaultTag, ForcedTag


class Test(unittest.TestCase):

    def test_tests_tag_is_shown(self):
        tag = Tag('tag')
        test = testcase_controller()
        test.tags.add(tag)
        assert_true(tag in test.tags)

    def test_default_from_suite(self):
        tag = DefaultTag('suite tag')
        test = testcase_controller()
        suite = test.datafile_controller
        suite.default_tags.add(tag)
        assert_true(tag in test.tags)

    def test_overwriting_default(self):
        tag_to_overwrite = DefaultTag('suite tag')
        tag = Tag('overwriter')
        test = testcase_controller()
        suite = test.datafile_controller
        suite.default_tags.add(tag_to_overwrite)
        test.tags.add(tag)
        assert_true(tag_to_overwrite not in test.tags)
        assert_true(tag in test.tags)

    def test_force_tag_from_suite(self):
        force_tag = ForcedTag('force tag')
        test = testcase_controller()
        suite = test.datafile_controller
        suite.force_tags.add(force_tag)
        assert_true(force_tag in test.tags)

    def test_force_tag_from_suites_parent_directory(self):
        force_tag = ForcedTag('forced from directory')
        test = testcase_controller()
        directory = test.datafile_controller.parent
        directory.force_tags.add(force_tag)
        assert_true(force_tag in test.tags)

    def test_force_tag_from_suites_parents_parent_directory(self):
        force_tag = ForcedTag('forced from directory')
        test = testcase_controller()
        directory = test.datafile_controller.parent.parent
        directory.force_tags.add(force_tag)
        assert_true(force_tag in test.tags)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()