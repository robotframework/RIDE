import unittest
from robot.parsing.settings import Fixture, Documentation, Timeout, Tags, Return

from robot.utils.asserts import assert_equals, assert_true, assert_false, assert_none
from robot.parsing.model import TestDataDirectory
from robotide.controller.settingcontroller import *
from robotide.controller.filecontroller import *
from robotide.controller.filecontroller import _WithListOperations
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
        assert_equals(self.ctrl.value, 'Initial doc')
        assert_true(self.ctrl.datafile is None)
        ctrl = DocumentationController(self.parent, Documentation('[Documentation]'))
        assert_equals(ctrl.label, 'Documentation')

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
        assert_equals(self.ctrl.value, 'My Setup | argh | urgh')
        assert_equals(self.ctrl.label, 'Suite Setup')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(FixtureController(self.parent, Fixture('Teardown')).value, '')

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
        self.tags = Tags('Force Tags')
        self.tags.value = ['f1', 'f2']
        self.parent = _FakeParent()
        self.ctrl = TagsController(self.parent, self.tags)

    def test_creation(self):
        assert_equals(self.ctrl.value, 'f1 | f2')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_fixture(self):
        assert_equals(TagsController(self.parent, Tags('Tags')).value, '')

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
        assert_equals(self.ctrl.value, '1 s | message')
        assert_true(self.ctrl.is_set)

    def test_value_with_empty_timeout(self):
        assert_equals(TimeoutController(self.parent, Timeout('Timeout')).value, '')

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
        ctrl = TestCaseFileController(TestCaseFile())
        for st in ctrl.settings:
            assert_true(st is not None)
        assert_false(ctrl.dirty)

    def test_has_format(self):
        ctrl = TestCaseFileController(TestCaseFile())
        assert_true(ctrl.has_format())
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_true(ctrl.has_format())

    def test_get_format(self):
        ctrl = TestCaseFileController(TestCaseFile())
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.get_format(), 'html')

    def test_set_format(self):
        ctrl = TestCaseFileController(TestCaseFile())
        ctrl.data.source = '/tmp/.path.with.dots/test.cases.html'
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.html')
        ctrl.set_format('txt')
        assert_equals(ctrl.source, '/tmp/.path.with.dots/test.cases.txt')


class TestDataDirectoryControllerTest(unittest.TestCase):

    def test_creation(self):
        ctrl = TestDataDirectoryController(TestDataDirectory())
        for st in ctrl.settings:
            assert_true(st is not None)

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


class TestCaseControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.testcase = self.tcf.testcase_table.add('Test')
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


class UserKeywordControllerTest(unittest.TestCase):

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


class ImportSettingsControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self.ctrl = ImportSettingsController(TestCaseFileController(self.tcf),
                                             self.tcf.setting_table)

    def test_addding_library(self):
        self.ctrl.add_library('MyLib | Some | argu | ments')
        self._assert_import('MyLib', ['Some', 'argu', 'ments'])

    def test_adding_resource(self):
        self.ctrl.add_resource('/a/path/to/file.txt')
        self._assert_import('/a/path/to/file.txt')

    def test_adding_variables(self):
        self.ctrl.add_variables('varfile.py | an arg')
        self._assert_import('varfile.py', ['an arg'])

    def _assert_import(self, exp_name, exp_args=None):
        imp = self.tcf.setting_table.imports[-1]
        assert_equals(imp.name, exp_name)
        if exp_args is not None:
            assert_equals(imp.args, exp_args)
        assert_true(self.ctrl.dirty)

    def test_creation(self):
        assert_true(self.ctrl._items is not None)


class VariablesControllerTest(unittest.TestCase):

    def setUp(self):
        self.tcf = TestCaseFile()
        self._add_var('${foo}', 'foo')
        self._add_var('${bar}', 'bar')
        self.ctrl = VariableTableController(TestCaseFileController(self.tcf),
                                            self.tcf.variable_table)

    def _add_var(self, name, value):
        self.tcf.variable_table.add(name, value)

    def test_adding_scalar(self):
        self.ctrl.add_variable('${blaa}', 'value')
        assert_true(self.ctrl.dirty)
        self._assert_var_in(2, '${blaa}')

    def test_creation(self):
        assert_true(self.ctrl._items is not None)

    def _assert_var_in(self, index, name):
        assert_equals(self.tcf.variable_table.variables[index].name, name)


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
                self.iteration_count+=1
                if controller.source and controller.source.endswith('test.txt'):
                    self.in_sub_dir = True
        check_count_and_sub_dir = Checker()
        [check_count_and_sub_dir(df) for df in self.directory_controller.iter_datafiles()]
        assert_true(check_count_and_sub_dir.iteration_count == 5)
        assert_true(check_count_and_sub_dir.in_sub_dir)


if __name__ == "__main__":
    unittest.main()
