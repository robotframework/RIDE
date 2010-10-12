import unittest
from robot.parsing.model import TestCaseFile

from robot.utils.asserts import assert_equals
from robotide.controller.chiefcontroller import ChiefController
from robotide.controller.filecontroller import (TestCaseFileController,
                                                TestCaseTableController,
                                                TestCaseController)


def TestCaseControllerWithSteps():
    tcf = TestCaseFile()
    tcf.source = 'some_suite.txt'
    tcf.setting_table.suite_setup.name = 'Suite Setup Kw'
    tcf.setting_table.test_setup.name = 'Test Setup Kw'
    tcf.setting_table.test_teardown.name = 'Test Teardown Kw'
    tcf.setting_table.suite_teardown.name = 'Suite Teardown Kw'
    tcf.setting_table.test_template.value = 'Test Template Kw'
    testcase = tcf.testcase_table.add('Test')
    for step in [['Log', 'Hello'], ['No Operation']]:
        testcase.add_step(step)
    testcase.setup.name = 'Setup Kw'
    testcase.teardown.name = 'Teardown Kw'
    testcase.template.value = 'Template Kw'
    uk = tcf.keyword_table.add('User Keyword')
    uk.add_step(['Some Keyword'])
    chief = ChiefController(None)
    tcf_ctrl = TestCaseFileController(tcf, chief)
    chief._controller = tcf_ctrl
    tctablectrl = TestCaseTableController(tcf_ctrl,
                                          tcf.testcase_table)
    return TestCaseController(tctablectrl, testcase)


class FindOccurrencesTest(unittest.TestCase):

    def setUp(self):
        self.test_ctrl = TestCaseControllerWithSteps()

    def test_no_occurrences(self):
        find_occurrences = FindOccurrences('Keyword Name')
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equals(occurrences, [])

    def test_occurrences_in_steps(self):
        self._assert_occurrence('Log', 'Test', 'Step 1')

    def test_occurrences_are_case_and_space_insensitive(self):
        self._assert_occurrence('no   OpEratioN  ', 'Test', 'Step 2')
        self._assert_occurrence('se tu p KW  ', 'Test', 'Setup')

    def test_occurrences_in_test_metadata(self):
        self._assert_occurrence('Setup Kw', 'Test', 'Setup')
        self._assert_occurrence('Teardown Kw', 'Test', 'Teardown')
        self._assert_occurrence('Template Kw', 'Test', 'Template')

    def test_occurrences_in_suite_metadata(self):
        self._assert_occurrence('Suite Setup Kw', 'Some Suite', 'Suite Setup')
        self._assert_occurrence('Test Setup Kw', 'Some Suite', 'Test Setup')
        self._assert_occurrence('Test Teardown Kw', 'Some Suite', 'Test Teardown')
        self._assert_occurrence('Suite Teardown Kw', 'Some Suite', 'Suite Teardown')
        self._assert_occurrence('Test Template Kw', 'Some Suite', 'Test Template')

    def test_occurrences_in_user_keywords(self):
        self._assert_occurrence('Some Keyword', 'User Keyword', 'Step 1')

    def _assert_occurrence(self, kw_name, source, usage):
        find_occurrences = FindOccurrences(kw_name)
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equals(occurrences[0].usage, '%s (%s)' % (source, usage))


class Occurrence(object):

    def __init__(self, item):
        self._item = item

    @property
    def usage(self):
        return self._item.logical_name


class FindOccurrences(object):

    def __init__(self, keyword_name):
        self._keyword_name = keyword_name

    def execute(self, context):
        result = []
        for df in context.datafiles:
            result.extend(self._find_occurrences_in(df.settings))
            for test in df.tests:
                result.extend(self._find_occurrences_in(test.steps + test.settings))
            for kw in df.keywords:
                result.extend(self._find_occurrences_in(kw.steps))
        return result

    def _find_occurrences_in(self, items):
        return (Occurrence(item) for item in items
                if item.contains_keyword(self._keyword_name))
