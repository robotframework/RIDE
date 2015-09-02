import unittest

from nose.tools import assert_true, assert_false

from robotide.utils.highlightmatcher import highlight_matcher


class TestHighlightMatcher(unittest.TestCase):

    def test_empty_cell_should_not_match(self):
        assert_false(self.matcher('', ''))

    def test_exact_match(self):
        assert_true(self.matcher('My Keyword', 'My Keyword'))
        assert_false(self.matcher('My Keyword', 'Keyword'))

    def test_normalized_match(self):
        assert_true(self.matcher('MyKeyword', 'My Keyword'))
        assert_true(self.matcher('mykeyword', 'My Keyword'))
        assert_true(self.matcher('my_key_word', 'My Keyword'))

    def test_variable_with_equals_sign(self):
        assert_true(self.matcher('${foo} =', '${foo}'))
        assert_true(self.matcher('${foo}=', '${foo}'))
        assert_true(self.matcher('${foo}=', '${  F O O }'))
        assert_false(self.matcher('${foo}=', '${foo2}'))

    def test_variable_inside_cell_content(self):
        assert_true(self.matcher('${foo} =', 'some  ${foo} data'))
        assert_false(self.matcher('some  ${foo} data', '${foo} ='))
        assert_false(self.matcher('${foo}=', 'some not matching ${var}'))
        assert_true(self.matcher('${foo} =', 'Jep we have ${var} and ${foo}!'))

    def test_list_variable(self):
        assert_true(self.matcher('@{foo} =', '@{foo}'))

    def test_list_variable_when_index_is_used(self):
        assert_true(self.matcher('@{foo}[2]', '@{foo}'))
        assert_true(self.matcher('@{foo}[2]', '@{foo}[1]'))
        assert_true(self.matcher('@{foo}[2]', 'some @{foo} data'))
        assert_false(self.matcher('@{foo}[2]', 'some @{foo2} data'))
        assert_false(self.matcher('@{foo}123', '@{foo}'))

    def test_extended_variable(self):
        assert_true(self.matcher('${foo.extended}', '${foo}'))
        assert_true(self.matcher('${foo + 5}', '${foo}'))
        assert_true(self.matcher('${foo}', 'some ${foo.extended} data'))
        assert_true(self.matcher('${foo} =', 'some ${foo.extended} data'))
        assert_false(self.matcher('${foo + 5}', '${foo2}'))

    def test_list_variable_used_as_scalar(self):
        assert_true(self.matcher('@{foo}', '${foo}'))

    def matcher(self, value, content):
        return highlight_matcher(value, content)

if __name__ == "__main__":
    unittest.main()
