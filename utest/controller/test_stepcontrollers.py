import unittest

from robotide.controller.stepcontrollers import StepController


class FakeStep(StepController):

    def __init__(self):
        pass

class UpdatingArgumentsTest(unittest.TestCase):

    def test_converting_last_empty_cell_without_args(self):
        self.assertEqual(FakeStep()._change_last_empty_to_empty_var([], None), [])

    def test_converting_last_empty_cell_with_single_value(self):
        self.assertEqual(FakeStep()._change_last_empty_to_empty_var([''], None),
                         ['${EMPTY}'])

    def test_converting_last_empty_cell_with_multiple_values(self):
        self.assertEqual(FakeStep()._change_last_empty_to_empty_var(['Foo', '', ''], None),
                         ['Foo', '', '${EMPTY}'])

    def test_converting_last_empty_cell_with_comment(self):
        self.assertEqual(FakeStep()._change_last_empty_to_empty_var([''], 'comment'),
                         [''])

class UpdatingCommentsTest(unittest.TestCase):

    def test_stripping_comments(self):
        self.assertEqual(FakeStep()._remove_whitespace(' comment '),
                         'comment')

    def test_stripping_empty_comment(self):
        self.assertEqual(FakeStep()._remove_whitespace(None), None)


if __name__ == "__main__":
    unittest.main()
