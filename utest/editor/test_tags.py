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

import sys
import os
import pathlib
import unittest

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
SCRIPT_DIR = os.path.dirname(pathlib.Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)

from robotide.editor.tags import TagsDisplay
from controller.controller_creator import _testcase_controller as tc
from robotide.controller.tags import Tag


class _PartialTagsDisplay(TagsDisplay):

    def __init__(self, controller):
        self._tag_boxes = []
        self._controller = controller

    def add_tag(self, tag):
        self._tag_boxes += [_TagInfo(tag, True)]

    def build(self):
        pass


class _TagInfo(object):

    add_new = False

    def __init__(self, tag, editable):
        self.set_tag(tag)
        self.SetEditable(editable)

    @property
    def enabled(self):
        return self._editable

    @property
    def value(self):
        return self._tag.name

    def GetValue(self):
        if self._tag.is_empty(): return ''
        return self.value

    def is_empty(self):
        return self._tag.is_empty()

    def set_tag(self, tag):
        self._tag = tag

    def SetEditable(self, editable):
        self._editable = editable

    def Destroy(self):
        pass


class TestTagsModifications(unittest.TestCase):

    def setUp(self):
        self._cntrl = tc()
        self._tags_display = _PartialTagsDisplay(self._cntrl.tags)

    @property
    def tagboxes(self):
        return self._tags_display._tag_boxes

    def test_set_empty_value(self):
        self._tags_display.set_value(self._cntrl.tags)
        assert len(self.tagboxes) == 0

    def test_set_non_empty_value(self):
        tag = Tag('moro')
        self._cntrl.tags.add(tag)
        self._tags_display.set_value(self._cntrl.tags)
        assert len(self.tagboxes) == 1
        assert self.tagboxes[0]._tag == tag

    def test_remove_only_tag(self):
        self.test_set_non_empty_value()
        self._cntrl.tags.clear()
        self._tags_display.clear_field()
        assert len(self.tagboxes) == 0


if __name__ == '__main__':
    unittest.main()
