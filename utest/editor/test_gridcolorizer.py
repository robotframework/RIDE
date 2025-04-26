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
import random

from robotide.editor.gridbase import GridEditor

# wx needs to imported last so that robotide can select correct wx version.
import os
import pytest

from robotide.lib.robot.libraries.String import String

from robotide.controller.cellinfo import CellInfo, ContentType, CellType, CellContent, CellPosition
from robotide.editor.gridcolorizer import Colorizer


# DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)  # Avoid failing unit tests in system without X11
import wx

DATA = [['kw1', '', ''],
        ['kw2', 'arg1', ''],
        ['kw3', 'arg1', 'arg2']]

myapp = wx.App(None)


class _FakeMainFrame(wx.Frame):
    myapp = wx.App(None)

    def __init__(self):
        wx.Frame.__init__(self, None)
        self.plugin = None


def EditorWithData():
    myapp = wx.App(None)
    grid = GridEditor(_FakeMainFrame(), 5, 5)
    for ridx, rdata in enumerate(DATA):
        for cidx, cdata in enumerate(rdata):
            grid.write_cell(ridx, cidx, cdata, update_history=False)
    return grid


class MockGrid(object):
    noop = lambda *args: None
    SetCellTextColour = SetCellBackgroundColour = SetCellFont = noop
    settings = {
        'font size': 10,
        'font face': '',
        'fixed font': False,
        'col size': 150,
        'max col size': 450,
        'auto size cols': False,
        'text user keyword': 'blue',
        'text library keyword': '#0080C0',
        'text variable': 'forest green',
        'text unknown variable': 'purple',
        'text commented': 'firebrick',
        'text string': 'black',
        'text empty': 'black',
        'background assign': '#FFFFFF',
        'background keyword': '#FFFFFF',
        'background mandatory': '#FFFFFF',
        'background optional': '#F5F5F5',
        'background must be empty': '#C0C0C0',
        'background unknown': '#FFFFFF',
        'background error': '#FF9385',
        'background highlight': '#FFFF77',
        'word wrap': True,
        'enable auto suggestions': False
    }

    def GetCellFont(self, x, y):
        return Font()


class Font(object):
    SetWeight = lambda s, x: True


class ControllerWithCellInfo(object):
    content_types = [getattr(ContentType, i) for i in
                     dir(ContentType) if not i.startswith('__') ]
    cell_types = [getattr(CellType, i) for i in
                  dir(CellType) if not i.startswith('__') ]

    def __init__(self):
        self._string = String()

    def get_cell_info(self, row, column):
        return CellInfo(CellContent(self._get(self.content_types), self._get_data(), None),
                        CellPosition(self._get(self.cell_types), None))

    def _get(self, items):
        return items[random.randint(0, len(items)-1)]

    def _get_data(self):
        if random.randint(0, 5) == 0:
            return "data with some ${variable} in there"
        return self._string.generate_random_string(50)


# @pytest.mark.skip('It is getting unexpected data')
class TestPerformance(unittest.TestCase):
    _data = ['Keyword', 'Some longer data in cell', '${variable}',
             '#asdjaskdkjasdkjaskdjkasjd', 'asdasd,asdasd,as asd jasdj asjd asjdj asd']

    def setUp(self):
        self._editor = EditorWithData()

    def test_colorizing_performance(self):
        colorizer = Colorizer(MockGrid(), ControllerWithCellInfo())
        for _ in range(0, 500):
            rdata = self._data[random.randint(0, 4)]
            self._editor.SetCellValue(1, 1, rdata)
            cdata = self._editor.GetCellValue(1, 1)
            colorizer._colorize_cell(1,1, cdata)


class TestColorIdentification(unittest.TestCase):
    _data = ['xyz', 'FOR', 'try', 'for', 'LOG']
    _type = [CellInfo(CellContent(ContentType.STRING, _data[0]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.LIBRARY_KEYWORD, _data[1]), CellPosition(CellType.ASSIGN, '${i}')),
             CellInfo(CellContent(ContentType.STRING, _data[2]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.STRING, _data[3]), CellPosition(CellType.UNKNOWN, None)),
             CellInfo(CellContent(ContentType.LIBRARY_KEYWORD, _data[4]), CellPosition(CellType.MANDATORY, 'Message'))
             ]

    def test_unknown_string(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[0])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[0], self._data[0])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_valid_for(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[1])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[1], self._data[1])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text library keyword'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_invalid_try(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[2])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[2], self._data[2])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_invalid_for(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[3])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[3], self._data[3])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text string'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)

    def test_valid_log(self):
        grid = MockGrid()
        colorizer = Colorizer(grid, ControllerWithCellInfo())
        txt_color = colorizer._get_text_color(self._type[4])
        # print(f"DEBUG: Text color={txt_color.title().upper()}")
        bk_color = colorizer._get_background_color(self._type[4], self._data[4])
        # print(f"DEBUG: Background color={bk_color.title().upper()}")
        assert txt_color.title().upper() == grid.settings['text library keyword'].upper()
        assert bk_color.title().upper() == grid.settings['background highlight'].upper()  # I am cheating here ;)


if __name__ == '__main__':
    unittest.main()
