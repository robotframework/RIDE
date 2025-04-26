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

from robotide.editor.gridbase import GridEditor

# wx needs to be imported last so that robotide can select correct wx version.
import os
import pytest
# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)  # Avoid failing unit tests in system without X11
import wx
from robotide.context import IS_WINDOWS

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

app = wx.App(None)


class _FakeScrolledPanel(wx.lib.scrolledpanel.ScrolledPanel):

    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, None)

    def SetupScrolling(self):
        pass


class _FakeMainFrame(wx.Frame, _FakeScrolledPanel):
    myapp = wx.App(None)

    def __init__(self):
        wx.Frame.__init__(self, None)
        _FakeScrolledPanel.__init__(self, None)
        self.plugin = None


def EditorWithData():
    myapp = wx.App(None)
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
        assert self._editor.selection.topleft.row == toprow
        assert self._editor.selection.topleft.col == topcol
        assert self._editor.selection.bottomright.row == botrow
        assert self._editor.selection.bottomright.col == botcol


if __name__ == '__main__':
    unittest.main()
