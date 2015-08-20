import unittest
from nose.tools import assert_equals

from robotide.editor.tags import TagsDisplay
from controller.controller_creator import testcase_controller as tc
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
        assert_equals(len(self.tagboxes), 0)

    def test_set_non_empty_value(self):
        tag = Tag('moro')
        self._cntrl.tags.add(tag)
        self._tags_display.set_value(self._cntrl.tags)
        assert_equals(len(self.tagboxes), 1)
        assert_equals(self.tagboxes[0]._tag, tag)

    def test_remove_only_tag(self):
        self.test_set_non_empty_value()
        self._cntrl.tags.clear()
        self._tags_display.clear()
        assert_equals(len(self.tagboxes), 0)


if __name__ == '__main__':
    unittest.main()
