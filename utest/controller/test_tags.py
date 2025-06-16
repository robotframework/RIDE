#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import unittest
from robotide.controller.tags import Tag, DefaultTag, ForcedTag
from robotide.controller.ctrlcommands import ChangeTag

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

try:
    from controller_creator import _testcase_controller
except ModuleNotFoundError:
    from .controller_creator import _testcase_controller


class Test(unittest.TestCase):

    def setUp(self):
        self._test = _testcase_controller()

    @property
    def tags(self):
        return self._test.tags

    def test_tests_tag_is_shown(self):
        tag = Tag('tag')
        self.tags.add(tag)
        assert tag in self.tags

    def test_default_from_suite(self):
        tag = DefaultTag('suite tag')
        suite = self._test.datafile_controller
        suite.default_tags.add(tag)
        assert tag in self.tags

    def test_adding_empty_tag_will_remove_default(self):
        self.test_default_from_suite()
        self._verify_number_of_tags(1)
        t = self.tags.empty_tag()
        self.tags.execute(ChangeTag(t, ''))
        self._verify_number_of_tags(1)
        self._tag_with_name_exists('')

    def test_overwriting_default(self):
        tag_to_overwrite = DefaultTag('suite tag')
        tag = Tag('overwriter')
        suite = self._test.datafile_controller
        suite.default_tags.add(tag_to_overwrite)
        self.tags.add(tag)
        assert tag_to_overwrite not in self.tags
        assert tag in self.tags

    def test_force_tag_from_suite(self):
        force_tag = ForcedTag('force tag')
        suite = self._test.datafile_controller
        suite.force_tags.add(force_tag)
        assert force_tag in self.tags

    def test_force_tag_from_suites_parent_directory(self):
        force_tag = ForcedTag('forced from directory')
        directory = self._test.datafile_controller.parent
        directory.force_tags.add(force_tag)
        assert force_tag in self.tags

    def test_force_tag_from_suites_parents_parent_directory(self):
        force_tag = ForcedTag('forced from directory')
        directory = self._test.datafile_controller.parent.parent
        directory.force_tags.add(force_tag)
        assert force_tag in self.tags

    def test_changing_tag(self):
        tag = Tag('tag')
        self.tags.add(tag)
        self.tags.execute(ChangeTag(tag, 'foo'))
        self._tag_with_name_exists('foo')
        assert not any(t for t in self.tags if t.name == 'tag')

    def test_changing_empty_tag_adds_tag(self):
        name = 'sometag'
        self.tags.add(Tag('tag'))
        self.tags.execute(ChangeTag(self.tags.empty_tag(), name))
        self._tag_with_name_exists(name)

    def test_changing_tag_to_empty_removes_tag(self):
        tag = Tag('tag')
        self.tags.add(tag)
        self.tags.execute(ChangeTag(tag, ''))
        self._verify_number_of_tags(1)
        self._tag_with_name_does_not_exists('tag')
        self._tag_with_name_exists('')

    def test_removing_one_tag_when_multiple_with_same_name(self):
        name = 'tag'
        tag = Tag(name)
        tag2 = Tag(name)
        self.tags.add(tag)
        self.tags.add(tag2)
        self.tags.execute(ChangeTag(tag, ''))
        self._verify_number_of_tags(1)
        self._tag_with_name_exists(tag2.name)

    def test_changing_partial_tag(self):
        self.tags.add(Tag('tag'))
        partial = Tag('ag')
        self.tags.add(partial)
        self.tags.execute(ChangeTag(partial, 'foo'))
        self._tag_with_name_exists('foo')
        self._tag_with_name_exists('tag')
        self._tag_with_name_does_not_exists('ag')

    def test_changing_tags_does_not_change_total_number_of_tags(self):
        tag_to_change = Tag('tagistano')
        self.tags.add(tag_to_change)
        self._test.datafile_controller.force_tags.add(ForcedTag('suite'))
        self._test.datafile_controller.parent.force_tags.add(ForcedTag('directory'))
        self._verify_number_of_tags(3)
        self._test.tags.execute(ChangeTag(tag_to_change, 'foobar'))
        self._verify_number_of_tags(3)

    def _verify_number_of_tags(self, number):
        assert number == sum(1 for _ in self.tags)

    def _tag_with_name_exists(self, name):
        assert any(t for t in self.tags if t.name == name)

    def _tag_with_name_does_not_exists(self, name):
        assert not any(t for t in self.tags if t.name == name)


if __name__ == "__main__":
    unittest.main()
