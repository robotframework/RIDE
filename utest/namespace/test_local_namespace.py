import unittest
from robot.utils.asserts import assert_equals, assert_false, assert_true
import datafilereader


class TestLocalNamespace(unittest.TestCase):

    def setUp(self):
        self._chief = datafilereader.construct_chief_controller(datafilereader.SIMPLE_PROJECT)
        self._test = datafilereader.get_ctrl_by_name('Test Case', self._chief.datafiles[0].tests)
        self._keyword = datafilereader.get_ctrl_by_name('Keyword', self._chief.datafiles[0].keywords)

    def test_macro_controller_has_local_namespace(self):
        assert_true(self._test.get_local_namespace() is not None)
        assert_true(self._keyword.get_local_namespace() is not None)

    def test_keyword_argument_is_visible_in_keywords_local_namespace(self):
        assert_true(self._keyword.get_local_namespace().has_name('${argument}'))

    def test_keyword_argument_is_not_visible_in_test_cases_local_namespace(self):
        assert_false(self._test.get_local_namespace().has_name('${argument}'))

    def test_keyword_steps_local_namespace_does_not_contain_local_variables_before_definition(self):
        for i in range(5):
            local_namespace = self._keyword.get_local_namespace_for_row(i)
            if i < 3:
                assert_false(local_namespace.has_name('${foo}'))
            if i < 5:
                assert_false(local_namespace.has_name('${bar}'))

    def test_keyword_steps_local_namespace_does_contain_local_variables_after_definition(self):
        for i in range(5):
            local_namespace = self._keyword.get_local_namespace_for_row(i)
            assert_true(local_namespace.has_name('${argument}'))
            if i >= 3:
                assert_true(local_namespace.has_name('${foo}'))
            if i >= 5:
                assert_true(local_namespace.has_name('${bar}'))


if __name__ == '__main__':
    unittest.main()
