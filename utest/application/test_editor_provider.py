import unittest

from nose.tools import assert_equals, assert_raises

from robotide.application.editorprovider import EditorProvider


class TestObject(object): pass
class TestEditor(object): pass
class TestEditor2(object): pass


class TestEditorProvide(unittest.TestCase):

    def setUp(self):
        self.p = EditorProvider()
        self.p.register_editor(TestObject, TestEditor)

    def test_registering(self):
        assert_equals(self.p.get_editor(TestObject), TestEditor)
        self.p.register_editor(TestObject, TestEditor2)
        assert_equals(self.p.get_editor(TestObject), TestEditor2)

    def test_setting_deafult_editor(self):
        self.p.register_editor(TestObject, TestEditor2, default=False)
        assert_equals(self.p.get_editor(TestObject), TestEditor)

    def test_getting_when_none_registered(self):
        self.p.unregister_editor(TestObject, TestEditor)
        assert_raises(IndexError, self.p.get_editor, TestObject)

    def test_unregistering(self):
        self.p.register_editor(TestObject, TestEditor2)
        self.p.unregister_editor(TestObject, TestEditor2)
        assert_equals(self.p.get_editor(TestObject), TestEditor)

    def test_get_editors(self):
        self.p.register_editor(TestObject, TestEditor2)
        assert_equals(self.p.get_editors(TestObject), [TestEditor, TestEditor2])

    def test_registering_twice_does_nothing(self):
        self.p.register_editor(TestObject, TestEditor)
        assert_equals(self.p.get_editors(TestObject), [TestEditor])

    def test_activating(self):
        self.p.register_editor(TestObject, TestEditor2, default=False)
        self.p.set_active_editor(TestObject, TestEditor2)
        assert_equals(self.p.get_editor(TestObject), TestEditor2)

