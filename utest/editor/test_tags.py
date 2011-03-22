import unittest
from robotide.editor.tags import TagsDisplay
from controller.controller_creator import testcase_controller as tc
from robot.utils.asserts import assert_equals, assert_true
from robotide.controller.tags import Tag

class _PartialTagsDisplay(TagsDisplay):

    def __init__(self, controller):
        self._tag_boxes = []
        self._controller = controller

    def add_tag(self, tag, editable):
        self._tag_boxes += [_TagInfo(tag, editable)]

    def build(self):
        pass

class _TagInfo(object):

    def __init__(self, tag, editable):
        self.set_tag(tag)
        self.SetEditable(editable)

    @property
    def editable(self):
        return self._editable

    @property
    def value(self):
        return self._tag.name

    def GetValue(self):
        return self.value

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

    def test_set_empty_value(self):
        self._tags_display.set_value(self._cntrl.tags)
        assert_equals(len(self._tags_display._tag_boxes), 1)
        self._is_empty(self._tags_display._tag_boxes[0])

    def test_set_none_empty_value(self):
        t = Tag('moro')
        self._cntrl.tags.add(t)
        self._tags_display.set_value(self._cntrl.tags)
        assert_equals(len(self._tags_display._tag_boxes), 2)
        assert_equals(self._tags_display._tag_boxes[0]._tag, t)
        self._is_empty(self._tags_display._tag_boxes[1])

    def test_remove_only_tag(self):
        self.test_set_none_empty_value()
        self._cntrl.tags.clear()
        self._tags_display._tag_boxes[0].set_tag(self._cntrl.tags.empty_tag())
        self._tags_display.clear()
        assert_equals(len(self._tags_display._tag_boxes), 1)
        self._is_empty(self._tags_display._tag_boxes[0])

    def _is_empty(self, tag_info):
        assert_true(tag_info.editable)
        assert_equals(tag_info.value, '')