import unittest
from robot.utils.asserts import assert_equals


class TableWriter(object):

    def __init__(self, output, cell_separator, line_separator):
        self._output = output
        self._cell_separator = cell_separator
        self._line_separator = line_separator
        self._headers = None
        self._data = []

    def add_headers(self, headers):
        self._headers = headers

    def add_row(self, row):
        self._data += [row]

    def write(self):
        separators = self._compute_cell_separators()
        for row, col_separators in zip([self._headers]+self._data, separators):
            while col_separators:
                self._output.write(row.pop(0))
                self._output.write(col_separators.pop(0))
            self._output.write(row.pop(0))
            self._output.write(self._line_separator)

    def _compute_cell_separators(self):
        if len(self._headers) < 2:
            return [[self._cell_separator for _ in range(len(row)-1)] for row in [self._headers]+self._data]
        lengths = self._max_column_item_lengths()
        separators = []
        for row in [self._headers]+self._data:
            col_separators = []
            for i, col in enumerate(row[:-1]):
                col_separators += [' '*(lengths[i]-len(col))+self._cell_separator]
            separators += [col_separators]
        return separators


    def _max_column_item_lengths(self):
        lengths = {}
        for row in [self._headers]+self._data:
            for i, item in enumerate(row):
                lengths[i] = max(lengths.get(i, 0), len(item))
        return lengths

    def _unify_first_two_columns_with(self, cell_separator):
        for row in self._data:
            if len(row) > 1:
                row[0] = row[0]+cell_separator+row[1]
                row.pop(1)


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

    def _data_should_equal(self, *expected):
        for exp, act in zip(expected, self._data.split('\n')):
            assert_equals(exp, act)

    def write(self, data):
        self._data += data


if __name__ == '__main__':
    unittest.main()
