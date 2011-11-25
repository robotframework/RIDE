import unittest
from robot.utils.asserts import assert_equals
from robotide.writer.tablewriter import TableWriter


class TableWriterTest(unittest.TestCase):

    def setUp(self):
        self._writer = TableWriter(output=self,
                             cell_separator='    ',
                             line_separator='\n')
        self._data = ''

    def test_writing(self):
        self._writer.add_headers(['*** Test Cases ***'])
        self._writer.add_row(['My Test Case'])
        self._writer.add_row(['', 'Log', 'hello'])
        self._writer.write()
        self._data_should_equal(
            '*** Test Cases ***',
            'My Test Case',
            '    Log    hello')

    def test_writing_with_1_additional_header(self):
        self._writer.add_headers(['*** Test Cases ***', 'header'])
        self._writer.add_row(['My Test'])
        self._writer.add_row(['', 'Something', 'nothing'])
        self._writer.write()
        self._data_should_equal(
            '*** Test Cases ***    header',
            'My Test',
            '                      Something    nothing')

    def test_writing_with_2_additional_headers(self):
        self._writer.add_headers(['*** Test Cases ***', 'h1', 'h2'])
        self._writer.add_row(['My Test'])
        self._writer.add_row(['', 'Something', 'nothing more to say'])
        self._writer.add_row(['', 'Something else', 'jeps', 'heps'])
        self._writer.write()
        self._data_should_equal(
            '*** Test Cases ***    h1                h2',
            'My Test',
            '                      Something         nothing more to say',
            '                      Something else    jeps                   heps'
        )

    def test_ignore_first_column_length_when_only_one_element_in_row(self):
        self._writer.add_headers(['*** Test Cases ***', 'h1', 'h2'])
        self._writer.add_row(['Test Case with very long title that should be ignored'])
        self._writer.add_row(['', 'something', 'something else'])
        self._writer.write()
        self._data_should_equal(
            '*** Test Cases ***    h1           h2',
            'Test Case with very long title that should be ignored',
            '                      something    something else'
        )

    def _data_should_equal(self, *expected):
        for exp, act in zip(expected, self._data.split('\n')):
            assert_equals(exp, act)

    def write(self, data):
        self._data += data


if __name__ == '__main__':
    unittest.main()
