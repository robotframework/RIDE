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

import unittest

from nose.tools import assert_equal, assert_raises

from robotide.application.editorprovider import EditorProvider


class TestObject(object): pass
class TestEditor(object): pass
class TestEditor2(object): pass


class TestEditorProvide(unittest.TestCase):

    def setUp(self):
        self.p = EditorProvider()
        self.p.register_editor(TestObject, TestEditor)

    def test_registering(self):
        assert_equal(self.p.get_editor(TestObject), TestEditor)
        self.p.register_editor(TestObject, TestEditor2)
        assert_equal(self.p.get_editor(TestObject), TestEditor2)

    def test_setting_deafult_editor(self):
        self.p.register_editor(TestObject, TestEditor2, default=False)
        assert_equal(self.p.get_editor(TestObject), TestEditor)

    def test_getting_when_none_registered(self):
        self.p.unregister_editor(TestObject, TestEditor)
        assert_raises(IndexError, self.p.get_editor, TestObject)

    def test_unregistering(self):
        self.p.register_editor(TestObject, TestEditor2)
        self.p.unregister_editor(TestObject, TestEditor2)
        assert_equal(self.p.get_editor(TestObject), TestEditor)

    def test_get_editors(self):
        self.p.register_editor(TestObject, TestEditor2)
        assert_equal(self.p.get_editors(TestObject), [TestEditor, TestEditor2])

    def test_registering_twice_does_nothing(self):
        self.p.register_editor(TestObject, TestEditor)
        assert_equal(self.p.get_editors(TestObject), [TestEditor])

    def test_activating(self):
        self.p.register_editor(TestObject, TestEditor2, default=False)
        self.p.set_active_editor(TestObject, TestEditor2)
        assert_equal(self.p.get_editor(TestObject), TestEditor2)

