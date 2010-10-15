import unittest
from robot.parsing import TestCase
from robot.parsing.settings import Fixture, Documentation, Timeout, Tags, Return

from robot.utils.asserts import (assert_equals, assert_true, assert_false,
                                 assert_none, assert_raises_with_msg)
from robotide.controller.settingcontroller import *
from robotide.controller.filecontroller import *
from robotide.controller.tablecontrollers import _WithListOperations
from robotide.controller.tablecontrollers import *
from robotide.controller import NewDatafile
from resources import SUITEPATH


class _FakeParent(object):
    def __init__(self):
        self.dirty = False
        self.datafile = None
    def mark_dirty(self):
        self.dirty = True


class DocumentationControllerTest(unittest.TestCase):

    def setUp(self):
        self.doc = Documentation('Documentation')
        self.doc.value = 'Initial doc'
        self.parent = _FakeParent()
        self.ctrl = DocumentationController(self.parent, self.doc)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'Initial doc')
        assert_true(self.ctrl.datafile is None)
        ctrl = DocumentationController(self.parent, Documentation('[Documentation]'))
        assert_equals(ctrl.label, 'Documentation')

    def test_setting_value(self):
        self.ctrl.set_value('Doc changed')
        assert_equals(self.doc.value, 'Doc changed')
        self.ctrl.set_value('Doc changed | again')
        assert_equals(self.doc.value, 'Doc changed | again')

    def test_get_editable_value(self):
        self.doc.value = 'My doc \\n with enters \\\\\\r\\n and \\t tabs and escapes \\\\n \\\\\\\\r'
        assert_equals(self.ctrl.editable_value, 'My doc \n with enters \\\\\n'
                                                ' and \\t tabs and escapes \\\\n \\\\\\\\r')

    def test_set_editable_value(self):
        test_text = '''My doc
 with enters
 and \t tabs'''
        self.ctrl.editable_value = test_text
        assert_equals(self.doc.value, 'My doc\\n with enters\\n and \t tabs')
        assert_equals(self.ctrl.editable_value, test_text)

    def test_set_editable_value_should_escape_leading_hash(self):
        self.ctrl.editable_value = '# Not # Comment'
        assert_equals(self.doc.value, '\\# Not # Comment')
        assert_equals(self.ctrl.editable_value, '\\# Not # Comment')

    def test_get_visible_value(self):
        self.doc.value = 'My doc \\n with enters \\n and \t tabs'
        assert_equals(self.ctrl.visible_value, '''My doc <br />
with enters <br />
and &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; tabs''')

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

    def test_clear(self):
        self.ctrl.clear()
        assert_equals(self.doc.value, '')
        assert_true(self.ctrl.dirty)


class FixtureControllerTest(unittest.TestCase):

    def setUp(self):
        self.fix = Fixture('Suite Setup')
        self.fix.name = 'My Setup'
        self.fix.args = ['argh', 'urgh']
        self.parent = _FakeParent()
        self.ctrl = FixtureController(self.parent, self.fix)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'My Setup | argh | urgh')
        assert_equals(self.ctrl.label, 'Suite Setup')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(FixtureController(self.parent, Fixture('Teardown')).display_value, '')

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
        assert_equals(self.ctrl.display_value, 'Name | a | b | c')

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

    def test_setting_comment(self):
        self.ctrl.set_comment('My comment')
        assert_equals(self.ctrl.comment, 'My comment')
        assert_true(self.ctrl.dirty)


class TagsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tags = Tags('Force Tags')
        self.tags.value = ['f1', 'f2']
        self.parent = _FakeParent()
        self.ctrl = TagsController(self.parent, self.tags)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, 'f1 | f2')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(TagsController(self.parent, Tags('Tags')).display_value, '')

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
        self.to = Timeout('Timeout')
        self.to.value = '1 s'
        self.to.message = 'message'
        self.parent = _FakeParent()
        self.ctrl = TimeoutController(self.parent, self.to)

    def test_creation(self):
        assert_equals(self.ctrl.display_value, '1 s | message')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_timeout(self):
        assert_equals(TimeoutController(self.parent,
                                        Timeout('Timeout')).display_value, '')

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


class ReturnValueControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = ReturnValueController(_FakeParent(), Return('[Return]'))
        assert_equals(ctrl.label, 'Return Value')


class TestCaseFileControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = self._file_ctrl()
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(ctrl.settings), 9)
        assert_false(ctrl.dirty)

    def test_has_format(self):
        ctrl = self._file_ctrl()
        assert_true(ctrl.has_format())
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_true(ctrl.has_format())

    def test_get_format(self):
        ctrl = self._file_ctrl()
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.get_format(), 'html')

    def test_set_format(self):
        ctrl = self._file_ctrl()
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.html')
        ctrl.set_format('txt')
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.txt')

    def test_add_test_or_kw(self):
        ctrl = self._file_ctrl()
        assert_equals(len(ctrl.tests), 0)
        new_test = TestCaseController(ctrl, TestCase(TestCaseFile(), 'New test'))
        ctrl.add_test_or_keyword(new_test)
        assert_equals(len(ctrl.tests), 1)
        assert_true(ctrl.tests[0]._test.parent is ctrl.datafile)
        assert_true(ctrl.dirty)

    def test_new_test(self):
        test_ctrl = self._file_ctrl().new_test('Foo')
        assert_equals(test_ctrl.name, 'Foo')

    def test_new_keyword(self):
        kw_ctrl = self._file_ctrl().new_keyword('An UK')
        assert_equals(kw_ctrl.name, 'An UK')

    def test_new_keyword_with_args(self):
        kw_ctrl = self._file_ctrl().new_keyword('UK', '${a1} | ${a2}')
        assert_equals(kw_ctrl.name, 'UK')
        assert_equals(kw_ctrl.data.args.value, ['${a1}', '${a2}'])

    def _file_ctrl(self):
        return TestCaseFileController(TestCaseFile())


class TestDataDirectoryControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_equals(len(ctrl.settings), 6)

    def test_has_format(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        assert_false(ctrl.has_format())
        ctrl.mark_dirty()
        assert_false(ctrl.has_format())
        ctrl.data.initfile = '/tmp/__init__.html'
        assert_true(ctrl.has_format())

    def test_set_format(self):
        dir = TestDataDirectory()
        dir.source = '/tmp/'
        ctrl = TestDataDirectoryController(dir)
        assert_false(ctrl.has_format())
        ctrl.set_format('txt')
        assert_true(ctrl.has_format())
        assert_equals(ctrl.source, '/tmp/__init__.txt')

    def test_adding_new_child(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        assert_true(ctrl.new_datafile(NewDatafile('path/to/data.txt',
                                                  is_dir_type=False)))


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
            setting.set_comment('hobo')
        new = self.ctrl.copy('new name')
        for setting in new.settings:
            assert_true(setting.is_set, 'empty %s' % setting.__class__)
            assert_equals(setting.value, 'boo', 'not boo %s' % setting.__class__)
            assert_equals(setting.comment, 'hobo', 'comment not copied %s' % setting.__class__)

    def _test_uk_creation(self):
        observer = self._creation_oberver()
        num_keywords = len(self.tcf.keywords)
        self.ctrl.create_user_keyword('New UK', [], observer.observe)
        assert_true(isinstance(observer.item, UserKeywordController))
        self._check_argument_names(observer.item, 0)
        assert_equals(len(self.tcf.keywords), num_keywords + 1)

    def _test_creation_with_conflicting_name(self):
        self.tcf.keyword_table.add('Duplicate name')
        num_kws = len(self.tcf.keywords)
        assert_raises_with_msg(ValueError, 'User keyword with this name already exists.',
                               self.ctrl.create_user_keyword, 'Duplicate name',
                               [], self._creation_oberver().observe)
        assert_equals(len(self.tcf.keywords), num_kws)
        assert_false(self.ctrl.dirty)

    def _test_creation_with_arguments(self):
        observer = self._creation_oberver()
        self.ctrl.create_user_keyword('Uk w args', ['some', 'value'],
                                      observer.observe)
        kw_ctrl = observer.item
        self._check_argument_names(kw_ctrl, 2)

    def _creation_oberver(self):
        class CreationObserver(object):
            item = None
            def observe(self, controller):
                self.item = controller
        return CreationObserver()

    def _check_argument_names(self, kw_ctrl, num_args):
        for exp, act in zip(('${arg%s}' % i for i in range(1, num_args + 1)),
                            kw_ctrl.data.args.value):
            assert_equals(exp, act)


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

    def test_rename_validation(self):
        assert_false(self.ctrl.validate_name('This name is valid'))
        assert_none(self.ctrl.validate_name('Another test'))
        assert_equals(self.ctrl.validate_name('Test'),
                      'Test case with this name already exists.')

    def test_rename(self):
        self.ctrl.rename('Foo Barness')
        assert_equals(self.ctrl.name, 'Foo Barness')
        assert_true(self.ctrl.dirty)

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()

    def test_create_user_keyword(self):
        self._test_uk_creation()

    def test_creating_user_keyword_with_conflicting_name_does_nothing(self):
        self._test_creation_with_conflicting_name()

    def test_creation_with_arguments(self):
        self._test_creation_with_arguments()

    def test_extract_kw(self):
        obs = self._creation_oberver()
        self.ctrl.extract_keyword('New KW', '${argh}', (0,1), obs.observe)
        assert_equals(self.testcase.steps[0].keyword, 'New KW')
        assert_equals(len(self.testcase.steps), 2)

        assert_equals(obs.item.steps[0].keyword, 'Log')
        assert_equals(obs.item.steps[1].keyword, 'No Operation')
        assert_equals(obs.item.arguments.value, '${argh}')
        assert_true(self.ctrl.dirty)

    def test_extract_kw_from_the_middle(self):
        obs = self._creation_oberver()
        self.ctrl.extract_keyword('New KW', '', (1,1), obs.observe)
        assert_equals(self.testcase.steps[0].keyword, 'Log')
        assert_equals(self.testcase.steps[1].keyword, 'New KW')
        assert_equals(self.testcase.steps[2].keyword, 'Foo')
        assert_equals(len(self.testcase.steps), 3)
        assert_equals(obs.item.steps[0].keyword, 'No Operation')


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

    def test_creation(self):
        for st in self.ctrl.settings:
            assert_true(st is not None)
        assert_equals(self.ctrl.steps[0].keyword, 'No Operation')
        assert_true(self.ctrl.datafile is self.tcf)

    def test_dirty(self):
        self.ctrl.mark_dirty()
        assert_true(self.ctrl.dirty)

    def test_rename_validation(self):
        assert_false(self.ctrl.validate_name('This name is valid'))
        assert_true(self.ctrl.validate_name('UK'))
        assert_equals(self.ctrl.validate_name('UK 2'),
                      'User keyword with this name already exists.')

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

    def test_step_parsing(self):
        self.ctrl.parse_steps_from_rows([['Foo']])
        self._assert_step(self.ctrl.steps[0], exp_keyword='Foo')
        self.ctrl.parse_steps_from_rows([['${var}= ', 'Foo', 'args'],
                                         [': FOR', '${i}', 'In', '@{bar}'],
                                         ['', 'blaa']])
        self._assert_step(self.ctrl.steps[0], ['${var}='], 'Foo', ['args'])
        assert_equals(self.ctrl.steps[1].vars, ['${i}'])
        self._assert_step(self.ctrl.steps[1].steps[0], exp_keyword='blaa')

    def _assert_step(self, step, exp_assign=[], exp_keyword=None, exp_args=[]):
        assert_equals(step.assign, exp_assign)
        assert_equals(step.keyword, exp_keyword)
        assert_equals(step.args, exp_args)

    def test_copy_empty(self):
        self._test_copy_empty()

    def test_copy_content(self):
        self._test_copy_content()

    def test_create_user_keyword(self):
        self._test_uk_creation()

    def test_creating_user_keyword_with_conflicting_name_does_nothing(self):
        self._test_creation_with_conflicting_name()

    def test_creation_with_arguments(self):
        self._test_creation_with_arguments()


class ImportControllerTest(unittest.TestCase):
    class FakeParent(object):

        @property
        def directory(self):
            return 'tmp'

        def resource_import_modified(self, path):
            pass

    def setUp(self):
        self.tcf = TestCaseFile()
        self.tcf.setting_table.add_library('somelib', ['foo', 'bar'])
        self.tcf.setting_table.add_resource('resu')
        self.tcf.setting_table.add_library('BuiltIn', ['WITH NAME', 'InBuilt'])
        tcf_ctrl = TestCaseFileController(self.tcf, ImportControllerTest.FakeParent())
        tcf_ctrl.data.directory = 'tmp'
        self.parent = ImportSettingsController(tcf_ctrl, self.tcf.setting_table)

    def test_creation(self):
        self._assert_import(0, 'somelib', ['foo', 'bar'])
        self._assert_import(1, 'resu')
        self._assert_import(2, 'BuiltIn', exp_alias='InBuilt')

    def test_display_value(self):
        assert_equals(self.parent[0].display_value, 'foo | bar')
        assert_equals(self.parent[1].display_value, '')
        assert_equals(self.parent[2].display_value, 'WITH NAME | InBuilt')

    def test_editing(self):
        ctrl = ImportController(self.parent, self.parent[1]._import)
        ctrl.set_value('foo')
        self._assert_import(1, 'foo')
        assert_true(self.parent.dirty)

    def test_editing_with_args(self):
        ctrl = ImportController(self.parent, self.parent[0]._import)
        ctrl.set_value('bar', 'quux')
        self._assert_import(0, 'bar', ['quux'])
        assert_true(self.parent.dirty)
        ctrl.set_value('name', 'a1 | a2')
        self._assert_import(0, 'name', ['a1', 'a2'])

    def test_editing_with_alias(self):
        ctrl = ImportController(self.parent, self.parent[0]._import)
        ctrl.set_value('newname', '', 'namenew')
        self._assert_import(0, 'newname', exp_alias='namenew')
        ctrl.set_value('again')
        self._assert_import(0, 'again')

    def _assert_import(self, index, exp_name, exp_args=[], exp_alias=''):
        item = self.parent[index]
        assert_equals(item.name, exp_name)
        assert_equals(item.args, exp_args)
        assert_equals(item.alias, exp_alias)


class ImportSettingsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.ctrl = ImportSettingsController(TestCaseFileController(self.tcf),
                                             self.tcf.setting_table)

    def test_addding_library(self):
        self.ctrl.add_library('MyLib', 'Some | argu | ments', 'alias')
        self._assert_import('MyLib', ['Some', 'argu', 'ments'], 'alias')

    def test_adding_resource(self):
        self.ctrl.add_resource('/a/path/to/file.txt')
        self._assert_import('/a/path/to/file.txt')

    def test_adding_variables(self):
        self.ctrl.add_variables('varfile.py', 'an arg')
        self._assert_import('varfile.py', ['an arg'])

    def _assert_import(self, exp_name, exp_args=[], exp_alias=None):
        imp = self.tcf.setting_table.imports[-1]
        assert_equals(imp.name, exp_name)
        assert_equals(imp.args, exp_args)
        assert_true(self.ctrl.dirty)

    def test_creation(self):
        assert_true(self.ctrl._items is not None)


class VariablesControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self._add_var('${foo}', 'foo')
        self._add_var('@{bar}', ['b', 'a', 'r'])
        self.ctrl = VariableTableController(TestCaseFileController(self.tcf),
                                            self.tcf.variable_table)

    def _add_var(self, name, value):
        self.tcf.variable_table.add(name, value)

    def test_creation(self):
        assert_equals(self.ctrl[0].name, '${foo}')
        assert_equals(self.ctrl[1].name, '@{bar}')

    def test_adding_scalar(self):
        self.ctrl.add_variable('${blaa}', 'value')
        assert_true(self.ctrl.dirty)
        self._assert_var_in_model(2, '${blaa}', ['value'])

    def test_editing(self):
        self.ctrl[0].set_value('${blaa}', 'quux')
        self._assert_var_in_ctrl(0, '${blaa}', ['quux'])
        self.ctrl[1].set_value('@{listvar}', ['a', 'b', 'c'])
        self._assert_var_in_ctrl(1, '@{listvar}', ['a', 'b', 'c'])
        assert_true(self.ctrl.dirty)

    def _assert_var_in_ctrl(self, index, name, value):
        assert_equals(self.ctrl[index].name, name)
        assert_equals(self.ctrl[index].value, value)

    def _assert_var_in_model(self, index, name, value):
        assert_equals(self.tcf.variable_table.variables[index].name, name)
        assert_equals(self.tcf.variable_table.variables[index].value, value)


class MetadataListControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.tcf.setting_table.add_metadata('Meta name', 'Some value')
        self.ctrl = MetadataListController(TestCaseFileController(self.tcf),
                                           self.tcf.setting_table)

    def test_creation(self):
        self._assert_meta_in_ctrl(0, 'Meta name', 'Some value')

    def test_editing(self):
        self.ctrl[0].set_value('New name', 'another value')
        self._assert_meta_in_model(0, 'New name', 'another value')
        assert_true(self.ctrl[0].dirty)

    def _assert_meta_in_ctrl(self, index, name, value):
        assert_equals(self.ctrl[index].name, name)
        assert_equals(self.ctrl[index].value, value)

    def _assert_meta_in_model(self, index, name, value):
        assert_equals(self.tcf.setting_table.metadata[index].name, name)
        assert_equals(self.tcf.setting_table.metadata[index].value, value)


class FakeListController(_WithListOperations):

    def __init__(self):
        self._itemslist = ['foo', 'bar', 'quux']
        self.dirty = False

    @property
    def _items(self):
        return self._itemslist

    def mark_dirty(self):
        self.dirty = True


class WithListOperationsTest(unittest.TestCase):

    def setUp(self):
        self._list_operations = FakeListController()

    def test_swap(self):
        self._assert_item_in(0, 'foo')
        self._assert_item_in(1, 'bar')
        self._list_operations.swap(0, 1)
        assert_true(self._list_operations.dirty)
        self._assert_item_in(0, 'bar')
        self._assert_item_in(1, 'foo')

    def test_delete(self):
        self._list_operations.delete(0)
        self._assert_item_in(0, 'bar')

    def _assert_item_in(self, index, name):
        assert_equals(self._list_operations._items[index], name)


class DatafileIteratorTest(unittest.TestCase):

    def setUp(self):
        test_data_suite = TestDataDirectory(source=SUITEPATH)
        self.directory_controller = TestDataDirectoryController(test_data_suite)

    def test_iterate_all(self):
        class Checker(object):
            def __init__(self):
                self.iteration_count = 0
                self.in_sub_dir = False
            def __call__(self, controller):
                self.iteration_count += 1
                if controller.source and controller.source.endswith('test.txt'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df in self.directory_controller.iter_datafiles()]
        assert_true(check_count_and_sub_dir.iteration_count == 5)
        assert_true(check_count_and_sub_dir.in_sub_dir)


if __name__ == "__main__":
    unittest.main()
