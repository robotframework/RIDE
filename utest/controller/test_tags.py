import unittest
from robot.utils.asserts import fail, assert_true, assert_false
from controller_creator import testcase_controller
from robotide.controller.tags import Tag, DefaultTag, ForcedTag
from robotide.controller.commands import ChangeTag
from robotide.controller.settingcontrollers import TagsController


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

    def test_changing_tag(self):
        tag = Tag('tag')
        test = testcase_controller()
        test.tags.add(tag)
        test.tags.execute(ChangeTag(tag, 'foo'))
        assert_true(any(t for t in test.tags if t.name == 'foo'))
        assert_false(any(t for t in test.tags if t.name == 'tag'))

    def test_changing_empty_tag_adds_tag(self):
        name = 'sometag'
        test = testcase_controller()
        test.tags.execute(ChangeTag(test.tags.empty_tag(), name))
        assert_true(any(t for t in test.tags if t.name == name))

    def test_changing_partial_tag(self):
        test = testcase_controller()
        test.tags.add(Tag('tag'))
        partial = Tag('ag')
        test.tags.add(partial)
        test.tags.execute(ChangeTag(partial, 'foo'))
        assert_true(any(t for t in test.tags if t.name == 'foo'))
        assert_true(any(t for t in test.tags if t.name == 'tag'))
        assert_false(any(t for t in test.tags if t.name == 'ag'))

    def test_changing_tags_does_not_change_total_number_of_tags(self):
        tag_to_change = Tag('tagistano')
        test = testcase_controller()
        test.tags.add(tag_to_change)
        test.datafile_controller.force_tags.add(ForcedTag('suite'))
        test.datafile_controller.parent.force_tags.add(ForcedTag('directory'))
        assert_true(3 == sum(1 for _ in test.tags))
        test.tags.execute(ChangeTag(tag_to_change, 'foobar'))
        assert_true(3 == sum(1 for _ in test.tags))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()