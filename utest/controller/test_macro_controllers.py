import unittest
from nose.tools import assert_equals, assert_true, assert_false

from robotide.robotapi import TestCaseFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.controller.macrocontrollers import (
    TestCaseController, UserKeywordController)
from robotide.controller.tablecontrollers import (
    TestCaseTableController, KeywordTableController)


class _BaseWithSteps(unittest.TestCase):

    def _test_copy_empty(self):
        for setting in self.ctrl.settings:
            assert_false(setting.is_set, 'not empty %s' % setting.__class__)
        new = self.ctrl.copy('new name')
        for setting in new.settings:
            assert_false(setting.is_set, 'not empty %s' % setting.__class__)

    def _test_copy_content(self):
        for setting in self.ctrl.settings:
            assert_false(setting.is_set, 'not empty %s' % setting.__class__)
            setting.set_value('boo')
            setting.set_comment(['hobo'])
        new = self.ctrl.copy('new name')
        for setting in new.settings:
            assert_true(setting.is_set, 'empty %s' % setting.__class__)
            assert_equals(setting.value, 'boo', 'not boo %s' % setting.__class__)
            assert_equals(setting.comment.as_list(), ['# hobo'], 'comment not copied %s' % setting.__class__)


class TestCaseControllerTest(_BaseWithSteps):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.testcase = self.tcf.testcase_table.add('Test')
        self.testcase.add_step(['Log', 'Hello'])
        self.testcase.add_step(['No Operation'])
        self.testcase.add_step(['Foo'])
        self.tcf.testcase_table.add('Another Test')
        tctablectrl = TestCaseTableController(TestCaseFileController(self.tcf),
                                              self.tcf.testcase_table)
        self.ctrl = TestCaseController(tctablectrl, self.testcase)

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_true(self.ctrl.datafile is self.tcf, self.ctrl.datafile)

    def test_rename(self):
        self.ctrl.rename('Foo Barness')
        assert_equals(self.ctrl.name, 'Foo Barness')
        assert_true(self.ctrl.dirty)

    def test_rename_strips_whitespace(self):
        self.ctrl.rename('\t  \n Foo Barness        ')
        assert_equals(self.ctrl.name, 'Foo Barness')
        assert_true(self.ctrl.dirty)

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()

    def test_add_tag(self):
        orig_num_tags = len(self.ctrl.tags.as_list())
        self.ctrl.add_tag('Some tag')
        assert_true(len(self.ctrl.tags.as_list()) == orig_num_tags + 1)


class UserKeywordControllerTest(_BaseWithSteps):

    def setUp(self):
        self.tcf = TestCaseFile()
        uk = self.tcf.keyword_table.add('UK')
        uk.add_step(['No Operation'])
        uk2 = self.tcf.keyword_table.add('UK 2')
        tablectrl = KeywordTableController(TestCaseFileController(self.tcf),
                                           self.tcf.keyword_table)
        self.ctrl = UserKeywordController(tablectrl, uk)
        self.ctrl2 = UserKeywordController(tablectrl, uk2)

    def test_keyword_settings(self):
        labels = [setting.label for setting in self.ctrl.settings]
        assert_true('Documentation' in labels)
        assert_true('Arguments' in labels)
        assert_true('Teardown' in labels)
        assert_true('Return Value' in labels)
        assert_true('Timeout' in labels)

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equals(self.ctrl.steps[0].keyword, 'No Operation')
        assert_true(self.ctrl.datafile is self.tcf)

    def test_dirty(self):
        self.ctrl.mark_dirty()
        assert_true(self.ctrl.dirty)

    def test_move_up(self):
        assert_false(self.ctrl.move_up())
        self._assert_uk_in(0, 'UK')
        assert_true(self.ctrl2.move_up())
        self._assert_uk_in(0, 'UK 2')

    def test_move_down(self):
        assert_false(self.ctrl2.move_down())
        self._assert_uk_in(1, 'UK 2')
        assert_true(self.ctrl.move_down())
        self._assert_uk_in(1, 'UK')

    def test_delete(self):
        self.ctrl.delete()
        assert_false('UK' in self.tcf.keyword_table.keywords)
        self._assert_uk_in(0, 'UK 2')

    def _assert_uk_in(self, index, name):
        assert_equals(self.tcf.keyword_table.keywords[index].name, name)

    def _assert_step(self, step, exp_assign=[], exp_keyword=None, exp_args=[]):
        assert_equals(step.assign, exp_assign)
        assert_equals(step.keyword, exp_keyword)
        assert_equals(step.args, exp_args)

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()
