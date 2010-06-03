import unittest
from robot.parsing import TestCaseFile
from robot.parsing.settings import Fixture, Documentation, Timeout, Tags

from robot.utils.asserts import assert_equals, assert_true, assert_false
from robot.parsing.model import TestDataDirectory, TestCase, UserKeyword
from robotide.controller.settingcontroller import *
from robotide.controller.filecontroller import (TestCaseFileController,
        TestDataDirectoryController, TestCaseController, UserKeywordController)


class _FakeParent(object):
    def __init__(self):
        self.dirty = False
    def mark_dirty(self):
        self.dirty = True


class DocumentationControllerTest(unittest.TestCase):

    def setUp(self):
        self.doc = Documentation()
        self.doc.value = 'Initial doc'
        self.parent = _FakeParent()
        self.ctrl = DocumentationController(self.parent, self.doc)

    def test_creation(self):
        assert_equals(self.ctrl.value, 'Initial doc')
        assert_true(self.ctrl.datafile is None)

    def test_setting_value(self):
        self.ctrl.set_value('Doc changed')
        assert_equals(self.doc.value, 'Doc changed')
        self.ctrl.set_value('Doc changed | again')
        assert_equals(self.doc.value, 'Doc changed | again')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.doc.value, '')
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('Initial doc')
        assert_false(self.ctrl.dirty)


class FixtureControllerTest(unittest.TestCase):

    def setUp(self):
        self.fix = Fixture()
        self.fix.name = 'My Setup'
        self.fix.args = ['argh', 'urgh']
        self.parent = _FakeParent()
        self.ctrl = FixtureController(self.parent, self.fix, 'Suite Setup')

    def test_creation(self):
        assert_equals(self.ctrl.value, 'My Setup | argh | urgh')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(FixtureController(self.parent, Fixture(), '').value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('Blaa')
        assert_equals(self.fix.name, 'Blaa')
        assert_equals(self.fix.args, [])
        self.ctrl.set_value('Blaa | a')
        assert_equals(self.fix.name, 'Blaa')
        assert_equals(self.fix.args, ['a'])

    def test_whitespace_is_ignored_in_value(self):
        self.ctrl.set_value('Name |   a    |    b      |     c')
        assert_equals(self.fix.name, 'Name')
        assert_equals(self.fix.args, ['a', 'b', 'c'])
        assert_equals(self.ctrl.value, 'Name | a | b | c')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.fix.name, '')
        assert_equals(self.fix.args, [])
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('My Setup | argh | urgh')
        assert_false(self.ctrl.dirty)


class TagsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tags = Tags()
        self.tags.value = ['f1', 'f2']
        self.parent = _FakeParent()
        self.ctrl = TagsController(self.parent, self.tags, 'Force Tags')

    def test_creation(self):
        assert_equals(self.ctrl.value, 'f1 | f2')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(TagsController(self.parent, Tags(), '').value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('Blaa')
        assert_equals(self.tags.value, ['Blaa'])
        self.ctrl.set_value('a1 | a2 | a3')
        assert_equals(self.tags.value, ['a1', 'a2', 'a3'])

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('Blaa')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.tags.value, [])
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('f1 | f2')
        assert_false(self.ctrl.dirty)


class TimeoutControllerTest(unittest.TestCase):

    def setUp(self):
        self.to = Timeout()
        self.to.value = '1 s'
        self.to.message = 'message'
        self.parent = _FakeParent()
        self.ctrl = TimeoutController(self.parent, self.to, 'Suite Setup')

    def test_creation(self):
        assert_equals(self.ctrl.value, '1 s | message')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_timeout(self):
        assert_equals(TimeoutController(self.parent, Timeout(), '').value, '')

    def test_setting_value_changes_fixture_state(self):
        self.ctrl.set_value('3 s')
        assert_equals(self.to.value, '3 s')
        assert_equals(self.to.message, '')
        self.ctrl.set_value('3 s | new message')
        assert_equals(self.to.value, '3 s')
        assert_equals(self.to.message, 'new message')

    def test_setting_value_informs_parent_controller_about_dirty_model(self):
        self.ctrl.set_value('1 min')
        assert_true(self.ctrl.dirty)

    def test_set_empty_value(self):
        self.ctrl.set_value('')
        assert_equals(self.to.value, '')
        assert_equals(self.to.message, '')
        assert_true(self.ctrl.dirty)

    def test_same_value(self):
        self.ctrl.set_value('1 s | message')
        assert_false(self.ctrl.dirty)


class TestCaseFileControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestCaseFileController(TestCaseFile())
        for st in ctrl.settings:
            assert_true(st is not None)


class TestDataDirectoryControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        for st in ctrl.settings:
            assert_true(st is not None)


class TestCaseControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestCaseController(TestCase(parent=None, name='Test'))
        for st in ctrl.settings:
            assert_true(st is not None)


class UserKeywordControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = UserKeywordController(UserKeyword(parent=None, name='UK'))
        for st in ctrl.settings:
            assert_true(st is not None)

