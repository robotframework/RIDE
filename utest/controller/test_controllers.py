import unittest
from robot.parsing import TestCaseFile
from robot.parsing.settings import Fixture, Documentation

from robotide.model.controller import FixtureController, DocumentationController,\
    TestCaseFileController, TestDataDirectoryController, TestCaseController,\
    UserKeywordController
from robot.utils.asserts import assert_equals, assert_true, assert_false
from robot.parsing.model import TestDataDirectory, TestCase, UserKeyword


class _FakeParent(object):
    def __init__(self):
        self.dirty = False
    def mark_dirty(self):
        self.dirty = True


class TestDocumentationController(unittest.TestCase):

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


class TestFixtureController(unittest.TestCase):

    def setUp(self):
        self.fix = Fixture()
        self.fix.name = 'My Setup'
        self.fix.args = ['argh', 'urgh']
        self.parent = _FakeParent()
        self.ctrl = FixtureController(self.parent, self.fix, 'Suite Setup')

    def test_creation(self):
        assert_equals(self.ctrl.value, 'My Setup | argh | urgh')
        assert_true(self.ctrl.is_set)

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


class TestTestCaseFileController(unittest.TestCase):

    def test_creation(self):
        ctrl = TestCaseFileController(TestCaseFile())
        for st in ctrl.settings:
            assert_true(st is not None)


class TestTestDirectoryDataController(unittest.TestCase):

    def test_creation(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        for st in ctrl.settings:
            assert_true(st is not None)


class TestTestCaseController(unittest.TestCase):

    def test_creation(self):
        ctrl = TestCaseController(TestCase(parent=None, name='Test'))
        for st in ctrl.settings:
            assert_true(st is not None)


class TestUserKeywordController(unittest.TestCase):

    def test_creation(self):
        ctrl = UserKeywordController(UserKeyword(parent=None, name='UK'))
        for st in ctrl.settings:
            assert_true(st is not None)

