import unittest
from nose.tools import assert_equal, assert_true, assert_false

from robotide.robotapi import TestCaseFile
from robotide.controller import Project
from robotide.controller.macrocontrollers import KEYWORD_NAME_FIELD
from robotide.controller.ctrlcommands import (
    Undo, FindOccurrences, FindVariableOccurrences, NullObserver,
    RenameKeywordOccurrences, ChangeCellValue)
from robotide.controller.filecontrollers import (
    TestCaseFileController, TestCaseTableController, TestCaseController)
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideItemStepsChanged,\
    RideItemSettingsChanged, RideItemNameChanged
from robotide.namespace.namespace import Namespace
from robotide.spec.librarymanager import LibraryManager
from robotide.usages.commands import FindUsages
from resources import FakeSettings
import datafilereader


STEP1_KEYWORD = 'Log'
STEP2_ARGUMENT = 'No Operation'
TEST1_NAME = 'Test'
UNUSED_KEYWORD_NAME = 'Foo'
USERKEYWORD1_NAME = 'User Keyword'
USERKEYWORD2_NAME = 'Juuser kei woord'
SETUP_KEYWORD = 'Setup Kw'
TEMPLATE_KEYWORD = 'Template Kw'
SUITE_SETUP_KEYWORD = 'Suite Setup Kw'
SUITE_TEST_SETUP_KEYWORD = 'Test Setup Kw'
SUITE_TEST_TEMPLATE_KEYWORD = 'Test Template Kw'
SUITE_NAME = 'Some Suite'
KEYWORD_IN_USERKEYWORD1 = 'Some Keyword'
EMBEDDED_ARGUMENTS_KEYWORD = "Pick '${fruit}' and '${action}' it"


def TestCaseControllerWithSteps(project=None, source='some_suite.txt'):
    tcf = TestCaseFile()
    tcf.source = source
    tcf.setting_table.suite_setup.name = 'Suite Setup Kw'
    tcf.setting_table.test_setup.name = SUITE_TEST_SETUP_KEYWORD
    tcf.setting_table.test_teardown.name = 'Test Teardown Kw'
    tcf.setting_table.suite_teardown.name = 'Suite Teardown Kw'
    tcf.setting_table.test_template.value = SUITE_TEST_TEMPLATE_KEYWORD
    testcase = _create_testcase(tcf)
    uk = tcf.keyword_table.add(USERKEYWORD1_NAME)
    uk.add_step([KEYWORD_IN_USERKEYWORD1])
    uk = tcf.keyword_table.add(USERKEYWORD2_NAME)
    uk.add_step(['No Operation'])
    uk = tcf.keyword_table.add(EMBEDDED_ARGUMENTS_KEYWORD)
    uk.add_step(['No Operation'])
    if project is None:
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        project = Project(Namespace(FakeSettings()),
                          library_manager=library_manager)
    tcf_ctrl = TestCaseFileController(tcf, project)
    project._controller = tcf_ctrl
    tctablectrl = TestCaseTableController(tcf_ctrl,
                                          tcf.testcase_table)
    return TestCaseController(tctablectrl, testcase), project._namespace


def _create_testcase(tcf):
    testcase = tcf.testcase_table.add(TEST1_NAME)
    for step in [[STEP1_KEYWORD, 'Hello'],
                 ['Run Keyword', STEP2_ARGUMENT],
                 [USERKEYWORD2_NAME],
                 ["Pick 'apple' and 'peel' it"]]:
        testcase.add_step(step)
    for_loop = testcase.add_for_loop([': FOR', '${i}', 'IN RANGE', '10'])
    for_loop.add_step(['Log', '${i}'])
    testcase.setup.name = SETUP_KEYWORD
    testcase.teardown.name = 'Teardown Kw'
    testcase.template.value = TEMPLATE_KEYWORD
    return testcase


def assert_occurrence(test_ctrl, kw_name, expected_source, expected_usage):
    occ = _first_occurrence(test_ctrl, kw_name)
    # print("DEBUG: assert_occurrence %s kw_name %s" % (repr(occ.location), kw_name))
    assert_equal(occ.location, expected_source,
                  'Occurrence not in the right place')
    assert_equal(occ.usage, expected_usage, 'Usage not in the right place')


def assert_variable_occurrence(occurrences, source, usage, count):
    times_found = 0
    for occ in occurrences:
        if occ.location == source and occ.usage == usage:
            times_found += 1
    assert_equal(times_found, count)


def check_for_variable_occurrences(test_ctrl, name, expected_occurrences):
    occurrences = list(test_ctrl.execute(FindVariableOccurrences(name)))
    processed_occurrences = 0
    for source, usage, count in expected_occurrences:
        assert_variable_occurrence(occurrences, source, usage, count)
        processed_occurrences += count
    assert_equal(processed_occurrences, len(occurrences))


def _first_occurrence(test_ctrl, kw_name):
    occurrences = test_ctrl.execute(FindOccurrences(kw_name))
    if not occurrences:
        raise AssertionError('No occurrences found for "%s"' % kw_name)
    return next(occurrences)
    # see https://stackoverflow.com/questions/21622193/
    # python-3-2-coroutine-attributeerror-generator-object-has-no-attribute-next


def _get_ctrl_by_name(self, name, datafiles):
    for file in datafiles:
        if file.name == name:
            return file
        for test in file.tests:
            if test.name == name:
                return test
        for kw in file.keywords:
            if kw.name == name:
                return kw
    return None


class TestFindOccurrencesWithFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project_ctrl = datafilereader.construct_project(
            datafilereader.SIMPLE_TEST_SUITE_PATH)
        cls.ts1 = datafilereader.get_ctrl_by_name('TestSuite1',
                                                  cls.project_ctrl.datafiles)
        cls.ts2 = datafilereader.get_ctrl_by_name('TestSuite2',
                                                  cls.project_ctrl.datafiles)
        cls.ts3 = datafilereader.get_ctrl_by_name('TestSuite3',
                                                  cls.project_ctrl.datafiles)
        cls.resu = datafilereader.get_ctrl_by_name(
            datafilereader.SIMPLE_TEST_SUITE_RESOURCE_NAME,
            cls.project_ctrl.datafiles)

    @classmethod
    def tearDownClass(cls):
        cls.project_ctrl.close()

    def test_finds_only_occurrences_with_same_source(self):
        self.assert_occurrences(self.ts1, 'My Keyword', 2)
        self.assert_occurrences(self.ts2, 'My Keyword', 3)
        self.assert_occurrences(self.resu, 'My Keyword', 3)

    def test_first_occurrences_are_from_the_same_file(self):
        occ = self.resu.execute(FindOccurrences('My Keyword'))
        # see https://stackoverflow.com/questions/21622193/
        # python-3-2-coroutine-attributeerror-generator-object-has-no-attribute-next
        assert_true(self.resu.filename.endswith(occ.__next__().item.parent.source))
        assert_equal(occ.__next__().source, self.ts2.source)
        assert_equal(occ.__next__().source, self.ts2.source)

    def test_finds_occurrences_that_are_unrecognized(self):
        self.assert_occurrences(self.ts1, 'None Keyword', 2)
        self.assert_occurrences(self.ts2, 'None Keyword', 4)

    def test_finds_occurrences_that_override_builtin(self):
        self.assert_occurrences(self.ts1, 'Log', 1)
        self.assert_occurrences(self.ts2, 'Log', 2)

    # TODO This test fails in Python 3 because of order or returned item
    @unittest.skip("Sometimes FAILS with Python 3")
    def test_ignores_definition_in_base_resource(self):
        self.assert_occurrences(self.resu, 'Keyword In Both Resources', 1)
        occ = _first_occurrence(self.resu, 'Keyword In Both Resources')
        assert_equal(occ.item.parent.source, 'inner_resource.txt')

    def test_rename_resu_occurrence_in_case_of_double_definition(self):
        old_name = 'Keyword In Both Resources'
        new_name = 'FiiFaa'
        for kw in [k for k in self.resu.keywords if k.name == old_name]:
            self.resu.execute(RenameKeywordOccurrences(kw.name, new_name,
                                                       NullObserver(),
                                                       kw.info))
            assert_equal(kw.name, new_name)

    def test_rename_embedded_arguments_keyword_but_dont_rename_occurrences(
            self):
        old_name = 'embedded ${args} keyword'
        new_name = 'unembedded keyword'
        self.assert_occurrences(self.ts3, old_name, 2)
        self.assert_occurrences(self.ts3, new_name, 0)
        self.ts3.execute(RenameKeywordOccurrences(old_name, new_name,
                                                  NullObserver()))
        self.assert_occurrences(self.ts3, old_name, 1)
        self.assert_occurrences(self.ts3, new_name, 1)

    def test_rename_embedded_arguments_keyword_with_another_embedded_arguments_keyword(self):
        old_name = '2nd embedded ${args} keyword'
        new_name = '2nd embedded args keyword with ${trailing args}'
        self.assert_occurrences(self.ts3, old_name, 2)
        self.assert_occurrences(self.ts3, new_name, 0)
        self.ts3.execute(RenameKeywordOccurrences(old_name, new_name,
                                                  NullObserver()))
        self.assert_occurrences(self.ts3, old_name, 1)
        self.assert_occurrences(self.ts3, new_name, 1)

    def test_finding_from_test_setup_with_run_keyword(self):
        self._assert_usage('Test Setup Keyword', 'Setup')

    def test_finding_from_suite_setup_with_run_keyword(self):
        self._assert_usage('Suite Setup Keyword', 'Suite Setup')

    def test_finding_from_test_teardown_with_run_keyword(self):
        self._assert_usage('Test Teardown Keyword', 'Teardown')

    def test_finding_from_keyword_teardown(self):
        self._assert_usage('Keyword Teardown Keyword', 'Teardown')

    def test_finding_from_test_teardown_in_settings(self):
        self._assert_usage('Test Teardown in Setting', 'Test Teardown')

    def test_occurrences_in_suite_documentation_should_not_be_found(self):
        self._assert_no_usages('suitedocmatch')

    def test_occurrences_in_test_documentation_should_not_be_found(self):
        self._assert_no_usages('testdocmatch')

    def test_occurrences_in_keyword_documentation_should_not_be_found(self):
        self._assert_no_usages('keyworddocmatch')

    def _assert_usage(self, keyword, usage):
        occ = list(self.ts2.execute(FindUsages(keyword)))
        self.assertEqual(len(occ), 1)
        self.assertEqual(occ[0].usage, usage)

    def _assert_no_usages(self, keyword):
        self.assertEqual(list(self.ts2.execute(FindUsages(keyword))), [])

    def assert_occurrences(self, ctrl, kw_name, count):
        assert_equal(sum(1 for _ in ctrl.execute(FindOccurrences(kw_name))),
                     count)


class FindOccurrencesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_ctrl, cls.namespace = TestCaseControllerWithSteps()

    def test_no_occurrences(self):
        find_occurrences = FindOccurrences('Keyword Name')
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equal([i for i in occurrences], [])

    def test_occurrences_in_steps(self):
        assert_occurrence(self.test_ctrl, STEP1_KEYWORD, TEST1_NAME, 'Steps')

    def test_occurrences_in_step_arguments(self):
        assert_occurrence(self.test_ctrl, STEP2_ARGUMENT, TEST1_NAME, 'Steps')

    def test_occurrences_are_case_and_space_insensitive(self):
        assert_occurrence(self.test_ctrl, 'R un KE Y W O rd', TEST1_NAME,
                          'Steps')
        assert_occurrence(self.test_ctrl, 'se tu p KW  ', TEST1_NAME, 'Setup')

    def test_embedded_arguments_occurrence(self):
        assert_occurrence(self.test_ctrl, EMBEDDED_ARGUMENTS_KEYWORD,
                          TEST1_NAME, 'Steps')

    def test_unknown_variable_occurrences(self):
        self.assertEqual(list(self.test_ctrl.execute(FindOccurrences(
            '${some unknown variable}'))), [])

    def test_occurrences_in_test_metadata(self):
        assert_occurrence(self.test_ctrl, SETUP_KEYWORD,
                          TEST1_NAME, 'Setup')
        assert_occurrence(self.test_ctrl, 'Teardown Kw',
                          TEST1_NAME, 'Teardown')
        assert_occurrence(self.test_ctrl, TEMPLATE_KEYWORD,
                          TEST1_NAME, 'Template')

    def test_occurrences_in_suite_metadata(self):
        assert_occurrence(self.test_ctrl, SUITE_SETUP_KEYWORD,
                          SUITE_NAME, 'Suite Setup')
        assert_occurrence(self.test_ctrl, 'Test Setup Kw',
                          SUITE_NAME, 'Test Setup')
        assert_occurrence(self.test_ctrl, 'Test Teardown Kw',
                          SUITE_NAME, 'Test Teardown')
        assert_occurrence(self.test_ctrl, 'Suite Teardown Kw',
                          SUITE_NAME, 'Suite Teardown')
        assert_occurrence(self.test_ctrl, 'Test Template Kw',
                          SUITE_NAME, 'Test Template')

    def test_occurrences_in_user_keywords(self):
        assert_occurrence(self.test_ctrl, KEYWORD_IN_USERKEYWORD1,
                          USERKEYWORD1_NAME, 'Steps')
    """
    # TODO This test fails in Python 3 because can't find User Keyword
    # only fails with invoke, not with test_all.sh
    def test_occurrence_in_user_keyword_name(self):
        assert_occurrence(self.test_ctrl, USERKEYWORD1_NAME,
                          USERKEYWORD1_NAME, KEYWORD_NAME_FIELD)
    """

class FindVariableOccurrencesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        project = datafilereader.construct_project(
            datafilereader.FINDWHEREUSED_VARIABLES_PATH)
        cls._suite1 = _get_ctrl_by_name(cls, "Suite 1", project.datafiles)
        cls._suite2 = _get_ctrl_by_name(cls, "Suite 2", project.datafiles)
        cls._resource1 = _get_ctrl_by_name(cls, "Res1", project.datafiles)
        cls._case1 = _get_ctrl_by_name(cls, "Case 1", project.datafiles)
        cls._case2 = _get_ctrl_by_name(cls, "Case 2", project.datafiles)
        cls._case3 = _get_ctrl_by_name(cls, "Case 3", project.datafiles)
        cls._case4 = _get_ctrl_by_name(cls, "Case 4", project.datafiles)
        cls._case5 = _get_ctrl_by_name(cls, "Case 5", project.datafiles)
        cls._case6 = _get_ctrl_by_name(cls, "Case 6", project.datafiles)
        cls._kw1 = _get_ctrl_by_name(cls, "User KW 1", project.datafiles)
        cls._kw2 = _get_ctrl_by_name(cls, "User KW 2", project.datafiles)

    def test_occurrences_local_variable(self):
        check_for_variable_occurrences(self._case2, "${log}",
                                       ((self._case2.name, 'Steps', 2),
                                        (self._case2.name, 'Documentation',
                                         1)))

        check_for_variable_occurrences(self._kw2, "${arg1}",
                                       ((self._kw2.name, 'Arguments', 1),
                                        (self._kw2.name, 'Documentation', 1),
                                        (self._kw2.name, 'Steps', 1)))

        check_for_variable_occurrences(
            self._kw2, "@{arg2}", ((self._kw2.name, 'Arguments', 1),
                                   (self._kw2.name, 'Teardown', 1),
                                   (self._kw2.name, 'Steps', 1)))

    def test_occurrences_file_variable(self):
        check_for_variable_occurrences(self._case1, "${fileVar}",
                                       ((self._case2.name, 'Teardown', 1),
                                        (self._case1.name, 'Setup', 1),
                                        (self._case3.name, 'Steps', 1),
                                        (self._suite1.name, 'Variable Table',
                                         1)))

        check_for_variable_occurrences(
            self._kw2, "${resVar}",
            ((self._resource1.name, 'Variable Table', 1), (self._kw2.name,
                                                           'Steps', 1),
             (self._kw1.name, 'Teardown', 1),
             (self._case5.name, 'Steps', 1),
             (self._case5.name, 'Documentation', 1)))

    def test_occurrences_imported_variable(self):
        check_for_variable_occurrences(
            self._case5, "${resVar}",
            ((self._resource1.name, 'Variable Table', 1),
             (self._kw2.name, 'Steps', 1),
             (self._kw1.name, 'Teardown', 1),
             (self._case5.name, 'Steps', 1),
             (self._case5.name, 'Documentation', 1)))

    def test_occurrences_external_file_variable(self):
        check_for_variable_occurrences(
            self._case2, "${ServerHost}", ((self._case1.name, 'Steps', 1),
                                           (self._case2.name, 'Steps', 1),
                                           (self._case5.name, 'Steps', 1)))

        check_for_variable_occurrences(
            self._case5, "${ServerHost}", ((self._case1.name, 'Steps', 1),
                                           (self._case2.name, 'Steps', 1),
                                           (self._case5.name, 'Steps', 1)))

        check_for_variable_occurrences(
            self._case1, "${ServerPort}", ((self._case1.name, 'Steps', 1),
                                           (self._kw1.name, 'Steps', 1)))

    def test_occurrences_builtin_variable(self):
        check_for_variable_occurrences(self._kw1,
                                       "${True}",
                                       ((self._case4.name, 'Steps', 1),
                                        (self._case6.name, 'Setup', 1),
                                        (self._case6.name, 'Steps', 1),
                                        (self._kw1.name, 'Steps', 1)))

        check_for_variable_occurrences(
            self._case6, "${False}", ((self._case6.name, 'Documentation', 1),
                                      (self._case1.name, 'Steps', 1),
                                      (self._kw1.name, 'Steps', 1)))

        check_for_variable_occurrences(
            self._case3, "${EMPTY}",
            ((self._resource1.name, 'Variable Table', 1),
             (self._case3.name, 'Steps', 1)))


class RenameOccurrenceTest(unittest.TestCase):

    def setUp(self):
        self.test_ctrl, self.namespace = TestCaseControllerWithSteps()
        self._steps_have_changed = False
        self._testcase_settings_have_changed = False
        self._name_has_changed = False
        self._listeners_and_topics = [(self._steps_changed,
                                       RideItemStepsChanged),
                                      (self._testcase_settings_changed,
                                       RideItemSettingsChanged),
                                      (self._name_changed,
                                       RideItemNameChanged)]
        for listener, topic in self._listeners_and_topics:
            PUBLISHER.subscribe(listener, topic)

    def tearDown(self):
        for listener, topic in self._listeners_and_topics:
            PUBLISHER.unsubscribe(listener, topic)

    def _steps_changed(self, test):
        self._steps_have_changed = True

    def _testcase_settings_changed(self, message):
        if self.test_ctrl == message.item:
            self._testcase_settings_have_changed = True

    def _name_changed(self, data):
        self._name_has_changed = True

    def _expected_messages(self, steps_have_changed=False,
                           testcase_settings_have_changed=False,
                           name_has_changed=False):
        assert_equal(self._steps_have_changed, steps_have_changed)
        assert_equal(self._testcase_settings_have_changed,
                      testcase_settings_have_changed)
        assert_equal(self._name_has_changed, name_has_changed)

    def _rename(self, original_name, new_name, source, usage):
        self.test_ctrl.execute(RenameKeywordOccurrences(original_name,
                                                        new_name,
                                                        NullObserver()))
        assert_occurrence(self.test_ctrl, new_name, source, usage)

    def test_rename_updates_namespace(self):
        assert_true(self.namespace.is_user_keyword(self.test_ctrl.datafile,
                                                   USERKEYWORD2_NAME))
        assert_false(self.namespace.is_user_keyword(self.test_ctrl.datafile,
                                                    UNUSED_KEYWORD_NAME))
        self._rename(USERKEYWORD2_NAME, UNUSED_KEYWORD_NAME, TEST1_NAME,
                     'Steps')
        assert_true(self.namespace.is_user_keyword(self.test_ctrl.datafile,
                                                   UNUSED_KEYWORD_NAME))
        assert_false(self.namespace.is_user_keyword(self.test_ctrl.datafile,
                                                    USERKEYWORD2_NAME))

    def test_notifies_only_after_transaction_complete(self):
        datas_ok = {'steps': False, 'name': False}

        def name_changed_check_that_steps_have_also(data):
            datas_ok['steps'] = \
                self.test_ctrl.step(2).keyword == UNUSED_KEYWORD_NAME

        def steps_changed_check_that_name_has_also(data):
            datas_ok['name'] = any(True for i in
                                   self.test_ctrl.datafile_controller.keywords
                                   if i.name == UNUSED_KEYWORD_NAME)
        PUBLISHER.subscribe(name_changed_check_that_steps_have_also,
                            RideItemNameChanged)
        PUBLISHER.subscribe(steps_changed_check_that_name_has_also,
                            RideItemStepsChanged)
        try:
            self._rename(USERKEYWORD2_NAME, UNUSED_KEYWORD_NAME, TEST1_NAME,
                         'Steps')
        finally:
            PUBLISHER.unsubscribe(name_changed_check_that_steps_have_also,
                                  RideItemNameChanged)
            PUBLISHER.unsubscribe(steps_changed_check_that_name_has_also,
                                  RideItemStepsChanged)
        assert_true(datas_ok['steps'])
        assert_true(datas_ok['name'])

    def test_rename_in_steps(self):
        self._rename(STEP1_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)

    def test_rename_with_dollar_sign(self):
        self._rename(STEP1_KEYWORD, UNUSED_KEYWORD_NAME+'$', TEST1_NAME,
                     'Steps')
        self._expected_messages(steps_have_changed=True)

    def test_undo_rename_in_step(self):
        self._rename(STEP1_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self.test_ctrl.execute(Undo())
        assert_equal(self.test_ctrl.steps[0].keyword, STEP1_KEYWORD)

    def test_undo_after_renaming_to_something_that_is_already_there(self):
        self._rename(STEP1_KEYWORD, STEP2_ARGUMENT, TEST1_NAME, 'Steps')
        self.test_ctrl.execute(Undo())
        assert_equal(self.test_ctrl.steps[1].args[0], STEP2_ARGUMENT)

    def test_rename_steps_argument(self):
        self._rename(STEP2_ARGUMENT, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        assert_equal(self.test_ctrl.steps[1].as_list(), ['Run Keyword',
                                                          UNUSED_KEYWORD_NAME])

    """
    # TODO This test fails in Python 3 because can't find User Keyword
    # only fails with invoke, not with test_all.sh
    def test_user_keyword_rename(self):
        self._rename(USERKEYWORD1_NAME, UNUSED_KEYWORD_NAME,
                     UNUSED_KEYWORD_NAME, KEYWORD_NAME_FIELD)
        self._expected_messages(name_has_changed=True)
    """

    def test_rename_in_test_setup(self):
        self._rename(SETUP_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Setup')
        self._expected_messages(testcase_settings_have_changed=True)
        self.assertTrue(self.test_ctrl.dirty)

    def test_rename_in_test_template(self):
        self._rename(TEMPLATE_KEYWORD, UNUSED_KEYWORD_NAME,
                     TEST1_NAME, 'Template')
        self._expected_messages(testcase_settings_have_changed=True)
        self.assertTrue(self.test_ctrl.dirty)

    def test_rename_in_suite_metadata(self):
        self._rename(SUITE_SETUP_KEYWORD, UNUSED_KEYWORD_NAME, SUITE_NAME,
                     'Suite Setup')
        self._expected_messages()
        self.assertTrue(self.test_ctrl.dirty)

    def test_rename_in_suite_test_setup(self):
        self._rename(SUITE_TEST_SETUP_KEYWORD, UNUSED_KEYWORD_NAME, SUITE_NAME,
                     'Test Setup')
        self._expected_messages()
        self.assertTrue(self.test_ctrl.dirty)

    def test_rename_in_suite_test_template(self):
        self._rename(SUITE_TEST_TEMPLATE_KEYWORD, UNUSED_KEYWORD_NAME,
                     SUITE_NAME, 'Test Template')
        self._expected_messages()
        self.assertTrue(self.test_ctrl.dirty)

    def test_rename_in_user_keywords(self):
        self._rename(KEYWORD_IN_USERKEYWORD1, UNUSED_KEYWORD_NAME,
                     USERKEYWORD1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)

    def test_rename_given_prefixed_keywords(self):
        kw = 'BLOdkajasdj'
        self._add_step('Given '+kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          'Given '+UNUSED_KEYWORD_NAME)

    def test_rename_when_prefixed_keywords(self):
        kw = 'fjsdklhf37849'
        self._add_step('wHEn   '+kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          'wHEn   '+UNUSED_KEYWORD_NAME)

    def test_rename_then_prefixed_keywords(self):
        kw = 'djkfsekrhnbdxcvzo dsjah'
        self._add_step('THen '+kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          'THen '+UNUSED_KEYWORD_NAME)

    def test_rename_and_prefixed_keywords(self):
        kw = 'mmxznbfje uiriweyi yr iu fjkdhzxck'
        self._add_step('AND '+kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          'AND '+UNUSED_KEYWORD_NAME)

    def test_rename_but_prefixed_keywords(self):
        kw = 'sdlmclkds dslcm ldsm sdclmklm'
        self._add_step('bUt '+kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          'bUt '+UNUSED_KEYWORD_NAME)

    def test_rename_when_keyword_begins_with_prefix(self):
        kw = 'When I say so'
        self._add_step(kw)
        self._rename(kw, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Steps')
        self._expected_messages(steps_have_changed=True)
        self.assertEqual(self.test_ctrl.step(100).as_list()[100],
                          UNUSED_KEYWORD_NAME)

    def _add_step(self, keyword):
        self.test_ctrl.execute(ChangeCellValue(100, 100, keyword))
        self._steps_have_changed = False


if __name__ == '__main__':
    unittest.main()

