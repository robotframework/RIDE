import unittest
from robot.parsing.model import TestCaseFile

from robot.utils.asserts import assert_equals
from robotide.controller import ChiefController
from robotide.controller.macrocontrollers import KEYWORD_NAME_FIELD, TESTCASE_NAME_FIELD
from robotide.controller.commands import Undo, FindOccurrences, RenameOccurrences
from robotide.controller.filecontrollers import (TestCaseFileController,
                                                 TestCaseTableController,
                                                 TestCaseController)
from robotide.publish import PUBLISHER
from robotide.publish.messages import RideItemStepsChanged, RideItemSettingsChanged,\
    RideItemNameChanged

STEP1_KEYWORD = 'Log'
STEP2_ARGUMENT = 'No Operation'
TEST1_NAME = 'Test'
UNUSED_KEYWORD_NAME = 'Foo'
USERKEYWORD1_NAME = 'User Keyword'
SETUP_KEYWORD = 'Setup Kw'
TEMPLATE_KEYWORD = 'Template Kw'
SUITE_SETUP_KEYWORD = 'Suite Setup Kw'
SUITE_NAME = 'Some Suite'
KEYWORD_IN_USERKEYWORD1 = 'Some Keyword'


def TestCaseControllerWithSteps():
    tcf = TestCaseFile()
    tcf.source = 'some_suite.txt'
    tcf.setting_table.suite_setup.name = 'Suite Setup Kw'
    tcf.setting_table.test_setup.name = 'Test Setup Kw'
    tcf.setting_table.test_teardown.name = 'Test Teardown Kw'
    tcf.setting_table.suite_teardown.name = 'Suite Teardown Kw'
    tcf.setting_table.test_template.value = 'Test Template Kw'
    testcase = tcf.testcase_table.add(TEST1_NAME)
    for step in [[STEP1_KEYWORD, 'Hello'], ['Run Keyword', STEP2_ARGUMENT]]:
        testcase.add_step(step)
    for_loop = testcase.add_for_loop([': FOR', '${i}', 'IN RANGE', '10'])
    for_loop.add_step(['Log', '${i}'])
    testcase.setup.name = SETUP_KEYWORD
    testcase.teardown.name = 'Teardown Kw'
    testcase.template.value = TEMPLATE_KEYWORD
    uk = tcf.keyword_table.add(USERKEYWORD1_NAME)
    uk.add_step([KEYWORD_IN_USERKEYWORD1])
    chief = ChiefController(None)
    tcf_ctrl = TestCaseFileController(tcf, chief)
    chief._controller = tcf_ctrl
    tctablectrl = TestCaseTableController(tcf_ctrl,
                                          tcf.testcase_table)
    return TestCaseController(tctablectrl, testcase)


def assert_occurrence(test_ctrl, kw_name, source, usage):
    assert_equals(_first_occurrence(test_ctrl, kw_name).usage, '%s (%s)' % (source, usage))

def _first_occurrence(test_ctrl, kw_name):
    occurrences = test_ctrl.execute(FindOccurrences(kw_name))
    if not occurrences:
        raise AssertionError('No occurrences found for "%s"' % kw_name)
    return occurrences[0]


class FindOccurrencesTest(unittest.TestCase):

    def setUp(self):
        self.test_ctrl = TestCaseControllerWithSteps()

    def test_no_occurrences(self):
        find_occurrences = FindOccurrences('Keyword Name')
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equals(occurrences, [])

    def test_occurrences_in_steps(self):
        assert_occurrence(self.test_ctrl, STEP1_KEYWORD, TEST1_NAME, 'Step 1')

    def test_occurrences_in_step_arguments(self):
        assert_occurrence(self.test_ctrl, STEP2_ARGUMENT, TEST1_NAME, 'Step 2')

    def test_occurrences_are_case_and_space_insensitive(self):
        assert_occurrence(self.test_ctrl, 'R un KE Y W O rd', TEST1_NAME, 'Step 2')
        assert_occurrence(self.test_ctrl, 'se tu p KW  ', TEST1_NAME, 'Setup')

    def test_occurrences_in_test_metadata(self):
        assert_occurrence(self.test_ctrl, SETUP_KEYWORD, TEST1_NAME, 'Setup')
        assert_occurrence(self.test_ctrl, 'Teardown Kw', TEST1_NAME, 'Teardown')
        assert_occurrence(self.test_ctrl, TEMPLATE_KEYWORD, TEST1_NAME, 'Template')

    def test_occurrences_in_suite_metadata(self):
        assert_occurrence(self.test_ctrl, SUITE_SETUP_KEYWORD, SUITE_NAME, 'Suite Setup')
        assert_occurrence(self.test_ctrl, 'Test Setup Kw', SUITE_NAME, 'Test Setup')
        assert_occurrence(self.test_ctrl, 'Test Teardown Kw', SUITE_NAME, 'Test Teardown')
        assert_occurrence(self.test_ctrl, 'Suite Teardown Kw', SUITE_NAME, 'Suite Teardown')
        assert_occurrence(self.test_ctrl, 'Test Template Kw', SUITE_NAME, 'Test Template')

    def test_occurrences_in_user_keywords(self):
        assert_occurrence(self.test_ctrl, KEYWORD_IN_USERKEYWORD1, USERKEYWORD1_NAME, 'Step 1')

    def test_occurrence_in_user_keyword_name(self):
        assert_occurrence(self.test_ctrl, USERKEYWORD1_NAME, USERKEYWORD1_NAME, KEYWORD_NAME_FIELD)


class RenameOccurrenceTest(unittest.TestCase):

    def setUp(self):
        self.test_ctrl = TestCaseControllerWithSteps()
        self._steps_have_changed = False
        self._testcase_settings_have_changed = False
        self._keyword_name_has_changed = False
        PUBLISHER.subscribe(self._steps_changed, RideItemStepsChanged)
        PUBLISHER.subscribe(self._testcase_settings_changed, RideItemSettingsChanged)
        PUBLISHER.subscribe(self._keyword_name_changed, RideItemNameChanged)

    def tearDown(self):
        PUBLISHER.unsubscribe(self._steps_changed, RideItemStepsChanged)
        PUBLISHER.unsubscribe(self._testcase_settings_changed, RideItemSettingsChanged)
        PUBLISHER.unsubscribe(self._keyword_name_changed, RideItemNameChanged)

    def _steps_changed(self, test):
        self._steps_have_changed = True

    def _testcase_settings_changed(self, test):
        self._testcase_settings_have_changed = True

    def _keyword_name_changed(self, data):
        self._keyword_name_has_changed = True

    def _expected_messages(self, steps_have_changed=False, testcase_settings_have_changed=False,
                           keyword_name_has_changed=False):
        assert_equals(self._steps_have_changed, steps_have_changed)
        assert_equals(self._testcase_settings_have_changed, testcase_settings_have_changed)
        assert_equals(self._keyword_name_has_changed, keyword_name_has_changed)

    def _rename(self, original_name, new_name, source, usage):
        self.test_ctrl.execute(RenameOccurrences(original_name, new_name))
        assert_occurrence(self.test_ctrl, new_name, source, usage)

    def test_rename_in_steps(self):
        self._rename(STEP1_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Step 1')
        self._expected_messages(steps_have_changed=True)

    def test_undo_rename_in_step(self):
        self._rename(STEP1_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Step 1')
        self.test_ctrl.execute(Undo())
        assert_equals(self.test_ctrl.steps[0].keyword, STEP1_KEYWORD)

    def test_undo_after_renaming_to_something_that_is_already_there(self):
        self._rename(STEP1_KEYWORD, STEP2_ARGUMENT, TEST1_NAME, 'Step 1')
        self.test_ctrl.execute(Undo())
        assert_equals(self.test_ctrl.steps[1].args[0], STEP2_ARGUMENT)


    def test_rename_steps_argument(self):
        self._rename(STEP2_ARGUMENT, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Step 2')
        self._expected_messages(steps_have_changed=True)
        assert_equals(self.test_ctrl.steps[1].as_list(), ['Run Keyword', UNUSED_KEYWORD_NAME])

    def test_user_keyword_rename(self):
        self._rename(USERKEYWORD1_NAME, UNUSED_KEYWORD_NAME, UNUSED_KEYWORD_NAME, KEYWORD_NAME_FIELD)
        self._expected_messages(keyword_name_has_changed=True)

    def test_rename_in_test_setup(self):
        self._rename(SETUP_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Setup')
        self._expected_messages(testcase_settings_have_changed=True)

    def test_rename_in_test_template(self):
        self._rename(TEMPLATE_KEYWORD, UNUSED_KEYWORD_NAME, TEST1_NAME, 'Template')
        self._expected_messages(testcase_settings_have_changed=True)

    def test_rename_in_suite_metadata(self):
        self._rename(SUITE_SETUP_KEYWORD, UNUSED_KEYWORD_NAME, SUITE_NAME, 'Suite Setup')
        self._expected_messages()

    def test_rename_in_user_keywords(self):
        self._rename(KEYWORD_IN_USERKEYWORD1, UNUSED_KEYWORD_NAME, USERKEYWORD1_NAME, 'Step 1')
        self._expected_messages(steps_have_changed=True)
