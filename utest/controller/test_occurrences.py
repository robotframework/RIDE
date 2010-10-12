import unittest
from robot.parsing.model import TestCaseFile

from robot.utils.asserts import assert_equals
from robotide.controller.chiefcontroller import ChiefController
from robotide.controller.filecontroller import (TestCaseFileController,
                                                TestCaseTableController,
                                                TestCaseController)


def TestCaseControllerWithSteps(steps):
    tcf = TestCaseFile()
    testcase = tcf.testcase_table.add('Test')
    for step in steps:
        testcase.add_step(step)
    testcase.setup.name = 'Setup'
    chief = ChiefController(None)
    tcf_ctrl = TestCaseFileController(tcf, chief)
    chief._controller = tcf_ctrl
    tctablectrl = TestCaseTableController(tcf_ctrl,
                                          tcf.testcase_table)
    return TestCaseController(tctablectrl, testcase)


class FindOccurrencesTest(unittest.TestCase):

    def setUp(self):
        self.test_ctrl = TestCaseControllerWithSteps([['Log', 'Hello']])

    def test_no_occurrences(self):
        find_occurrences = FindOccurrences('Keyword Name')
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equals(occurrences, [])

    def test_occurrences_in_steps(self):
        self._assert_occurrence('Log', 'Test (Step 1)')

    def test_occurrences_in_test_metadata(self):
        self._assert_occurrence('Setup', 'Test (Setup)')

    def _assert_occurrence(self, kw_name, usage):
        find_occurrences = FindOccurrences(kw_name)
        occurrences = self.test_ctrl.execute(find_occurrences)
        assert_equals(occurrences[0].usage, usage)


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
        for data_file in context.datafile_controller._chief_controller.datafiles:
            for test in data_file.tests:
                result.extend(self._find_occurances_in_test(test))
        return result

    def _find_occurances_in_test(self, test):
        for item in test.steps + test.settings:
            if item.contains_keyword(self._keyword_name):
                yield Occurrence(item)
