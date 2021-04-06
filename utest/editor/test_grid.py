#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import unittest
from nose.tools import assert_equal

from robotide.editor.gridbase import GridEditor

# wx needs to imported last so that robotide can select correct wx version.
import wx
from robotide.context import IS_WINDOWS

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

app = wx.App(None)

class _FakeMainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.plugin = None


def EditorWithData():
    grid = GridEditor(_FakeMainFrame(), 5, 5)
    for ridx, rdata in enumerate(DATA):
        for cidx, cdata in enumerate(rdata):
            grid.write_cell(ridx, cidx, cdata, update_history=False)
    return grid


class TestCoordinates(unittest.TestCase):

    def setUp(self):
        self._editor = EditorWithData()

    def test_cell_selection(self):
        self._editor.SelectBlock(2, 2, 2, 2)
        self._verify_selection(2, 2, 2, 2)

    def test_selecting_multiple_cells(self):
        self._editor.SelectBlock(0, 1, 3, 4)
        self._verify_selection(0, 1, 3, 4)

    def _verify_selection(self, toprow, topcol, botrow, botcol):
        assert_equal(self._editor.selection.topleft.row, toprow)
        assert_equal(self._editor.selection.topleft.col, topcol)
        assert_equal(self._editor.selection.bottomright.row, botrow)
        assert_equal(self._editor.selection.bottomright.col, botcol)


if not IS_WINDOWS:
    class TestClipBoard(unittest.TestCase):

        def setUp(self):
            self._editor = EditorWithData()

        def test_copy_one_cell(self):
            self._copy_block_and_verify((0, 0, 0, 0), [['kw1']])

        def test_copy_row(self):
            self._copy_block_and_verify((1, 0, 1, 1), [[val for val in DATA[1] if val]])

        def test_copy_block(self):
            self._copy_block_and_verify((0, 0, 2, 2), DATA)

        def _copy_block_and_verify(self, block, exp_content):
            self._editor.SelectBlock(*block)
            self._editor.copy()
            assert_equal(self._editor._clipboard_handler._clipboard.get_contents(),
                          exp_content)
            self._verify_grid_content(DATA)

        def test_cut_one_cell(self):
            self._cut_block_and_verify((0, 0, 0, 0), [['kw1']],
                                       [['', '', '']] + DATA[1:])

        def test_cut_row(self):
            self._cut_block_and_verify((2, 0, 2, 2), [DATA[2]], DATA[:2])

        def test_cut_block(self):
            self._cut_block_and_verify((0, 0, 2, 2), DATA, [])

        def _cut_block_and_verify(self, block, exp_clipboard, exp_grid):
            self._cut_block(block)
            assert_equal(self._editor._clipboard_handler._clipboard.get_contents(),
                          exp_clipboard)
            self._verify_grid_content(exp_grid)

        def test_undo_with_cut(self):
            self._cut_undo_and_verify((0,0,0,0), DATA)
            self._cut_undo_and_verify((0, 0, 2, 2), DATA)

        def _cut_undo_and_verify(self, block, exp_data_after_undo):
            self._cut_block(block)
            self._editor.undo()
            self._verify_grid_content(exp_data_after_undo)

        def test_multiple_levels_of_undo(self):
            self._cut_block((0, 0, 0, 0))
            self._cut_block((2, 0, 2, 2))
            self._editor.undo()
            self._verify_grid_content([['', '', '']] + DATA[1:])
            self._editor.undo()
            self._verify_grid_content(DATA)

        def _cut_block(self, block):
            self._editor.SelectBlock(*block)
            self._editor.cut()

        def test_paste_one_cell(self):
            self._copy_and_paste_block((1, 0, 1, 0), (3, 0, 3, 0), DATA + [['kw2']])
            # These tests are not independent
            self._copy_and_paste_block((1, 0, 1, 0), (0, 3, 0, 3),
                                       [DATA[0] + ['kw2']] + DATA[1:] + [['kw2']])

        def test_paste_row(self):
            self._copy_and_paste_block((2, 0, 2, 2), (3, 1, 3, 1), DATA + [[''] + DATA[2]])

        def test_paste_block(self):
            self._copy_and_paste_block((0, 0, 2, 2), (4, 0, 4, 0), DATA + [['']] + DATA)

        def test_paste_over(self):
            self._copy_and_paste_block((1, 0, 1, 1), (0, 0, 0, 0), [DATA[1]] + DATA[1:])

        def _copy_and_paste_block(self, sourceblock, targetblock, exp_content):
            self._editor.SelectBlock(*sourceblock)
            self._editor.copy()
            self._editor.SelectBlock(*targetblock)
            self._editor.paste()
            self._verify_grid_content(exp_content)

        def _verify_grid_content(self, data):
            for row in range(self._editor.NumberRows):
                for col in range(self._editor.NumberCols):
                    value = self._editor.GetCellValue(row, col)
                    try:
                        assert_equal(value, data[row][col],
                                      'The contents of cell (%d,%d) was not as '
                                      'expected' % (row, col))
                    except IndexError:
                        assert_equal(value, '')

        def test_simple_undo(self):
            self._editor.SelectBlock(*(0, 0, 0, 0))
            self._editor.cut()
            self._editor.undo()
            self._verify_grid_content(DATA)


if __name__ == '__main__':
    unittest.main()
