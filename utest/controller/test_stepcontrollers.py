import unittest

from robotide.controller.stepcontrollers import StepController


class FakeStep(StepController):

    def __init__(self):
        pass


class UpdatingArgumentsTest(unittest.TestCase):

    def test_converting_last_empty_cell_without_args(self):
        self.assertEqual(
            FakeStep()._change_last_empty_to_empty_var([], None), [])

    def test_converting_last_empty_cell_with_single_value(self):
        self.assertEqual(
            FakeStep()._change_last_empty_to_empty_var([''], None),
            ['${EMPTY}'])

    def test_converting_last_empty_cell_with_multiple_values(self):
        self.assertEqual(
            FakeStep()._change_last_empty_to_empty_var(['Foo', '', ''], None),
            ['Foo', '', '${EMPTY}'])

    def test_converting_last_empty_cell_with_comment(self):
        self.assertEqual(
            FakeStep()._change_last_empty_to_empty_var([''], 'comment'), [''])


class StepContainsKeywordTest(unittest.TestCase, FakeStep):

    @property
    def keyword(self):
        return self._keyword

    @property
    def args(self):
        return self._args

    def setUp(self):
        self._keyword = 'Foo'
        self._args = ['Bar']

    def _verify_contains(self, keyword):
        self.assertTrue(self.contains_keyword(keyword))

    def _verify_does_not_contain(self, keyword):
        self.assertFalse(self.contains_keyword(keyword))

    def test_contains_keyword_in_keyword_position(self):
        self._verify_contains('Foo')

    def test_contains_keyword_in_argument_position(self):
        self._verify_contains('Bar')

    def test_does_not_contain_keyword(self):
        self._verify_does_not_contain('FooBar')

    def test_contains_keyword_with_given_prefix(self):
        self._args += ['Given Keyword']
        self._verify_contains('Keyword')

    def test_contains_keyword_with_when_prefix(self):
        self._keyword = 'When Something'
        self._verify_contains('SomeThing')

    def test_contains_keyword_with_then_prefix(self):
        self._args = ['Then anything']
        self._verify_contains('anythinG')

    def test_contains_keyword_with_and_prefix(self):
        self._keyword = 'and Nothing Else'
        self._verify_contains('nothingelse')

    def test_contains_keyword_with_but_prefix(self):
        self._keyword = 'but on the other end'
        self._verify_contains('ontheotherend')

    def test_does_not_remove_too_many_prefixes(self):
        self._keyword = 'Then And Nothing'
        self._verify_contains('And Nothing')
        self._verify_does_not_contain('Nothing')

    def test_matches_to_keyword_with_prefix_word(self):
        self._keyword = 'Then came John'
        self._verify_contains('Then came John')

if __name__ == "__main__":
    unittest.main()
