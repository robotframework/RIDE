import unittest
import random

from robot.libraries.String import String


from robotide.controller.cellinfo import CellInfo, ContentType, CellType,\
    CellContent, CellPosition
from robotide.editor.gridcolorizer import Colorizer, ColorizationSettings,\
    parse_info_grid

from resources import PYAPP_REFERENCE as _ #Needed to be able to create wx components

# wx needs to imported last so that robotide can select correct wx version.
import wx
from robot.utils.asserts import assert_not_none, assert_none


class MockGrid(object):
    SetCellTextColour = SetCellBackgroundColour = SetCellFont = lambda s, x, y, z: True

    def __init__(self, rows, cols):
        self.NumberRows = rows
        self.NumberCols = cols

    def GetCellFont(self, x, y):
        return Font()


class Font(object):
    SetWeight = lambda s, x: True


class ControllerWithCellInfo(object):
    content_types = [getattr(ContentType, i) for i in dir(ContentType) if not i.startswith('__') ]
    cell_types = [getattr(CellType, i) for i in dir(CellType) if not i.startswith('__') ]

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


class ControllerWithNoCellInfo(ControllerWithCellInfo):

    def get_cell_info(self, row, column):
        return None


class TestGridColorization(unittest.TestCase):
    _data = ['Keyword', 'Some longer data in cell', '${variable}', 
             '#asdjaskdkjasdkjaskdjkasjd', 'asdasd,asdasd,as asd jasdj asjd asjdj asd']

    def test_parsing_gets_values(self):
        grid = MockGrid(10,4)
        info_grid = parse_info_grid(grid, ControllerWithCellInfo())
        for row in range(0,10):
            for col in range(0,4):
                assert_not_none(info_grid[row][col])

    def test_parsing_empty_grid(self):
        grid = MockGrid(10,4)
        info_grid = parse_info_grid(grid, ControllerWithNoCellInfo())
        for row in range(0,10):
            for col in range(0,4):
                assert_none(info_grid[row][col])

    def test_parsing_and_colorizing_grid(self):
        grid = MockGrid(10,4)
        info_grid = parse_info_grid(grid, ControllerWithCellInfo())
        colorizer = Colorizer(grid, ColorizationSettings())
        colorizer.colorize(info_grid, None)

    def test_colorizing_performance(self):
        grid = MockGrid(100,5)
        info_grid = parse_info_grid(grid, ControllerWithCellInfo())
        colorizer = Colorizer(grid, ColorizationSettings())
        for _ in range(0, 500):
            colorizer._colorize_cell(info_grid[0][0],self._data[random.randint(0, 4)], 1, 1)


if __name__ == '__main__':
    unittest.main()
